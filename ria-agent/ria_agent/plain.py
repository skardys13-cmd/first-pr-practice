"""Plain-language rendering of receipts (Steps 5 and 8).

The test for this module is in Step 5: someone unfamiliar with the system reads
a day's export and understands what happened, with nobody sitting next to them.
So no field names, no enum values, no jargon leaks into the output here.

Used by both the exporter and the queue UI so the two can never drift into
telling different stories about the same receipt.
"""

from __future__ import annotations

from .receipts import (
    APPROVE, PENDING_APPROVAL, PROPOSE, READ, REJECT, Receipt,
    STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED, WRITE,
)

LANE_NAMES = {
    VERIFIED: "Done & verified",
    PENDING_APPROVAL: "Ready for approval",
    STOPPED_NO_CHANGE: "Stopped — nothing changed",
    STOPPED_CLEANUP_REQUIRED: "Stopped — needs cleanup",
}

LANE_BLURBS = {
    VERIFIED: "Finished, checked, and evidenced. Nothing is needed from you.",
    PENDING_APPROVAL: "Prepared but not applied. It takes effect only when you approve it.",
    STOPPED_NO_CHANGE: "The agent halted before changing anything. Nothing was left half-done.",
    STOPPED_CLEANUP_REQUIRED: "The agent halted after something had already changed. This one needs you.",
}

ACTION_VERBS = {
    READ: "Read",
    PROPOSE: "Prepared",
    WRITE: "Wrote to",
    APPROVE: "Approved",
    REJECT: "Rejected",
}

WORKFLOW_NAMES = {
    "statement_retrieval": "statement retrieval",
    "document_filing": "document filing",
    "balance_reconciliation": "balance reconciliation",
    "account_linkage_check": "account linkage check",
    "meeting_prep": "meeting preparation",
    "esign_chase": "e-sign follow-up",
    "task_classification": "task classification",
}

SYSTEM_NAMES = {
    "schwab": "Schwab",
    "redtail": "Redtail",
    "orion": "Orion",
    "nitrogen": "Nitrogen",
    "fidelity": "Fidelity",
}

REJECTION_PHRASES = {
    "wrong_target": "it was pointed at the wrong client or account",
    "wrong_document": "it was the wrong document",
    "wrong_naming": "the name or filing location was wrong",
    "bad_extraction": "a value was read incorrectly",
    "not_needed": "it did not need doing",
    "already_done": "it had already been done",
    "against_policy": "it is against firm policy",
    "other": "another reason",
}


def workflow_name(workflow_id: str) -> str:
    return WORKFLOW_NAMES.get(workflow_id, workflow_id.replace("_", " "))


def system_name(system: str) -> str:
    return SYSTEM_NAMES.get(system, system.replace("_", " ").title())


def lane_name(outcome: str) -> str:
    return LANE_NAMES.get(outcome, outcome)


def headline(receipt: Receipt) -> str:
    """One line that says what this was, for a list view."""
    verb = ACTION_VERBS.get(receipt.action_type, receipt.action_type)
    return (
        f"{verb} {system_name(receipt.system_touched)} "
        f"for {receipt.target_identifier} "
        f"({workflow_name(receipt.workflow_id)})"
    )


def diff_rows(before: dict | None, after: dict | None) -> list[tuple[str, str, str]]:
    """Field-by-field before/after.

    F-35's structural fix: approval should require seeing what changes, so the
    UI and the export both show a diff rather than a description of one.
    """
    before = before or {}
    after = after or {}
    rows = []
    for key in sorted(set(before) | set(after)):
        was = before.get(key, "")
        now = after.get(key, "")
        rows.append((
            key.replace("_", " "),
            "—" if was == "" else str(was),
            "—" if now == "" else str(now),
        ))
    return rows


def describe(receipt: Receipt) -> list[tuple[str, str]]:
    """The receipt as titled prose sections, in reading order."""
    sections: list[tuple[str, str]] = []

    sections.append((
        "What was attempted",
        f"{ACTION_VERBS.get(receipt.action_type, receipt.action_type)} "
        f"{system_name(receipt.system_touched)}, as part of "
        f"{workflow_name(receipt.workflow_id)}, at the step called "
        f"\"{receipt.step_id.replace('_', ' ')}\". "
        f"The target was {receipt.target_identifier}. "
        f"This was for {receipt.human_owner} ({receipt.role.replace('_', ' ')}), "
        f"against task {receipt.crm_task_id}.",
    ))

    sections.append((
        "What happened",
        f"{lane_name(receipt.outcome)}. {LANE_BLURBS.get(receipt.outcome, '')}",
    ))

    if receipt.confidence is not None:
        sections.append((
            "How sure the agent was",
            f"{receipt.confidence:.0%}. "
            + (
                "Below the threshold, so it was not acted on."
                if receipt.confidence < 0.85
                else "Above the threshold the whitelist requires."
            ),
        ))

    if receipt.stop_reason:
        sections.append((
            "Why it stopped",
            receipt.stop_reason.replace("_", " ").capitalize() + ".",
        ))
    if receipt.stop_next_step:
        sections.append(("What to do next", receipt.stop_next_step))
    if receipt.cleanup_instruction:
        sections.append((
            "What was left changed",
            receipt.cleanup_instruction
            + " Until someone does this, the system is in a state neither the "
              "agent nor you should assume anything about.",
        ))

    if receipt.action_type in (PROPOSE, WRITE):
        rows = diff_rows(receipt.before_state, receipt.after_state)
        if rows:
            verb = "would change" if receipt.action_type == PROPOSE else "changed"
            lines = [f"This {verb}:"]
            lines += [f"    {field}: {was}  ->  {now}" for field, was, now in rows]
            sections.append(("What changes", "\n".join(lines)))

    if receipt.action_type == APPROVE:
        sections.append((
            "Approval",
            f"{receipt.approver} approved this at {receipt.approval_timestamp}.",
        ))
    if receipt.action_type == REJECT:
        phrase = REJECTION_PHRASES.get(receipt.rejection_reason, receipt.rejection_reason or "")
        text = f"{receipt.approver} rejected this at {receipt.approval_timestamp}, because {phrase}."
        if receipt.rejection_note:
            text += f' They added: "{receipt.rejection_note}"'
        sections.append(("Rejection", text))

    if receipt.evidence:
        lines = []
        for item in receipt.evidence:
            label = item.kind.replace("_", " ")
            where = f" (from {item.source_location})" if item.source_location else ""
            lines.append(f"    {label}: {item.value}{where}")
        sections.append(("Evidence", "\n".join(lines)))
    else:
        sections.append((
            "Evidence",
            "    None recorded. A receipt with no evidence is not proof of anything.",
        ))

    sections.append((
        "When",
        f"Started {receipt.timestamp_start}, finished {receipt.timestamp_end}.",
    ))
    sections.append((
        "Run by",
        f"agent {receipt.agent_version}, model {receipt.model_version}."
        + (" Executed automatically under a promoted workflow." if receipt.auto_executed else ""),
    ))
    return sections


def as_text(receipt: Receipt) -> str:
    """The whole receipt as readable text, for a terminal or a plain export."""
    out = [headline(receipt), "=" * len(headline(receipt))]
    for title, body in describe(receipt):
        out.append("")
        out.append(f"{title}:")
        for line in body.splitlines():
            out.append(f"  {line}" if not line.startswith("    ") else line)
    return "\n".join(out)
