"""Task intent classification (Step 14).

Rules first, model for the tail, "unrecognised" whenever neither is sure.

Most CRM tasks come off a template, so most are classified by a rule that can be
read, argued with, and pointed at during a compliance review -- and never leave
the machine. Only genuine novelty reaches the model, which is the cheapest
available answer to the egress problem in OPEN_FINDINGS.md #1.

An honest "I do not know what this task is" is a success state, and it is the
common outcome by design. The alternative -- picking the nearest workflow -- is
F-29, the classifier being confidently wrong and executing the wrong thing.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .crm import CrmTask
from .untrusted import fence
from .workflows import UNRECOGNISED, is_known

#: Below this, a verdict is not actionable regardless of where it came from.
CONFIDENCE_FLOOR = 0.85

TEMPLATE_RULES = {
    "Statement Retrieval": "statement_retrieval",
    "Client Review - Prep Packet": "meeting_prep_packet",
    "Client Review - Post Meeting": "post_meeting_notes",
    "Document Filing": "document_filing",
    "Document Request": "document_request",
    "New Account - Application Prep": "new_account_application",
    "Transfer - ACAT Follow Up": "acat_follow_up",
    "Account Linking": "account_linking",
    "Registration Change": "registration_change",
    "Account Closure": "account_closure",
    "RMD Preparation": "rmd_preparation",
    "Distribution - Paperwork Prep": "distribution_paperwork",
    "Standing Instruction Verification": "standing_instruction_verification",
    "Journal Preparation": "journal_prep",
    "Tax Document Collection": "tax_document_collection",
    "Beneficiary Review": "beneficiary_review",
    "Fee Billing Verification": "fee_billing_verification",
    "Profile Change - Address": "address_change",
    "E-Sign Follow Up": "esign_chase",
    "Meeting Scheduling": "meeting_scheduling",
    "Balance Reconciliation": "balance_reconciliation",
    "Account Linkage Audit": "account_linkage_audit",
    "Data Hygiene": "data_hygiene",
}

#: Weaker than a template: a category narrows the field but rarely names the
#: workflow on its own, so these only fire where the category maps to exactly
#: one thing the firm does.
CATEGORY_RULES = {
    "Document Retrieval": "statement_retrieval",
    "Document Management": "document_filing",
    "Transfers": "acat_follow_up",
    "Account Opening": "new_account_application",
    "Distributions": "distribution_paperwork",
    "Tax": "tax_document_collection",
    "Billing": "fee_billing_verification",
}

#: Last resort before the model. Ordered: the first match wins, so the more
#: specific patterns come first.
KEYWORD_RULES: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r"(?i)\brmd\b|\brequired minimum distribution\b"), "rmd_preparation", 0.88),
    (re.compile(r"(?i)\bacat\b|\btransfer status\b"), "acat_follow_up", 0.88),
    (re.compile(r"(?i)\breconcil\w*\b.{0,30}\bbalance|\bbalance\w*\b.{0,30}\breconcil"), "balance_reconciliation", 0.9),
    (re.compile(r"(?i)\be-?sign\b|\bdocusign\b|\benvelope\b"), "esign_chase", 0.88),
    (re.compile(r"(?i)\bbeneficiar\w+\b"), "beneficiary_review", 0.87),
    (re.compile(r"(?i)\baddress change\b|\bchange of address\b"), "address_change", 0.9),
    (re.compile(r"(?i)\b(?:1099|tax document|tax package)\b"), "tax_document_collection", 0.88),
    (re.compile(r"(?i)\blink\w*\b.{0,25}\b(?:account|orion|redtail|nitrogen)\b"), "account_linking", 0.86),
    (re.compile(r"(?i)\bstanding instruction\w*\b"), "standing_instruction_verification", 0.9),
    (re.compile(r"(?i)\b(?:pull|retrieve|download|get)\b.{0,30}\bstatements?\b"), "statement_retrieval", 0.88),
    (re.compile(r"(?i)\bstatements?\b.{0,20}\b(?:pull|retriev\w+|download)\b"), "statement_retrieval", 0.88),
    (re.compile(r"(?i)\b(?:prep|prepare)\b.{0,20}\bpacket\b|\bprep packet\b"), "meeting_prep_packet", 0.88),
    (re.compile(r"(?i)\bfile\b.{0,25}\b(?:document|statement|scan)\w*\b"), "document_filing", 0.86),
    (re.compile(r"(?i)\bschedule\b.{0,25}\b(?:meeting|review|call)\b"), "meeting_scheduling", 0.87),
]

TEMPLATE = "template"
CATEGORY = "category"
KEYWORD = "keyword"
MODEL = "model"
NO_MATCH = "no_match"


@dataclass(frozen=True)
class Verdict:
    """What the classifier thinks, how sure, and on what basis."""

    workflow_id: str
    confidence: float
    basis: str
    matched_on: str = ""

    @property
    def recognised(self) -> bool:
        return self.workflow_id != UNRECOGNISED

    @property
    def actionable(self) -> bool:
        return self.recognised and self.confidence >= CONFIDENCE_FLOOR

    def describe(self) -> str:
        if not self.recognised:
            return "No rule matched and the model could not place it either."
        where = {
            TEMPLATE: f"the task template {self.matched_on!r}",
            CATEGORY: f"the task category {self.matched_on!r}",
            KEYWORD: f"the phrase {self.matched_on!r} in the subject",
            MODEL: "the model, because no rule matched",
        }.get(self.basis, self.basis)
        return f"Matched on {where}."


UNKNOWN = Verdict(UNRECOGNISED, 0.0, NO_MATCH)


class ModelClient(ABC):
    """The model tail. Only reached when no rule matches."""

    version = "unset"

    @abstractmethod
    def classify(self, prompt: str, choices: list[str]) -> Verdict:
        """Return a Verdict, which may be UNKNOWN. Never raise on uncertainty."""


class Classifier:
    def __init__(self, model: ModelClient | None = None, floor: float = CONFIDENCE_FLOOR):
        self.model = model
        self.floor = floor

    def classify(self, task: CrmTask) -> Verdict:
        for rule in (self._by_template, self._by_category, self._by_keyword):
            verdict = rule(task)
            if verdict is not None:
                return verdict
        return self._by_model(task)

    # -- rules -------------------------------------------------------------

    def _by_template(self, task: CrmTask) -> Verdict | None:
        workflow_id = TEMPLATE_RULES.get(task.template.strip())
        if workflow_id is None:
            return None
        return Verdict(workflow_id, 0.99, TEMPLATE, task.template.strip())

    def _by_category(self, task: CrmTask) -> Verdict | None:
        workflow_id = CATEGORY_RULES.get(task.category.strip())
        if workflow_id is None:
            return None
        return Verdict(workflow_id, 0.9, CATEGORY, task.category.strip())

    def _by_keyword(self, task: CrmTask) -> Verdict | None:
        for pattern, workflow_id, confidence in KEYWORD_RULES:
            match = pattern.search(task.subject or "")
            if match:
                return Verdict(workflow_id, confidence, KEYWORD, match.group(0))
        return None

    # -- the tail ----------------------------------------------------------

    def _by_model(self, task: CrmTask) -> Verdict:
        if self.model is None:
            return UNKNOWN
        verdict = self.model.classify(self._prompt(task), sorted(TEMPLATE_RULES.values()))
        if verdict is None or not verdict.recognised:
            return UNKNOWN
        if not is_known(verdict.workflow_id):
            # A model naming a workflow that does not exist is not a near miss.
            return UNKNOWN
        return Verdict(verdict.workflow_id, min(verdict.confidence, 0.95),
                       MODEL, verdict.matched_on or "model")

    @staticmethod
    def _prompt(task: CrmTask) -> str:
        """What gets sent, and deliberately what does not.

        The notes field carries the most client detail and the most instruction
        -shaped text, and it is the least useful signal for naming a workflow.
        It is not sent. Account numbers are masked. What leaves is a task
        subject, a template, and a category.
        """
        subject = re.sub(r"\b\d{3,}[-\s]?\d{3,}\b", "[account]", task.subject or "")
        return fence_task(subject, task.template, task.category)


def fence_task(subject: str, template: str, category: str) -> str:
    from .untrusted import Untrusted
    return (
        "Name the single workflow this task refers to, or say unrecognised.\n"
        f"Template: {template or '(none)'}\nCategory: {category or '(none)'}\n\n"
        + fence(Untrusted("task_subject", subject, "redtail"))
    )
