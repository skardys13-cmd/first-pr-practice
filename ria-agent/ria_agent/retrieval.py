"""Statement retrieval, end to end (Steps 18-22, 24).

The first thing the agent's hands do. Chosen because it is the top daily pain,
it is read-only, and a human can check it in seconds.

Session, then navigation, then verification, then a receipt -- and the receipt
is what decides the outcome, not the navigation. A run that reached a file but
failed a check is Stopped, never Done.

Nothing here lands in Done & verified until the workflow has been promoted
(Step 24, gated by `promotion`). Until then every retrieval waits for a person,
even once it is running unattended.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import session, stops
from .browser import BrowserDriver
from .guardrails import DEFAULT_CLICK_BUDGET, Guardrails
from .log_store import LogStore
from .navigator import Navigator, NavigationResult, RetrievalGoal, StatementRetrievalPolicy
from .promotion import PromotionRegistry
from .receipts import (
    EXTRACTED_VALUE, Evidence, FILE_HASH, PAGE_SIGNATURE, PENDING_APPROVAL, READ,
    Receipt, SCREENSHOT, STOPPED_NO_CHANGE, URL, VERIFIED, now_iso,
)
from .verification import Verification, verify_statement

WORKFLOW_ID = "statement_retrieval"


@dataclass
class Retrieval:
    """One attempt, and everything that came of it."""

    receipt: Receipt
    navigation: NavigationResult | None = None
    verification: Verification | None = None
    artifact: Path | None = None

    @property
    def succeeded(self) -> bool:
        return self.receipt.outcome in (VERIFIED, PENDING_APPROVAL)

    @property
    def stop_reason(self) -> str | None:
        return self.receipt.stop_reason


class StatementRetrieval:
    """Retrieve one statement for one account, and prove which one it was."""

    def __init__(
        self,
        driver: BrowserDriver,
        log: LogStore,
        *,
        operator: str,
        role: str,
        model_version: str,
        allowed_domains: set[str] | list[str],
        evidence_dir: Path,
        promotions: PromotionRegistry | None = None,
        presence: session.HumanPresence | None = None,
        click_budget: int = DEFAULT_CLICK_BUDGET,
    ):
        self.driver = driver
        self.log = log
        self.operator = operator
        self.role = role
        self.model_version = model_version
        self.allowed_domains = allowed_domains
        self.evidence_dir = Path(evidence_dir)
        self.promotions = promotions
        self.presence = presence
        self.click_budget = click_budget

    def run(self, crm_task_id: str, goal: RetrievalGoal) -> Retrieval:
        started = now_iso()
        run_dir = self.evidence_dir / f"{crm_task_id}-{goal.account}-{goal.period}"

        state = session.detect(self.driver, self.presence)
        if not state.live:
            return self._stopped(crm_task_id, goal, started,
                                 state.stop_reason, state.detail, state.next_step)

        guardrails = Guardrails(self.allowed_domains, click_budget=self.click_budget)
        navigator = Navigator(
            self.driver, guardrails, StatementRetrievalPolicy(), evidence_dir=run_dir)
        navigation = navigator.pursue(goal, destination=run_dir / "statement.pdf")

        if not navigation.reached or navigation.artifact is None:
            # Nothing was written anywhere, so this is a clean stop. A workflow
            # that had already changed something would land in the cleanup lane
            # instead, with an instruction saying what to undo.
            return self._stopped(
                crm_task_id, goal, started, navigation.stop_reason or stops.ELEMENT_NOT_FOUND,
                navigation.detail, navigation.next_step, navigation=navigation)

        verification = verify_statement(
            navigation.artifact, account=goal.account, period=goal.period,
            holder=goal.holder or None)

        if not verification.passed:
            return self._stopped(
                crm_task_id, goal, started, stops.VERIFICATION_FAILED,
                verification.summary(), stops.next_step_for(stops.VERIFICATION_FAILED),
                navigation=navigation, verification=verification,
                artifact=navigation.artifact)

        return self._verified(crm_task_id, goal, started, navigation, verification)

    # -- receipts ----------------------------------------------------------

    def _final_screenshot(self, navigation: NavigationResult | None) -> list[Evidence]:
        if navigation is None or not navigation.steps:
            return []
        last = navigation.steps[-1]
        pieces = [Evidence(PAGE_SIGNATURE, last.signature, source_location=last.url)]
        if last.screenshot:
            pieces.append(Evidence(SCREENSHOT, last.screenshot.name,
                                   source_location=str(last.screenshot.parent)))
        return pieces

    def _stopped(
        self, crm_task_id, goal, started, reason, detail, next_step,
        navigation=None, verification=None, artifact=None,
    ) -> Retrieval:
        evidence = self._final_screenshot(navigation)
        if verification is not None and verification.file_hash:
            evidence.append(Evidence(
                FILE_HASH, verification.file_hash,
                source_location=str(artifact) if artifact else "downloaded file"))
            for check in verification.failures:
                evidence.append(Evidence(
                    EXTRACTED_VALUE, f"{check.name}: {check.detail}",
                    source_location="verification"))
        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=WORKFLOW_ID, step_id="retrieve_statement",
            system_touched=_host(navigation) or "custodian", action_type=READ,
            target_identifier=f"{goal.account} / {goal.period}",
            outcome=STOPPED_NO_CHANGE, stop_reason=reason,
            stop_next_step=next_step or stops.next_step_for(reason),
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version, evidence=evidence,
        )
        self.log.append(receipt)
        return Retrieval(receipt, navigation, verification, artifact)

    def _verified(self, crm_task_id, goal, started, navigation, verification) -> Retrieval:
        promoted = bool(
            self.promotions and self.promotions.is_promoted(WORKFLOW_ID, self.role)
        )
        evidence = [
            Evidence(FILE_HASH, verification.file_hash,
                     source_location=str(navigation.artifact)),
            Evidence(URL, navigation.pages_visited[-1] if navigation.pages_visited else ""),
            Evidence(EXTRACTED_VALUE, goal.account,
                     source_location=f"{navigation.artifact.name}:account number"),
            Evidence(EXTRACTED_VALUE, goal.period,
                     source_location=f"{navigation.artifact.name}:statement period"),
        ]
        if goal.holder:
            evidence.append(Evidence(
                EXTRACTED_VALUE, goal.holder,
                source_location=f"{navigation.artifact.name}:account holder"))
        evidence.extend(self._final_screenshot(navigation))

        receipt = Receipt(
            human_owner=self.operator, role=self.role, crm_task_id=crm_task_id,
            workflow_id=WORKFLOW_ID, step_id="retrieve_statement",
            system_touched=_host(navigation) or "custodian", action_type=READ,
            target_identifier=f"{goal.account} / {goal.period}",
            # Step 24: unattended retrieval still waits for a person until the
            # workflow is promoted on its verification record.
            outcome=VERIFIED if promoted else PENDING_APPROVAL,
            auto_executed=promoted,
            timestamp_start=started, timestamp_end=now_iso(),
            model_version=self.model_version, evidence=evidence,
        )
        self.log.append(receipt)
        return Retrieval(receipt, navigation, verification, navigation.artifact)


def _host(navigation: NavigationResult | None) -> str:
    if not navigation or not navigation.pages_visited:
        return ""
    from urllib.parse import urlparse
    host = urlparse(navigation.pages_visited[0]).hostname or ""
    return host.split(".")[1] if host.count(".") >= 2 else host
