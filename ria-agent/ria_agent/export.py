"""Log exporters (Step 5).

If a CCO or an examiner asks what the agent did on 3 March, the answer is one
command away. The PDF is written for someone who has never seen this system and
has no interest in learning it.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from .log_store import LogStore
from .pdf import PdfDocument
from .plain import describe, headline, lane_name
from .receipts import (
    PENDING_APPROVAL, Receipt, STOPPED_CLEANUP_REQUIRED, STOPPED_NO_CHANGE, VERIFIED,
)

LANE_ORDER = (STOPPED_CLEANUP_REQUIRED, PENDING_APPROVAL, STOPPED_NO_CHANGE, VERIFIED)

CSV_COLUMNS = [
    "receipt_id", "timestamp_start", "timestamp_end", "human_owner", "role",
    "crm_task_id", "workflow_id", "step_id", "system_touched", "action_type",
    "target_identifier", "outcome", "stop_reason", "stop_next_step",
    "cleanup_instruction", "references_receipt_id", "approver",
    "approval_timestamp", "rejection_reason", "rejection_note", "confidence",
    "auto_executed", "before_state", "after_state", "evidence_count",
    "evidence", "model_version", "agent_version",
]


def _evidence_cell(receipt: Receipt) -> str:
    parts = []
    for item in receipt.evidence:
        where = f" @ {item.source_location}" if item.source_location else ""
        parts.append(f"{item.kind}={item.value}{where}")
    return " | ".join(parts)


def _row(receipt: Receipt) -> dict:
    data = receipt.to_dict()
    data["evidence_count"] = len(receipt.evidence)
    data["evidence"] = _evidence_cell(receipt)
    data["before_state"] = "" if receipt.before_state is None else str(receipt.before_state)
    data["after_state"] = "" if receipt.after_state is None else str(receipt.after_state)
    return {column: data.get(column, "") for column in CSV_COLUMNS}


def describe_filters(filters: dict) -> str:
    labels = {
        "human_owner": "person", "workflow_id": "workflow", "outcome": "outcome",
        "crm_task_id": "task", "action_type": "action", "since": "from", "until": "to",
    }
    active = [
        f"{labels.get(key, key)} = {value}"
        for key, value in sorted(filters.items())
        if value is not None
    ]
    return ", ".join(active) if active else "everything in the log, unfiltered"


def export_csv(store: LogStore, path: str | Path, **filters) -> Path:
    """One row per receipt, every field, for a spreadsheet or an examiner."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    receipts = store.query(**filters)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for receipt in receipts:
            writer.writerow(_row(receipt))
    return path


def export_pdf(
    store: LogStore,
    path: str | Path,
    *,
    title: str = "Agent activity log",
    firm: str = "",
    **filters,
) -> Path:
    """A readable account of what happened, in order, with the evidence."""
    path = Path(path)
    receipts = store.query(**filters)

    doc = PdfDocument(footer=f"{firm} {title}".strip() or title)
    doc.heading(title, size=19)
    if firm:
        doc.text(firm, size=11, bold=True, space_after=2)
    doc.text(f"Covering: {describe_filters(filters)}", size=10)
    doc.text(f"{len(receipts)} action(s) recorded.", size=10)
    doc.rule()

    doc.heading("Summary", size=13)
    by_lane = Counter(r.outcome for r in receipts)
    for lane in LANE_ORDER:
        if by_lane.get(lane):
            doc.text(f"{by_lane[lane]}  —  {lane_name(lane)}", size=10, indent=10, space_after=1)
    for lane, count in sorted(by_lane.items()):
        if lane not in LANE_ORDER:
            doc.text(f"{count}  —  {lane_name(lane)}", size=10, indent=10, space_after=1)
    doc.spacer(4)

    stops = Counter(r.stop_reason for r in receipts if r.stop_reason)
    if stops:
        doc.text("Why the agent stopped:", size=10, bold=True, space_after=2)
        for reason, count in stops.most_common():
            doc.text(
                f"{count}  —  {reason.replace('_', ' ')}",
                size=10, indent=10, space_after=1,
            )
        doc.spacer(4)

    unapproved = [
        r for r in receipts
        if r.action_type == "write" and not r.auto_executed and not r.references_receipt_id
    ]
    doc.text(
        "Unapproved writes: 0. Every write in this period was either approved "
        "by a named person or executed under a promoted workflow."
        if not unapproved else
        f"UNAPPROVED WRITES: {len(unapproved)}. This must be investigated.",
        size=10, bold=bool(unapproved),
    )
    doc.rule()

    doc.heading("Every action, in order", size=13)
    if not receipts:
        doc.text("Nothing was recorded in this period.", size=10)

    for number, receipt in enumerate(receipts, start=1):
        doc.spacer(4)
        doc.text(f"{number}. {headline(receipt)}", size=11, bold=True, space_after=3)
        doc.text(f"Receipt {receipt.receipt_id}", size=8, space_after=4)
        for section_title, body in describe(receipt):
            doc.text(f"{section_title}:", size=9.5, bold=True, indent=10, space_after=1)
            for line in body.splitlines():
                doc.text(line.strip(), size=9.5, indent=22, space_after=1)
            doc.spacer(2)
        doc.rule(space_after=4)

    return doc.save(path)
