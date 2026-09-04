"""The review queue on localhost (Steps 7-10).

Boring on purpose. Step 11's bar is that someone who has never seen this
understands it without being told anything, so there is no dashboard, no chart,
and nothing to learn.

Bound to the loopback interface only. This is one person's queue on one person's
machine, and it is never served to a network.
"""

from __future__ import annotations

import html
import secrets
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .export import export_csv, export_pdf
from .plain import LANE_BLURBS, describe, lane_name
from .queue import LANE_ORDER, Queue, QueueError, QueueItem
from .receipts import (
    PENDING_APPROVAL, REJECTION_REASONS, SCREENSHOT, STOPPED_CLEANUP_REQUIRED, VERIFIED,
)

REJECTION_LABELS = {
    "wrong_target": "Wrong client or account",
    "wrong_document": "Wrong document",
    "wrong_naming": "Wrong name or location",
    "bad_extraction": "A value was read wrong",
    "not_needed": "Did not need doing",
    "already_done": "Already done",
    "against_policy": "Against firm policy",
    "other": "Something else",
}

LANE_TONE = {
    STOPPED_CLEANUP_REQUIRED: "urgent",
    PENDING_APPROVAL: "waiting",
    VERIFIED: "done",
}

STYLE = """
*, *::before, *::after { box-sizing: border-box; }
body { margin:0; background:#f5f6f8; color:#1d2733;
       font:15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
a { color:#1b4f8f; }
header { background:#1d2733; color:#fff; padding:16px 28px; }
header h1 { margin:0; font-size:17px; font-weight:600; }
header .who { color:#a9b4c2; font-size:13px; margin-top:3px; }
header a { color:#c8d6e8; margin-right:14px; font-size:13px; }
main { max-width:960px; margin:0 auto; padding:24px 28px 64px; }
.lane { margin-bottom:34px; }
.lane h2 { font-size:15px; margin:0 0 2px; display:flex; align-items:center; gap:9px; }
.lane .blurb { color:#69737f; font-size:13px; margin:0 0 12px; }
.count { background:#dde2e9; color:#3c4653; border-radius:11px;
         padding:1px 9px; font-size:12.5px; font-weight:600; }
.urgent .count { background:#c0392b; color:#fff; }
.waiting .count { background:#b8791b; color:#fff; }
.done .count { background:#3f7d4f; color:#fff; }
.item { background:#fff; border:1px solid #e0e5eb; border-left:4px solid #c8ced6;
        border-radius:5px; padding:12px 15px; margin-bottom:8px; }
.urgent .item { border-left-color:#c0392b; }
.waiting .item { border-left-color:#b8791b; }
.done .item { border-left-color:#3f7d4f; }
.item a.title { font-weight:600; text-decoration:none; }
.item .meta { color:#69737f; font-size:12.5px; margin-top:3px; }
.empty { color:#8a939d; font-size:13.5px; font-style:italic; }
.capped { background:#fdf6e6; border:1px solid #e8d9ae; border-radius:5px;
          padding:10px 13px; font-size:13px; color:#6b5514; margin-top:8px; }
.card { background:#fff; border:1px solid #e0e5eb; border-radius:6px;
        padding:22px 26px; margin-bottom:18px; }
.card h3 { font-size:12px; text-transform:uppercase; letter-spacing:.06em;
           color:#69737f; margin:22px 0 6px; }
.card h3:first-child { margin-top:0; }
.card p { margin:0 0 4px; }
table { border-collapse:collapse; width:100%; font-size:13.5px; margin-top:4px; }
th, td { text-align:left; padding:7px 10px; border-bottom:1px solid #eceff3;
         vertical-align:top; }
th { color:#69737f; font-weight:600; font-size:12px; text-transform:uppercase;
     letter-spacing:.04em; }
td.was { color:#8a939d; }
td.now { font-weight:600; }
tr.changed td.now { background:#eef7f0; }
code, .mono { font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
              font-size:12.5px; }
img.shot { max-width:100%; border:1px solid #dde2e9; border-radius:4px; margin-top:6px; }
form.decide { display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end; margin-top:6px; }
label { display:block; font-size:12px; color:#69737f; margin-bottom:3px; }
select, input[type=text] { font:inherit; padding:7px 9px; border:1px solid #c8ced6;
                           border-radius:4px; background:#fff; }
input[type=text] { min-width:290px; }
button { font:inherit; font-weight:600; padding:8px 18px; border-radius:4px;
         border:1px solid transparent; cursor:pointer; }
button.approve { background:#2f6b40; color:#fff; }
button.reject  { background:#fff; color:#a5321f; border-color:#d9b0a8; }
.banner { border-radius:5px; padding:12px 15px; margin-bottom:18px; font-size:14px; }
.banner.ok { background:#eef7f0; border:1px solid #bfdcc7; color:#25532f; }
.banner.no { background:#fdeeeb; border:1px solid #eec4bb; color:#8c2c1a; }
.banner.seed { background:#eef2fb; border:1px solid #c2cfe8; color:#2a3f66; }
.decided { color:#69737f; font-size:13.5px; }
.cleanup { background:#fdeeeb; border:1px solid #eec4bb; border-radius:5px;
           padding:12px 15px; color:#8c2c1a; }
footer { color:#8a939d; font-size:12px; margin-top:40px; }
"""


