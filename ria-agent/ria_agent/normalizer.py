"""Task normalisation (Step 13, and OPEN_FINDINGS.md #8).

A Redtail task is free text written by a person in a hurry. This turns it into a
structured intent: which workflow, which entities, which artifacts, how sure.

The important part is that the intent carries the *resolved plan* -- which
account, which period -- and not only the workflow name. Misclassification is
not the sharp risk. "Retrieve statement", classified perfectly and pointed at
the wrong account, is, and a shadow log that records only the workflow label
cannot see it.

Every entity records where it came from. Constitution V: no value without
provenance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .classifier import Verdict
from .crm import CrmTask
from .matching import Match, find_account, resolve_sole_account
from .untrusted import describes_an_instruction
from .workflows import UNRECOGNISED, WORKFLOWS

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

_ISO_MONTH = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])\b")
_QUARTER = re.compile(r"(?i)\bQ([1-4])(?:\s+(20\d{2}))?\b")
_MONTH_NAME = re.compile(
    r"(?i)\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b(?:\s+(20\d{2}))?"
)
_LAST_YEAR = re.compile(r"(?i)\b(?:last|prior|previous)\s+year\b")
_ACCOUNT_IN_TEXT = re.compile(r"\b\d{4}[-\s]\d{4}\b")

#: What each workflow needs resolved before it could be acted on at all.
REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "statement_retrieval": ("account", "period"),
    "document_request": ("account", "period"),
    "tax_document_collection": ("account", "period"),
    "meeting_prep_packet": ("household", "account"),
    "balance_reconciliation": ("account",),
    "document_filing": ("household",),
    "acat_follow_up": ("account",),
    "account_linking": ("account",),
    "registration_change": ("account",),
    "rmd_preparation": ("account",),
    "distribution_paperwork": ("account",),
    "standing_instruction_verification": ("account",),
    "beneficiary_review": ("account",),
    "address_change": ("household",),
    "esign_chase": ("household",),
    "meeting_scheduling": ("household",),
}
_DEFAULT_REQUIREMENTS: tuple[str, ...] = ()


@dataclass(frozen=True)
class Entity:
    """A resolved value and where it was read from."""

    value: str
    source: str

    def __str__(self) -> str:
        return self.value


@dataclass
class Intent:
    """What the agent believes a task is asking for, and how sure it is."""

    task_id: str
    workflow_guess: str
    confidence: float
    basis: str
    template: str = ""
    entities: dict[str, Entity] = field(default_factory=dict)
    accounts: list[Entity] = field(default_factory=list)
    account: Match | None = None
    required_artifacts: tuple[str, ...] = ()
    blockers: list[str] = field(default_factory=list)
    injection_flags: list[str] = field(default_factory=list)

    @property
    def recognised(self) -> bool:
        return self.workflow_guess != UNRECOGNISED

    @property
    def ready(self) -> bool:
        """Everything the workflow needs is resolved, unambiguously."""
        return self.recognised and not self.blockers

    def get(self, name: str) -> str | None:
        entity = self.entities.get(name)
        return entity.value if entity else None

    def resolved_plan(self) -> dict:
        """The whole plan, for the shadow log and for a receipt.

        Recording only `workflow_guess` here would hide exactly the failure
        shadow mode exists to find.
        """
        return {
            "task_id": self.task_id,
            "template": self.template,
            "workflow": self.workflow_guess,
            "confidence": round(self.confidence, 3),
            "basis": self.basis,
            "account": self.account.value if self.account and self.account.found else None,
            "account_candidates": list(self.account.candidates) if self.account else [],
            "period": self.get("period"),
            "household": self.get("household"),
            "custodian": self.get("custodian"),
            "artifacts": list(self.required_artifacts),
            "blockers": list(self.blockers),
            "injection_flags": list(self.injection_flags),
            "ready": self.ready,
        }


def extract_period(text: str, source: str, today: date | None = None) -> Entity | None:
    """Find a statement period, most specific form first."""
    today = today or date.today()
    if not text:
        return None

    iso = _ISO_MONTH.search(text)
    if iso:
        return Entity(f"{iso.group(1)}-{iso.group(2)}", f"{source}:{iso.group(0)}")

    quarter = _QUARTER.search(text)
    if quarter:
        year = quarter.group(2) or str(today.year)
        return Entity(f"{year}-Q{quarter.group(1)}", f"{source}:{quarter.group(0)}")

    month = _MONTH_NAME.search(text)
    if month:
        number = MONTHS[month.group(1).lower()]
        year = int(month.group(2)) if month.group(2) else today.year
        if not month.group(2) and number > today.month:
            year -= 1  # a month later than today means last year's
        return Entity(f"{year:04d}-{number:02d}", f"{source}:{month.group(0)}")

    if _LAST_YEAR.search(text):
        return Entity(str(today.year - 1), f"{source}:last year")
    return None


def normalise(task: CrmTask, verdict: Verdict, today: date | None = None) -> Intent:
    """Turn a task and a classification into a structured, resolved intent."""
    intent = Intent(
        task_id=task.task_id,
        template=task.template,
        workflow_guess=verdict.workflow_id,
        confidence=verdict.confidence,
        basis=verdict.basis,
    )

    for text in (task.subject, task.notes):
        intent.injection_flags.extend(describes_an_instruction(text))

    if task.household:
        intent.entities["household"] = Entity(task.household, "redtail:household")
    elif task.contact_name:
        intent.entities["household"] = Entity(task.contact_name, "redtail:contact_name")
    if task.contact_name:
        intent.entities["contact"] = Entity(task.contact_name, "redtail:contact_name")
    if task.custodian:
        intent.entities["custodian"] = Entity(task.custodian, "redtail:custodian")

    intent.accounts = [
        Entity(number, "redtail:account_numbers") for number in task.account_numbers
    ]
    # Account numbers written into the subject count only when the CRM already
    # links them. Free text is a hint about which of the linked accounts was
    # meant, never a source of an account the record does not have.
    named = _ACCOUNT_IN_TEXT.search(task.subject or "")
    if named:
        match = find_account(named.group(0), [e.value for e in intent.accounts])
        intent.account = (
            Match(match.value, match.candidates)
            if match.found
            else Match(None, tuple(e.value for e in intent.accounts),
                       f"the subject names {named.group(0)}, which is not linked to this task")
        )
    else:
        intent.account = resolve_sole_account([e.value for e in intent.accounts])

    period = (
        extract_period(task.subject, "subject", today)
        or extract_period(task.notes, "notes", today)
    )
    if period:
        intent.entities["period"] = period

    workflow = WORKFLOWS.get(verdict.workflow_id)
    if workflow:
        intent.required_artifacts = workflow.required_artifacts

    intent.blockers = _blockers(intent, verdict)
    return intent


def _blockers(intent: Intent, verdict: Verdict) -> list[str]:
    """Everything standing between this intent and being actionable."""
    problems: list[str] = []
    if not verdict.recognised:
        return ["the agent does not recognise this task type"]
    if not verdict.actionable:
        problems.append(
            f"confidence {verdict.confidence:.0%} is below the threshold the "
            "whitelist requires"
        )

    for requirement in REQUIREMENTS.get(verdict.workflow_id, _DEFAULT_REQUIREMENTS):
        if requirement == "account":
            if intent.account is None or not intent.account.found:
                if intent.account is not None and intent.account.ambiguous:
                    problems.append(
                        "the task does not say which account it means, and "
                        f"{len(intent.account.candidates)} are linked"
                    )
                else:
                    problems.append(
                        intent.account.reason if intent.account and intent.account.reason
                        else "no account is linked to this task"
                    )
        elif requirement not in intent.entities:
            problems.append(f"no {requirement} could be resolved from the task")
    return problems
