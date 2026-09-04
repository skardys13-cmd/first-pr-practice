"""Artifact verification (Step 21, F-16, F-17).

Success is the artifact passing its checks, never the navigation completing.
That inversion is what makes portal drift fail loudly: a redesign that leads the
agent somewhere plausible still produces a file that fails these checks, and a
failed check is a stop, not a Done.

Nothing is accepted on one identifier. The account, the holder, and the period
must all agree, because an account number that is one digit out belongs to
somebody who is also a client of this firm.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from .matching import contains_account
from .normalizer import MONTHS

MONTH_NAMES = {
    number: name for name, number in MONTHS.items() if len(name) > 3
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class Verification:
    checks: list[Check] = field(default_factory=list)
    file_hash: str = ""
    size: int = 0
    text: str = ""

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if not check.passed]

    def summary(self) -> str:
        if self.passed:
            return f"All {len(self.checks)} checks passed."
        first = self.failures[0]
        return f"{first.name}: {first.detail}"


def period_present(text: str, period: str) -> bool:
    """Is this statement period stated in the document?

    Accepts `2026-08`, `August 2026`, `Aug 2026`, and `08/2026`. A year-only
    period (`2025`) accepts the bare year.
    """
    if not period:
        return False
    text_lower = (text or "").lower()

    quarter = re.fullmatch(r"(\d{4})-Q([1-4])", period)
    if quarter:
        year, number = quarter.group(1), quarter.group(2)
        return bool(re.search(rf"\bq{number}\b.{{0,12}}{year}|{year}.{{0,12}}\bq{number}\b",
                              text_lower))

    month = re.fullmatch(r"(\d{4})-(\d{2})", period)
    if not month:
        return bool(re.search(rf"\b{re.escape(period)}\b", text_lower))

    year, number = month.group(1), int(month.group(2))
    name = MONTH_NAMES.get(number, "")
    candidates = [
        rf"\b{year}-{number:02d}\b",
        rf"\b{number:02d}/{year}\b",
    ]
    if name:
        candidates.append(rf"\b{name}\w*\s+{year}\b")
        candidates.append(rf"\b{name[:3]}\w*\s+{year}\b")
    return any(re.search(pattern, text_lower) for pattern in candidates)


def verify_statement(
    path: str | Path,
    *,
    account: str,
    period: str,
    holder: str | None = None,
    extract=None,
) -> Verification:
    """Check a retrieved statement is the one that was asked for."""
    from .pdf import extract_text

    extract = extract or extract_text
    path = Path(path)
    result = Verification()

    if not path.exists():
        result.checks.append(Check("file exists", False, "nothing was downloaded"))
        return result

    data = path.read_bytes()
    result.size = len(data)
    result.file_hash = hashlib.sha256(data).hexdigest()

    result.checks.append(Check(
        "is a PDF", data[:5] == b"%PDF-",
        "the file is a PDF" if data[:5] == b"%PDF-"
        else f"the file does not start with a PDF header (starts {data[:8]!r})",
    ))
    result.checks.append(Check(
        "is not empty", len(data) > 0,
        f"{len(data)} bytes" if data else "the file is empty",
    ))

    text = extract(data) if data[:5] == b"%PDF-" else ""
    result.text = text
    result.checks.append(Check(
        "has readable text", bool(text.strip()),
        f"{len(text)} characters of text" if text.strip()
        else "no text could be read; a scanned statement needs a human",
    ))

    found_account = contains_account(text, account)
    result.checks.append(Check(
        "account matches", found_account,
        f"the document names {account}" if found_account
        else f"the document does not name {account}, so it is not this account's statement",
    ))

    found_period = period_present(text, period)
    result.checks.append(Check(
        "period matches", found_period,
        f"the document covers {period}" if found_period
        else f"the document does not state the period {period}",
    ))

    if holder:
        found_holder = holder.lower() in text.lower()
        result.checks.append(Check(
            "holder matches", found_holder,
            f"the document names {holder}" if found_holder
            else f"the document does not name {holder}; nothing is accepted on "
                 "the account number alone",
        ))
    return result