def esc(text) -> str:
    return html.escape(str(text), quote=True)


class QueueServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, *, queue: Queue, app, csrf_token: str):
        super().__init__(address, handler)
        self.queue = queue
        self.app = app
        self.csrf_token = csrf_token


class QueueHandler(BaseHTTPRequestHandler):
    server_version = "ria-agent-queue"

    # -- plumbing ----------------------------------------------------------

    def log_message(self, fmt, *args):  # quieter than the default
        pass

    @property
    def queue(self) -> Queue:
        return self.server.queue

    def _send(self, body: bytes, status=HTTPStatus.OK, content_type="text/html; charset=utf-8",
              extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _page(self, title: str, body: str, status=HTTPStatus.OK) -> None:
        app = self.server.app
        document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>{STYLE}</style></head><body>
<header>
  <h1>Agent review queue</h1>
  <div class="who">{esc(app.operator)} · {esc(app.role.replace('_', ' '))}
     · agent {esc(app.agent_version)} · model {esc(app.model_version)}</div>
  <div style="margin-top:8px"><a href="/">Queue</a><a href="/export.csv">Export CSV</a>
     <a href="/export.pdf">Export PDF</a></div>
</header>
<main>{body}
<footer>Everything here is a record in an append-only log. Approving or
rejecting writes another record naming you and the time.</footer>
</main></body></html>"""
        self._send(document.encode("utf-8"), status=status)

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- routing -----------------------------------------------------------

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        if path == "/":
            return self._render_queue(params)
        if path.startswith("/item/"):
            return self._render_item(path[len("/item/"):], params)
        if path.startswith("/evidence/"):
            return self._serve_evidence(path[len("/evidence/"):])
        if path in ("/export.csv", "/export.pdf"):
            return self._serve_export(path)
        self._page("Not found", "<div class='card'><p>No such page.</p></div>",
                   status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if not parsed.path.startswith("/item/"):
            return self._page("Not found", "<div class='card'><p>No such page.</p></div>",
                              status=HTTPStatus.NOT_FOUND)

        # A page in any other tab can POST to localhost. The queue approves
        # changes to client records, so a decision has to prove it came from
        # this UI.
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
            return self._page("Refused", "<div class='banner no'>Cross-origin request refused.</div>",
                              status=HTTPStatus.FORBIDDEN)

        length = int(self.headers.get("Content-Length") or 0)
        fields = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
        if fields.get("token", [""])[0] != self.server.csrf_token:
            return self._page(
                "Refused",
                "<div class='banner no'>This form was not submitted from the "
                "queue. Reload the page and try again.</div>",
                status=HTTPStatus.FORBIDDEN)

        _, _, tail = parsed.path.partition("/item/")
        receipt_id, _, action = tail.partition("/")
        approver = self.server.app.operator
        try:
            if action == "approve":
                self.queue.approve(receipt_id, approver, fields.get("note", [""])[0])
                flag = "approved"
            elif action == "reject":
                self.queue.reject(
                    receipt_id, approver,
                    reason=fields.get("reason", [""])[0],
                    note=fields.get("note", [""])[0],
                )
                flag = "rejected"
            else:
                return self._page("Not found", "<div class='card'><p>No such action.</p></div>",
                                  status=HTTPStatus.NOT_FOUND)
        except (QueueError, LookupError, ValueError) as exc:
            return self._render_item(receipt_id, {}, error=str(exc))
        self._redirect(f"/item/{urllib.parse.quote(receipt_id)}?decided={flag}")

    # -- views -------------------------------------------------------------

    def _render_queue(self, params: dict) -> None:
        person = params.get("person", [None])[0]
        lanes = self.queue.lanes(**({"human_owner": person} if person else {}))
        blocks = []
        for lane in lanes:
            tone = LANE_TONE.get(lane.key, "")
            rows = "".join(self._row(item) for item in lane.items)
            if not lane.items:
                rows = "<p class='empty'>Nothing here.</p>"
            capped = ""
            if lane.hidden_count and lane.key == PENDING_APPROVAL:
                capped = (
                    f"<div class='capped'>{lane.hidden_count} more waiting, not shown. "
                    "The approval lane is capped so it stays reviewable — a queue "
                    "nobody can get to the bottom of gets approved without reading. "
                    "Clear these first.</div>"
                )
            elif lane.hidden_count:
                capped = (
                    f"<div class='capped'>{lane.hidden_count} more, not shown. "
                    "These needed nothing from you. The full record is in the "
                    "<a href='/export.pdf'>export</a>.</div>"
                )
            blocks.append(
                f"<section class='lane {tone}'>"
                f"<h2>{esc(lane.name)} <span class='count'>{len(lane)}</span></h2>"
                f"<p class='blurb'>{esc(lane.blurb)}</p>{rows}{capped}</section>"
            )
        self._page("Agent review queue", "".join(blocks))

    def _row(self, item: QueueItem) -> str:
        receipt = item.receipt
        bits = [f"task {esc(receipt.crm_task_id)}", esc(receipt.human_owner),
                esc(receipt.timestamp_start.replace("T", " ")[:16])]
        if receipt.stop_reason:
            bits.insert(0, esc(receipt.stop_reason.replace("_", " ")))
        changes = ""
        if item.lane == PENDING_APPROVAL and item.diff:
            changed = [field for field, was, now in item.diff if was != now]
            changes = f"<div class='meta'>Changes: {esc(', '.join(changed))}</div>"
        return (
            f"<div class='item'>"
            f"<a class='title' href='/item/{esc(receipt.receipt_id)}'>{esc(item.headline)}</a>"
            f"<div class='meta'>{' · '.join(bits)}</div>{changes}</div>"
        )

    def _render_item(self, receipt_id: str, params: dict, error: str = "") -> None:
        item = self.queue.item(urllib.parse.unquote(receipt_id))
        if item is None:
            return self._page("Not found", "<div class='card'><p>No such receipt.</p></div>",
                              status=HTTPStatus.NOT_FOUND)

        parts = []
        if error:
            parts.append(f"<div class='banner no'>{esc(error)}</div>")
        decided = params.get("decided", [None])[0]
        if decided:
            parts.append(
                f"<div class='banner ok'>Recorded: you {esc(decided)} this, and that "
                "decision is now its own entry in the log.</div>")
            parts.append(self._seed_reveal(item, decided))

        parts.append(self._detail_card(item))
        if item.receipt.outcome == STOPPED_CLEANUP_REQUIRED:
            parts.append(
                f"<div class='card'><h3>This one needs you</h3>"
                f"<div class='cleanup'>{esc(item.receipt.cleanup_instruction)}</div></div>")
        if item.is_open:
            parts.append(self._decision_form(item))
        elif item.decision is not None:
            decision = item.decision
            reason = ""
            if decision.rejection_reason:
                reason = f" — {esc(REJECTION_LABELS.get(decision.rejection_reason, decision.rejection_reason))}"
            note = f"<br>“{esc(decision.rejection_note)}”" if decision.rejection_note else ""
            parts.append(
                f"<div class='card'><h3>Decision</h3><p class='decided'>"
                f"{esc(decision.approver)} {esc(item.decision_word)} this at "
                f"{esc(decision.approval_timestamp)}{reason}{note}</p></div>")

        self._page(item.headline, "".join(parts))

    def _seed_reveal(self, item: QueueItem, decided: str) -> str:
        """Tell the reviewer straight away when an item was a seeded check."""
        if not (item.seeded and self.queue.seeds):
            return ""
        record = self.queue.seeds.get(item.receipt_id)
        if not record:
            return ""
        caught = decided == "rejected"
        verdict = (
            "You caught it." if caught else
            "This one got through. That is the point of the check, and it is "
            "worth a minute working out what made it look right."
        )
        return (
            f"<div class='banner seed'><strong>This was a seeded check.</strong> "
            f"It was deliberately wrong: {esc(record['description'])}. {verdict} "
            f"Nothing was applied to any real record either way.</div>"
        )

    def _detail_card(self, item: QueueItem) -> str:
        receipt = item.receipt
        blocks = [f"<div class='card'>"]
        # The diff and the evidence are what the decision turns on, so they sit
        # above the run metadata rather than below it.
        trailing = []
        for title, body in describe(receipt):
            if title in ("Evidence", "What changes"):
                continue
            target = trailing if title in ("When", "Run by") else blocks
            target.append(f"<h3>{esc(title)}</h3><p>{esc(body)}</p>")

        if item.diff:
            blocks.append("<h3>What changes</h3>")
            blocks.append(
                "<table><tr><th>Field</th><th>Now</th><th>Proposed</th></tr>")
            for field, was, now in item.diff:
                cls = " class='changed'" if was != now else ""
                blocks.append(
                    f"<tr{cls}><td>{esc(field)}</td><td class='was'>{esc(was)}</td>"
                    f"<td class='now'>{esc(now)}</td></tr>")
            blocks.append("</table>")

        blocks.append("<h3>Evidence</h3>")
        if not receipt.evidence:
            blocks.append("<p class='empty'>None recorded. This is not proof of anything.</p>")
        else:
            blocks.append("<table><tr><th>Kind</th><th>Value</th><th>Where it came from</th></tr>")
            shots = []
            for piece in receipt.evidence:
                if piece.kind == SCREENSHOT:
                    shots.append(str(piece.value))
                blocks.append(
                    f"<tr><td>{esc(piece.kind.replace('_', ' '))}</td>"
                    f"<td class='mono'>{esc(piece.value)}</td>"
                    f"<td class='mono'>{esc(piece.source_location or '—')}</td></tr>")
            blocks.append("</table>")
            for shot in shots:
                blocks.append(
                    f"<img class='shot' alt='screenshot evidence' "
                    f"src='/evidence/{urllib.parse.quote(shot)}'>")

        blocks.extend(trailing)
        blocks.append(f"<h3>Receipt</h3><p class='mono'>{esc(receipt.receipt_id)}</p></div>")
        return "".join(blocks)

    def _decision_form(self, item: QueueItem) -> str:
        token = esc(self.server.csrf_token)
        options = "".join(
            f"<option value='{esc(key)}'>{esc(REJECTION_LABELS[key])}</option>"
            for key in sorted(REJECTION_REASONS, key=lambda k: REJECTION_LABELS[k])
        )
        return f"""<div class='card'>
<h3>Your decision</h3>
<p>Nothing above has been applied. It takes effect only if you approve it.</p>
<form class='decide' method='post' action='/item/{esc(item.receipt_id)}/approve'>
  <input type='hidden' name='token' value='{token}'>
  <button class='approve' type='submit'>Approve</button>
</form>
<h3>Or reject it</h3>
<form class='decide' method='post' action='/item/{esc(item.receipt_id)}/reject'>
  <input type='hidden' name='token' value='{token}'>
  <div><label for='reason'>What was wrong</label>
    <select id='reason' name='reason' required>{options}</select></div>
  <div><label for='note'>Anything else (optional)</label>
    <input id='note' type='text' name='note' maxlength='500'></div>
  <button class='reject' type='submit'>Reject</button>
</form>
<p class='empty'>A reason is required. It is how the agent learns what it got wrong.</p>
</div>"""

    def _serve_evidence(self, name: str) -> None:
        root = Path(self.server.app.evidence_dir).resolve()
        candidate = (root / urllib.parse.unquote(name)).resolve()
        if not candidate.is_file() or root not in candidate.parents:
            return self._send(b"not found", status=HTTPStatus.NOT_FOUND,
                              content_type="text/plain; charset=utf-8")
        kinds = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".svg": "image/svg+xml", ".webp": "image/webp", ".gif": "image/gif"}
        kind = kinds.get(candidate.suffix.lower())
        if kind is None:
            return self._send(b"unsupported evidence type", status=HTTPStatus.FORBIDDEN,
                              content_type="text/plain; charset=utf-8")
        self._send(candidate.read_bytes(), content_type=kind)

    def _serve_export(self, path: str) -> None:
        app = self.server.app
        out = Path(app.storage_dir) / "exports"
        if path.endswith(".csv"):
            written = export_csv(self.queue.store, out / "activity.csv")
            kind, name = "text/csv; charset=utf-8", "agent-activity.csv"
        else:
            written = export_pdf(self.queue.store, out / "activity.pdf",
                                 title="Agent activity log", firm="")
            kind, name = "application/pdf", "agent-activity.pdf"
        self._send(written.read_bytes(), content_type=kind,
                   extra={"Content-Disposition": f'attachment; filename="{name}"'})


def build_server(app, queue: Queue, host: str = "127.0.0.1", port: int = 8765) -> QueueServer:
    """Loopback only. This queue is never exposed to a network."""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError(
            f"refusing to bind the review queue to {host!r}. It is one person's "
            "queue on one person's machine and is served to loopback only."
        )
    return QueueServer((host, port), QueueHandler, queue=queue, app=app,
                       csrf_token=secrets.token_urlsafe(24))
