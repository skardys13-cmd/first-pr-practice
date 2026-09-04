"""Synthetic queue data (Step 11).

Step 11 says: seed the queue, use the UI for a week against fake data, and fix
what is annoying before real data touches it. This generates that week.

Everything here is invented. No real household, account, or balance appears,
and the generator is seeded so a run is reproducible when something looks wrong.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .receipts import (
    Evidence, EXTRACTED_VALUE, FILE_HASH, PENDING_APPROVAL, PROPOSE, READ,
    Receipt, SCREENSHOT, STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, URL, VERIFIED,
)
from .stops import next_step_for

HOUSEHOLDS = [
    "Barrow", "Ferreira", "Okonkwo", "Lindqvist", "Nakamura",
    "Abernathy", "Villanueva", "Whitcombe", "Oyelaran", "Castellanos",
]
CUSTODIANS = ["schwab", "fidelity", "pershing"]
PEOPLE = [("Ant", "para_planner"), ("Bea", "client_service")]

CLEAN_STOPS = [
    "session_expired", "not_logged_in", "mfa_challenge", "element_not_found",
    "ambiguous_match", "low_confidence", "timeout", "unrecognised_task",
    "task_type_not_whitelisted", "consent_interstitial",
]

CLEANUP_STOPS = {
    "session_expired": (
        "A document was uploaded to Redtail but not renamed or tagged. It is "
        "currently filed as \"scan_{n:04d}.pdf\" under the {household} household."
    ),
    "environment_interrupted": (
        "The machine slept midway through filing. The document reached Redtail "
        "under the {household} household but the account link was not set."
    ),
}


def _account_number(rng: random.Random) -> str:
    return f"{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def generate(
    count: int = 40,
    *,
    seed: int = 20260904,
    model_version: str = "claude-x-1",
    evidence_dir: Path | None = None,
    start: datetime | None = None,
) -> list[Receipt]:
    """A plausible day's worth of mixed outcomes."""
    rng = random.Random(seed)
    when = start or datetime.now(timezone.utc).replace(
        hour=8, minute=5, second=0, microsecond=0
    )
    receipts: list[Receipt] = []

    for index in range(count):
        when += timedelta(minutes=rng.randint(3, 17))
        owner, role = rng.choice(PEOPLE)
        household = rng.choice(HOUSEHOLDS)
        custodian = rng.choice(CUSTODIANS)
        account = _account_number(rng)
        period = f"2026-0{rng.randint(6, 8)}"
        roll = rng.random()

        if roll < 0.45:
            receipts.append(_retrieval(
                rng, when, owner, role, household, custodian, account, period,
                model_version, evidence_dir))
        elif roll < 0.75:
            receipts.append(_filing_proposal(
                rng, when, owner, role, household, custodian, account, period,
                model_version, evidence_dir))
        elif roll < 0.93:
            receipts.append(_clean_stop(
                rng, when, owner, role, household, custodian, account,
                model_version, evidence_dir))
        else:
            receipts.append(_cleanup_stop(
                rng, when, owner, role, household, custodian, account,
                model_version, evidence_dir))
    return receipts


def _times(when: datetime, seconds: int) -> tuple[str, str]:
    return (
        when.isoformat(timespec="seconds"),
        (when + timedelta(seconds=seconds)).isoformat(timespec="seconds"),
    )


def _shot(evidence_dir: Path | None, name: str) -> list[Evidence]:
    """Write a placeholder screenshot so the UI has something to render."""
    if evidence_dir is None:
        return []
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / f"{name}.svg"
    if not path.exists():
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="150">'
            '<rect width="520" height="150" fill="#eef1f5" stroke="#c3ccd8"/>'
            f'<text x="20" y="55" font-family="Helvetica" font-size="15" fill="#38414d">'
            f'synthetic screenshot</text>'
            f'<text x="20" y="85" font-family="Helvetica" font-size="13" fill="#69737f">'
            f'{name}</text>'
            '<text x="20" y="115" font-family="Helvetica" font-size="12" fill="#8a939d">'
            'no real client data appears in synthetic items</text></svg>',
            encoding="utf-8",
        )
    return [Evidence(SCREENSHOT, path.name, source_location="evidence")]


