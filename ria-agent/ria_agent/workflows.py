"""The six clusters and the workflows inside them (Step 14).

Roughly forty workflows were mapped at cluster level. This is the catalogue the
classifier chooses from, and the entry point checks against. A workflow that is
not here cannot be selected, which is why "unrecognised" has to be a first-class
answer rather than a fallback to the nearest match.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- The six clusters ------------------------------------------------------

CLIENT_MEETING_CYCLE = "client_meeting_cycle"
ACCOUNT_LIFECYCLE = "account_lifecycle"
MONEY_MOVEMENT_PREP = "money_movement_prep"
ANNUAL_CYCLES = "annual_cycles"
CLIENT_SERVICE = "client_service"
FIRM_OPERATIONS = "firm_operations"

CLUSTERS = {
    CLIENT_MEETING_CYCLE: "Client meeting cycle",
    ACCOUNT_LIFECYCLE: "Account lifecycle",
    MONEY_MOVEMENT_PREP: "Money movement prep",
    ANNUAL_CYCLES: "Annual cycles",
    CLIENT_SERVICE: "Client service",
    FIRM_OPERATIONS: "Firm operations",
}

#: Not a workflow. The honest answer when nothing fits, and a success state.
UNRECOGNISED = "unrecognised"


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    name: str
    cluster: str
    read_only: bool
    systems: tuple[str, ...] = ()
    required_artifacts: tuple[str, ...] = ()


def _w(*args, **kwargs) -> Workflow:
    return Workflow(*args, **kwargs)


WORKFLOWS: dict[str, Workflow] = {w.workflow_id: w for w in [
    # 1. Client meeting cycle
    _w("statement_retrieval", "Statement retrieval", CLIENT_MEETING_CYCLE, True,
       ("custodian",), ("statement_pdf",)),
    _w("meeting_prep_packet", "Meeting prep packet", CLIENT_MEETING_CYCLE, True,
       ("custodian", "orion", "nitrogen", "redtail"),
       ("statement_pdf", "performance_report", "risk_report", "agenda")),
    _w("post_meeting_notes", "Post-meeting notes and tasks", CLIENT_MEETING_CYCLE, False,
       ("redtail",), ("meeting_notes",)),

    # 2. Account lifecycle
    _w("new_account_application", "New account application prep", ACCOUNT_LIFECYCLE, False,
       ("custodian", "redtail"), ("application_form",)),
    _w("acat_follow_up", "Transfer / ACAT follow-up", ACCOUNT_LIFECYCLE, True,
       ("custodian",), ("transfer_status",)),
    _w("account_linking", "Account linking", ACCOUNT_LIFECYCLE, False,
       ("redtail", "orion"), ()),
    _w("registration_change", "Registration change", ACCOUNT_LIFECYCLE, False,
       ("custodian", "redtail"), ("registration_form",)),
    _w("account_closure", "Account closure", ACCOUNT_LIFECYCLE, False,
       ("custodian", "redtail"), ()),

    # 3. Money movement prep
    _w("distribution_paperwork", "Distribution paperwork prep", MONEY_MOVEMENT_PREP, False,
       ("custodian",), ("distribution_form",)),
    _w("rmd_preparation", "RMD preparation", MONEY_MOVEMENT_PREP, False,
       ("custodian", "orion"), ("rmd_calculation", "distribution_form")),
    _w("standing_instruction_verification", "Standing instruction verification",
       MONEY_MOVEMENT_PREP, True, ("custodian",), ("standing_instructions",)),
    _w("journal_prep", "Journal preparation", MONEY_MOVEMENT_PREP, False,
       ("custodian",), ("journal_form",)),

    # 4. Annual cycles
    _w("tax_document_collection", "Tax document collection", ANNUAL_CYCLES, True,
       ("custodian",), ("tax_document",)),
    _w("beneficiary_review", "Beneficiary and account review", ANNUAL_CYCLES, True,
       ("custodian", "redtail"), ("beneficiary_listing",)),
    _w("fee_billing_verification", "Fee billing verification", ANNUAL_CYCLES, True,
       ("orion",), ("fee_report",)),

    # 5. Client service
    _w("document_filing", "Document filing and naming", CLIENT_SERVICE, False,
       ("redtail",), ()),
    _w("address_change", "Address or profile change", CLIENT_SERVICE, False,
       ("custodian", "redtail"), ("change_form",)),
    _w("document_request", "Client document request", CLIENT_SERVICE, True,
       ("custodian",), ("statement_pdf",)),
    _w("esign_chase", "E-sign follow-up", CLIENT_SERVICE, True,
       ("esign",), ("envelope_status",)),
    _w("meeting_scheduling", "Meeting scheduling", CLIENT_SERVICE, False,
       ("calendar", "redtail"), ()),
    _w("inbound_triage", "Inbound request triage", CLIENT_SERVICE, True,
       ("redtail",), ()),

    # 6. Firm operations
    _w("balance_reconciliation", "Balance reconciliation", FIRM_OPERATIONS, True,
       ("custodian", "redtail", "orion", "nitrogen"), ("balance_comparison",)),
    _w("account_linkage_audit", "Account linkage audit", FIRM_OPERATIONS, True,
       ("redtail", "orion", "nitrogen"), ("linkage_report",)),
    _w("data_hygiene", "CRM data hygiene", FIRM_OPERATIONS, True,
       ("redtail",), ("exception_list",)),
    _w("kpi_extraction", "KPI extraction", FIRM_OPERATIONS, True,
       ("redtail", "orion"), ("kpi_report",)),
    _w("compliance_calendar", "Compliance calendar support", FIRM_OPERATIONS, True,
       ("redtail",), ()),
]}


def get(workflow_id: str) -> Workflow | None:
    return WORKFLOWS.get(workflow_id)


def is_known(workflow_id: str) -> bool:
    return workflow_id in WORKFLOWS


def in_cluster(cluster: str) -> list[Workflow]:
    return [w for w in WORKFLOWS.values() if w.cluster == cluster]


def read_only_ids() -> set[str]:
    return {w.workflow_id for w in WORKFLOWS.values() if w.read_only}
