"""A very small PDF writer (supports Step 5).

The exporter has to hand a human a readable PDF. Pulling in a reporting library
for that would put a compiled dependency into an install that has to work on a
staff laptop with no build tooling (F-40), so this writes the PDF directly.

Text only, base-14 fonts, WinAnsi encoding, automatic wrapping and pagination.
That is all a receipt log needs.
"""

from __future__ import annotations

import re
import zlib
from pathlib import Path

LETTER = (612.0, 792.0)

_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
_SHOWN = re.compile(rb"\((?:[^()\\]|\\.)*\)\s*Tj")


def extract_text(data: bytes) -> str:
    """Pull the visible text out of a PDF.

    Handles the plain and Flate-compressed content streams that ordinary
    generators produce, which is enough to verify a retrieved statement in the
    tests and against the fake portal.

    It is NOT a general PDF text extractor. A scanned statement is an image and
    yields nothing here, and a custodian using an unusual encoding may too --
    which is the right failure: verification finds no account number, the check
    fails, and the artifact is stopped rather than accepted. Production needs a
    real extractor behind this name, and it must fail the same way.
    """
    pieces: list[str] = []
    for raw in _STREAM.findall(data):
        try:
            body = zlib.decompress(raw)
        except zlib.error:
            body = raw
        for token in _SHOWN.findall(body):
            literal = token[token.index(b"(") + 1:token.rindex(b")")]
            pieces.append(_unescape(literal))
    return "\n".join(pieces)


def _unescape(raw: bytes) -> str:
    out = bytearray()
    index = 0
    while index < len(raw):
        byte = raw[index]
        if byte == 0x5C and index + 1 < len(raw):
            index += 1
            nxt = raw[index]
            out.append({0x6E: 0x0A, 0x72: 0x0D, 0x74: 0x09}.get(nxt, nxt))
        else:
            out.append(byte)
        index += 1
    return bytes(out).decode("cp1252", errors="replace")

# Helvetica advance widths (1/1000 em) for printable ASCII, from the base-14
# metrics. Needed so wrapping breaks lines where they actually fit.
_W = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584,
    "?": 556, "@": 1015, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "`": 333, "{": 334, "|": 260, "}": 334, "~": 584,
}
_W.update({c: 556 for c in "0123456789"})
_W.update(dict(zip(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    [667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833,
     722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611],
)))
_W.update(dict(zip(
    "abcdefghijklmnopqrstuvwxyz",
    [556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833,
     556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500],
)))
_DEFAULT_WIDTH = 556
_BOLD_FACTOR = 1.08  # bold runs wider; keep wrapping conservative


def text_width(text: str, size: float, bold: bool = False) -> float:
    total = sum(_W.get(ch, _DEFAULT_WIDTH) for ch in text)
    width = total * size / 1000.0
    return width * _BOLD_FACTOR if bold else width


def wrap(text: str, size: float, max_width: float, bold: bool = False) -> list[str]:
    """Greedy wrap on spaces, splitting any single word too long to fit."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if current and text_width(candidate, size, bold) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
            while text_width(current, size, bold) > max_width and len(current) > 1:
                cut = len(current)
                while cut > 1 and text_width(current[:cut], size, bold) > max_width:
                    cut -= 1
                lines.append(current[:cut])
                current = current[cut:]
        if current:
            lines.append(current)
    return lines


def _escape(text: str) -> bytes:
    raw = text.encode("cp1252", errors="replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class PdfDocument:
    """Append content top to bottom; pages break themselves."""

    def __init__(self, page_size=LETTER, margin: float = 54.0, footer: str = ""):
        self.width, self.height = page_size
        self.margin = margin
        self.footer = footer
        self._pages: list[list[bytes]] = []
        self._ops: list[bytes] = []
        self._y = self.height - margin
        self._pages.append(self._ops)

    @property
    def _text_width(self) -> float:
        return self.width - 2 * self.margin

    def _new_page(self) -> None:
        self._ops = []
        self._pages.append(self._ops)
        self._y = self.height - self.margin

    def _need(self, height: float) -> None:
        if self._y - height < self.margin + 24:
            self._new_page()

    def _draw(self, text: str, size: float, bold: bool, indent: float) -> None:
        font = b"/F2" if bold else b"/F1"
        self._ops.append(
            b"BT " + font + b" %.1f Tf 1 0 0 1 %.2f %.2f Tm (" % (size, self.margin + indent, self._y)
            + _escape(text) + b") Tj ET"
        )

    def text(
        self, body: str, size: float = 10.0, bold: bool = False,
        indent: float = 0.0, leading: float = 1.35, space_after: float = 4.0,
    ) -> None:
        line_height = size * leading
        for line in wrap(body, size, self._text_width - indent, bold):
            self._need(line_height)
            self._y -= line_height
            if line:
                self._draw(line, size, bold, indent)
        self._y -= space_after

    def heading(self, body: str, size: float = 15.0) -> None:
        self._need(size * 2.2)
        self._y -= 6
        self.text(body, size=size, bold=True, space_after=6.0)

    def rule(self, space_after: float = 8.0) -> None:
        self._need(6)
        self._y -= 3
        self._ops.append(
            b"0.75 w 0.6 0.6 0.6 RG %.2f %.2f m %.2f %.2f l S 0 0 0 RG"
            % (self.margin, self._y, self.width - self.margin, self._y)
        )
        self._y -= space_after

    def spacer(self, height: float = 8.0) -> None:
        self._need(height)
        self._y -= height

    def page_break(self) -> None:
        self._new_page()

    # -- assembly ----------------------------------------------------------

    def _page_content(self, index: int) -> bytes:
        ops = list(self._pages[index])
        if self.footer:
            label = f"{self.footer}   ·   page {index + 1} of {len(self._pages)}"
            ops.append(
                b"BT /F1 8.0 Tf 0.45 0.45 0.45 rg 1 0 0 1 %.2f %.2f Tm ("
                % (self.margin, self.margin * 0.7)
                + _escape(label) + b") Tj ET 0 0 0 rg"
            )
        return b"\n".join(ops)

    def to_bytes(self) -> bytes:
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        page_count = len(self._pages)
        first_page_obj = 5
        page_ids = [first_page_obj + 2 * i for i in range(page_count)]

        kids = b" ".join(b"%d 0 R" % pid for pid in page_ids)
        add(b"<< /Type /Catalog /Pages 2 0 R >>")
        add(b"<< /Type /Pages /Count %d /Kids [%s] >>" % (page_count, kids))
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

        for index in range(page_count):
            content = self._page_content(index)
            add(
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
                b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>"
                % (self.width, self.height, page_ids[index] + 1)
            )
            add(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n" % number + body + b"\nendobj\n"

        xref_at = len(out)
        out += b"xref\n0 %d\n" % (len(objects) + 1)
        out += b"0000000000 65535 f \n"
        for offset in offsets[1:]:
            out += b"%010d 00000 n \n" % offset
        out += (
            b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, xref_at)
        )
        return bytes(out)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.to_bytes())
        return path
