"""Role scoping (Constitution VI).

Capability is bound to the human's role, not to what the software permits. A
role gets a workflow only when a person in that seat already does that work by
hand today, and the agent never acquires a permission its human lacks.

The adviser role is read-only by design: briefing and prep, no writes, ever.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import workflows
from .receipts import PROPOSE, READ, WRITE

PARA_PLANNER = "para_planner"
CLIENT_SERVICE = "client_service"
ADVISER = "adviser"


@dataclass(frozen=True)
class Role:
    role_id: str
    name: str
    workflows: frozenset[str]
    action_types: frozenset[str]
    systems: frozenset[str]

    def permits(self, workflow_id: str, action_type: str = READ) -> bool:
        return workflow_id in self.workflows and action_type in self.action_types

    def refusal(self, workflow_id: str, action_type: str = READ) -> str | None:
        """Why this is not allowed, in words for the queue. None if it is."""
        if workflow_id not in self.workflows:
            return (
                f"{self.name} does not do "
                f"{workflows.WORKFLOWS[workflow_id].name.lower()}"
                if workflows.is_known(workflow_id)
                else f"{self.name} has no workflow called {workflow_id!r}"
            )
        if action_type not in self.action_types:
            return f"{self.name} is not permitted to {action_type} in any system"
        return None


ROLES: dict[str, Role] = {
    PARA_PLANNER: Role(
        PARA_PLANNER, "Para planner",
        workflows=frozenset({
            "statement_retrieval", "meeting_prep_packet", "document_filing",
            "acat_follow_up", "account_linking", "new_account_application",
            "registration_change", "balance_reconciliation",
            "account_linkage_audit", "tax_document_collection",
            "beneficiary_review", "rmd_preparation", "distribution_paperwork",
            "standing_instruction_verification", "data_hygiene",
            "fee_billing_verification",
        }),
        action_types=frozenset({READ, PROPOSE, WRITE}),
        systems=frozenset({"redtail", "orion", "nitrogen", "schwab", "fidelity", "pershing"}),
    ),
    CLIENT_SERVICE: Role(
        CLIENT_SERVICE, "Client service",
        workflows=frozenset({
            "meeting_scheduling", "document_filing", "document_request",
            "esign_chase", "address_change", "inbound_triage",
            "meeting_prep_packet", "statement_retrieval", "post_meeting_notes",
        }),
        action_types=frozenset({READ, PROPOSE, WRITE}),
        systems=frozenset({"redtail", "esign", "calendar", "schwab", "fidelity", "pershing"}),
    ),
    ADVISER: Role(
        ADVISER, "Adviser",
        # Read-only by design (plan 1.4). Briefing and prep, never a write.
        workflows=frozenset({
            "meeting_prep_packet", "statement_retrieval", "balance_reconciliation",
            "kpi_extraction", "compliance_calendar",
        }),
        action_types=frozenset({READ}),
        systems=frozenset({"redtail", "orion", "nitrogen", "schwab", "fidelity", "pershing"}),
    ),
}


def get(role_id: str) -> Role | None:
    return ROLES.get(role_id)


class UnknownRole(KeyError):
    def __init__(self, role_id: str):
        super().__init__(
            f"no role {role_id!r}. Roles are configured per install and must "
            f"be one of: {sorted(ROLES)}"
        )


def require(role_id: str) -> Role:
    role = ROLES.get(role_id)
    if role is None:
        raise UnknownRole(role_id)
    return role