def _retrieval(rng, when, owner, role, household, custodian, account, period,
               model_version, evidence_dir) -> Receipt:
    start, end = _times(when, rng.randint(20, 90))
    return Receipt(
        human_owner=owner, role=role, crm_task_id=f"RT-{rng.randint(4000, 4999)}",
        workflow_id="statement_retrieval", step_id="retrieve_statement",
        system_touched=custodian, action_type=READ,
        target_identifier=account, outcome=VERIFIED,
        timestamp_start=start, timestamp_end=end,
        confidence=round(rng.uniform(0.93, 0.99), 2),
        model_version=model_version,
        evidence=[
            Evidence(FILE_HASH, _hash(f"{account}{period}"),
                     source_location=f"{period} {household} statement.pdf"),
            Evidence(EXTRACTED_VALUE, account, source_location="pdf:page 1, header"),
            Evidence(EXTRACTED_VALUE, period, source_location="pdf:page 1, statement period"),
            Evidence(URL, f"https://portal.{custodian}.example/statements/{account}"),
        ] + _shot(evidence_dir, f"retrieval-{account}-{period}"),
    )


def _filing_proposal(rng, when, owner, role, household, custodian, account,
                     period, model_version, evidence_dir) -> Receipt:
    start, end = _times(when, rng.randint(10, 40))
    scan = f"scan_{rng.randint(1, 9999):04d}.pdf"
    proper = f"{period} {custodian.title()} Statement - {household} {account}.pdf"
    return Receipt(
        human_owner=owner, role=role, crm_task_id=f"RT-{rng.randint(4000, 4999)}",
        workflow_id="document_filing", step_id="propose_filing",
        system_touched="redtail", action_type=PROPOSE,
        target_identifier=f"{household} / {account}", outcome=PENDING_APPROVAL,
        timestamp_start=start, timestamp_end=end,
        confidence=round(rng.uniform(0.86, 0.99), 2),
        model_version=model_version,
        before_state={
            "filename": scan,
            "folder": "Unfiled",
            "linked_account": "",
            "tags": "",
        },
        after_state={
            "filename": proper,
            "folder": f"{household} / Statements / 2026",
            "linked_account": account,
            "tags": "statement, custodian",
        },
        evidence=[
            Evidence(FILE_HASH, _hash(scan), source_location=scan),
            Evidence(EXTRACTED_VALUE, account, source_location="pdf:page 1, header"),
            Evidence(EXTRACTED_VALUE, household, source_location="pdf:page 1, addressee"),
            Evidence(EXTRACTED_VALUE, period, source_location="pdf:page 1, statement period"),
        ] + _shot(evidence_dir, f"filing-{account}"),
    )


def _clean_stop(rng, when, owner, role, household, custodian, account,
                model_version, evidence_dir) -> Receipt:
    start, end = _times(when, rng.randint(5, 30))
    reason = rng.choice(CLEAN_STOPS)
    return Receipt(
        human_owner=owner, role=role, crm_task_id=f"RT-{rng.randint(4000, 4999)}",
        workflow_id=rng.choice(["statement_retrieval", "document_filing", "esign_chase"]),
        step_id="retrieve_statement", system_touched=custodian,
        action_type=READ, target_identifier=account,
        outcome=STOPPED_NO_CHANGE, stop_reason=reason,
        stop_next_step=next_step_for(reason),
        timestamp_start=start, timestamp_end=end,
        confidence=round(rng.uniform(0.2, 0.7), 2) if reason == "low_confidence" else None,
        model_version=model_version,
        evidence=_shot(evidence_dir, f"stop-{reason}"),
    )


def _cleanup_stop(rng, when, owner, role, household, custodian, account,
                  model_version, evidence_dir) -> Receipt:
    start, end = _times(when, rng.randint(30, 120))
    reason = rng.choice(list(CLEANUP_STOPS))
    instruction = CLEANUP_STOPS[reason].format(
        n=rng.randint(1, 9999), household=household
    )
    return Receipt(
        human_owner=owner, role=role, crm_task_id=f"RT-{rng.randint(4000, 4999)}",
        workflow_id="document_filing", step_id="file_document",
        system_touched="redtail", action_type=READ,
        target_identifier=f"{household} / {account}",
        outcome=STOPPED_CLEANUP_REQUIRED, stop_reason=reason,
        stop_next_step=next_step_for(reason),
        cleanup_instruction=instruction,
        timestamp_start=start, timestamp_end=end,
        model_version=model_version,
        evidence=_shot(evidence_dir, f"cleanup-{account}"),
    )
