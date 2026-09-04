"""Seeded errors and catch rate (F-35, and the gate in OPEN_FINDINGS.md #2).

Approval fatigue and high accuracy produce the same number: people clicking
approve without editing. So an approval rate cannot tell you which one you have,
and the promotion gate that reads it will happily promote a workflow nobody is
actually reviewing.

The only way to tell them apart is to put a known-wrong item in front of the
reviewer and see whether they catch it.

Ships disabled. Turning it on is a firm's decision, not a default, and the
firm's staff are told the mechanism exists -- not when an item is seeded, but
that seeding happens. Every seeded item is revealed to the reviewer as soon as
they decide on it, so nobody is left believing they made a real mistake, and
nobody's real work is silently altered.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from .receipts import (
    BAD_EXTRACTION, PENDING_APPROVAL, Receipt, WRONG_DOCUMENT, WRONG_NAMING,
    WRONG_TARGET, now_iso,
)

INJECTED = "injected"
RESOLVED = "resolved"


@dataclass(frozen=True)
class Fault:
    """A deliberate defect, and the rejection reason a reviewer should give."""

    kind: str
    expected_reason: str
    description: str


FAULTS = {
    "wrong_account": Fault(
        "wrong_account", WRONG_TARGET,
        "one digit of the account number was changed",
    ),
    "wrong_household": Fault(
        "wrong_household", WRONG_TARGET,
        "the item was pointed at a different household",
    ),
    "wrong_period": Fault(
        "wrong_period", WRONG_DOCUMENT,
        "the statement period was shifted by a month",
    ),
    "bad_naming": Fault(
        "bad_naming", WRONG_NAMING,
        "the filename does not follow the firm's convention",
    ),
    "transposed_value": Fault(
        "transposed_value", BAD_EXTRACTION,
        "two digits of an extracted balance were transposed",
    ),
}


@dataclass(frozen=True)
class CatchRate:
    caught: int
    missed: int
    pending: int

    @property
    def decided(self) -> int:
        return self.caught + self.missed

    @property
    def rate(self) -> float | None:
        """None when nothing has been decided yet -- not zero, and not one."""
        return self.caught / self.decided if self.decided else None

    def __str__(self) -> str:
        if self.rate is None:
            return "no seeded items have been decided yet"
        return f"{self.caught}/{self.decided} caught ({self.rate:.0%}), {self.pending} pending"


class SeedRegistry:
    """Append-only record of which items were seeded and who caught them.

    Kept out of the receipt schema on purpose: the marker must not be visible in
    the receipt the reviewer is reading, or the drill measures nothing.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            receipt_id = entry["receipt_id"]
            if entry["event"] == INJECTED:
                self._records[receipt_id] = dict(entry, resolution=None)
            elif receipt_id in self._records:
                self._records[receipt_id]["resolution"] = entry

    def _write(self, entry: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def record(self, receipt_id: str, workflow_id: str, fault: Fault) -> None:
        entry = {
            "event": INJECTED, "receipt_id": receipt_id, "workflow_id": workflow_id,
            "fault": fault.kind, "expected_reason": fault.expected_reason,
            "description": fault.description, "at": now_iso(),
        }
        self._write(entry)
        self._records[receipt_id] = dict(entry, resolution=None)

    def is_seeded(self, receipt_id: str) -> bool:
        return receipt_id in self._records

    def get(self, receipt_id: str) -> dict | None:
        return self._records.get(receipt_id)

    def resolve(
        self, receipt_id: str, *, caught: bool, decided_by: str,
        reason_given: str | None = None,
    ) -> dict:
        record = self._records.get(receipt_id)
        if record is None:
            raise LookupError(f"{receipt_id} was not a seeded item")
        entry = {
            "event": RESOLVED, "receipt_id": receipt_id, "caught": caught,
            "reason_given": reason_given, "decided_by": decided_by,
            "right_reason": reason_given == record["expected_reason"],
            "at": now_iso(),
        }
        self._write(entry)
        record["resolution"] = entry
        return record

    def catch_rate(self, workflow_id: str | None = None) -> CatchRate:
        caught = missed = pending = 0
        for record in self._records.values():
            if workflow_id and record["workflow_id"] != workflow_id:
                continue
            resolution = record.get("resolution")
            if resolution is None:
                pending += 1
            elif resolution["caught"]:
                caught += 1
            else:
                missed += 1
        return CatchRate(caught=caught, missed=missed, pending=pending)

    def unresolved(self) -> list[dict]:
        return [r for r in self._records.values() if r.get("resolution") is None]


class SeededErrorInjector:
    """Corrupts a copy of a proposal so a reviewer has something to catch.

    Disabled unless a firm switches it on. When disabled every call is a no-op,
    so the injector can sit in the pipeline permanently without doing anything.
    """

    def __init__(
        self,
        registry: SeedRegistry,
        *,
        enabled: bool = False,
        rate: float = 0.0,
        rng: random.Random | None = None,
    ):
        if not 0.0 <= rate <= 1.0:
            raise ValueError("rate must be between 0.0 and 1.0")
        self.registry = registry
        self.enabled = enabled
        self.rate = rate
        self._rng = rng or random.Random()

    def should_seed(self) -> bool:
        return self.enabled and self.rate > 0 and self._rng.random() < self.rate

    def maybe_seed(self, receipt: Receipt) -> tuple[Receipt, Fault | None]:
        """Return the receipt, seeded or untouched.

        Only proposals awaiting approval are ever seeded. A seeded item that
        nobody has to approve teaches nothing, and corrupting anything else
        would put a defect into real work with no gate in front of it.
        """
        if receipt.outcome != PENDING_APPROVAL or not self.should_seed():
            return receipt, None
        fault = self._rng.choice(list(FAULTS.values()))
        seeded = self._apply(receipt, fault)
        if seeded is None:
            return receipt, None
        self.registry.record(seeded.receipt_id, seeded.workflow_id, fault)
        return seeded, fault

    def _apply(self, receipt: Receipt, fault: Fault) -> Receipt | None:
        """Corrupt a copy. Returns None if this receipt has nothing to corrupt."""
        data = receipt.to_dict()
        after = dict(data.get("after_state") or {})

        if fault.kind == "wrong_account":
            digits = [c for c in receipt.target_identifier if c.isdigit()]
            if not digits:
                return None
            original = digits[-1]
            replacement = str((int(original) + 1) % 10)
            data["target_identifier"] = _replace_last(
                receipt.target_identifier, original, replacement
            )
        elif fault.kind == "wrong_household":
            data["target_identifier"] = f"{receipt.target_identifier} (Trust)"
        elif fault.kind == "wrong_period":
            changed = False
            for key, value in list(after.items()):
                shifted = _shift_month(str(value))
                if shifted is not None:
                    after[key] = shifted
                    changed = True
            if not changed:
                return None
            data["after_state"] = after
        elif fault.kind == "bad_naming":
            for key, value in list(after.items()):
                if "name" in key or str(value).endswith(".pdf"):
                    after[key] = str(value).replace(" ", "_").lower()
                    data["after_state"] = after
                    break
            else:
                return None
        elif fault.kind == "transposed_value":
            target = _numeric_field(after)
            if target is None:
                return None
            transposed = _transpose_digits(str(after[target]))
            if transposed is None:
                return None
            after[target] = transposed
            data["after_state"] = after
        else:
            return None

        data.pop("receipt_id")
        return Receipt.from_dict(data)


def _replace_last(text: str, old: str, new: str) -> str:
    index = text.rfind(old)
    return text if index < 0 else text[:index] + new + text[index + 1:]


def _shift_month(value: str) -> str | None:
    """Shift a leading YYYY-MM by one month, or return None."""
    if len(value) < 7 or value[4] != "-" or not value[:4].isdigit():
        return None
    if not value[5:7].isdigit():
        return None
    year, month = int(value[:4]), int(value[5:7])
    if not 1 <= month <= 12:
        return None
    month -= 1
    if month == 0:
        month, year = 12, year - 1
    return f"{year:04d}-{month:02d}" + value[7:]


#: A transposed-digit fault has to land on an amount, not on a filename that
#: happens to contain a date. Wrong field, wrong lesson.
_AMOUNT = re.compile(r"^[-+$(]?\s*[\d,]+(?:\.\d+)?\s*\)?$")
_AMOUNT_KEYS = ("balance", "amount", "value", "total", "market", "cash", "price")


def _numeric_field(state: dict) -> str | None:
    """Pick the field most plausibly holding a money amount."""
    candidates = [
        key for key, value in state.items()
        if _AMOUNT.match(str(value).strip()) and any(ch.isdigit() for ch in str(value))
    ]
    if not candidates:
        return None
    for key in candidates:
        if any(hint in key.lower() for hint in _AMOUNT_KEYS):
            return key
    return candidates[0]


def _transpose_digits(value: str) -> str | None:
    """Swap the first adjacent pair of differing digits, or return None."""
    chars = list(value)
    for index in range(len(chars) - 1):
        if chars[index].isdigit() and chars[index + 1].isdigit():
            if chars[index] != chars[index + 1]:
                chars[index], chars[index + 1] = chars[index + 1], chars[index]
                return "".join(chars)
    return None
