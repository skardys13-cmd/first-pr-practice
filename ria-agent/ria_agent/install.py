"""Install, version, and the diagnostic bundle (Steps 44, F-40, F-41).

Version is pinned and checked at startup: an install behind the required version
refuses to run rather than behaving in a way nobody can reproduce.

The diagnostic bundle is how you see a failure at a customer site without
building a phone-home channel. It contains versions, stop reasons, timings and
counts, and no client data at all -- no names, no account numbers, no balances,
no file paths. The customer reads it before they send it, which is the point:
a channel you cannot inspect reintroduces every objection the local install
avoided.
"""

from __future__ import annotations

import json
import platform
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import AGENT_VERSION
from .log_store import LogStore

MINIMUM_PYTHON = (3, 11)


@dataclass(frozen=True)
class VersionCheck:
    ok: bool
    detail: str


def parse(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split(".") if part.isdigit())


def check_version(required: str | None, installed: str = AGENT_VERSION) -> VersionCheck:
    """Refuse to run when behind the version this firm has agreed to (F-40)."""
    if not required:
        return VersionCheck(True, f"agent {installed}, no minimum pinned")
    if parse(installed) < parse(required):
        return VersionCheck(False, (
            f"this install is agent {installed} and the firm requires at least "
            f"{required}. It will not run. Update, then re-run."
        ))
    return VersionCheck(True, f"agent {installed} meets the required {required}")


def check_python() -> VersionCheck:
    current = sys.version_info[:2]
    if current < MINIMUM_PYTHON:
        return VersionCheck(False, (
            f"Python {current[0]}.{current[1]} is too old; "
            f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer is required."
        ))
    return VersionCheck(True, f"Python {current[0]}.{current[1]}")


def doctor(storage_dir: str | Path, required: str | None = None) -> list[VersionCheck]:
    """Everything an install has to satisfy before it is allowed to work."""
    from .secrets_posture import scan
    from .startup import find_constitution

    storage = Path(storage_dir)
    checks = [check_python(), check_version(required)]

    try:
        checks.append(VersionCheck(True, f"constitution at {find_constitution()}"))
    except FileNotFoundError as failure:
        checks.append(VersionCheck(False, str(failure)))

    if not storage.exists():
        checks.append(VersionCheck(True, f"storage will be created at {storage}"))
    else:
        findings = scan(storage)
        checks.append(VersionCheck(
            not findings,
            "no credentials in application storage" if not findings
            else f"{len(findings)} credential-shaped value(s) in storage"))

        log_dir = storage / "log"
        if (log_dir / "receipts.db").exists():
            store = LogStore(log_dir)
            problems = store.verify_mirror()
            count = store.count()
            store.close()
            checks.append(VersionCheck(
                not problems,
                f"the log verifies ({count} receipts)" if not problems
                else f"the log does not verify: {problems[0]}"))
    return checks


def diagnostic_bundle(storage_dir: str | Path, destination: str | Path) -> Path:
    """A package the customer can read, then send. No client data in it."""
    storage = Path(storage_dir)
    bundle = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "agent_version": AGENT_VERSION,
        "python": platform.python_version(),
        "platform": platform.system(),
        "checks": [{"ok": c.ok, "detail": c.detail} for c in doctor(storage)],
    }

    log_dir = storage / "log"
    if (log_dir / "receipts.db").exists():
        store = LogStore(log_dir)
        receipts = store.query()
        durations = []
        for receipt in receipts:
            try:
                start = datetime.fromisoformat(receipt.timestamp_start)
                end = datetime.fromisoformat(receipt.timestamp_end)
                durations.append((end - start).total_seconds())
            except ValueError:
                continue
        bundle["log"] = {
            "receipts": len(receipts),
            # Counts and reasons only. No target identifiers, no owners, no
            # evidence values, no balances, no file paths.
            "outcomes": dict(Counter(r.outcome for r in receipts)),
            "workflows": dict(Counter(r.workflow_id for r in receipts)),
            "stop_reasons": dict(Counter(r.stop_reason for r in receipts if r.stop_reason)),
            "model_versions": sorted({r.model_version for r in receipts}),
            "agent_versions": sorted({r.agent_version for r in receipts}),
            "median_seconds": round(sorted(durations)[len(durations) // 2], 2) if durations else None,
            "slowest_seconds": round(max(durations), 2) if durations else None,
        }
        store.close()

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return destination
