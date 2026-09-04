"""Startup credential check (Step 6).

Constitution I says the application stores no credentials. This is what turns
that from a claim into something checkable: on every start, the application's
own storage is scanned for credential-shaped values, and startup fails if one
is found.

Patterns are deliberately targeted rather than entropy-based. Receipts are full
of legitimate high-entropy strings -- SHA-256 file hashes are the whole point of
the evidence layer -- so a generic "this looks random" rule would fire on the
proof layer and get switched off within a week.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("private key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("JSON web token", re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("bearer token", re.compile(r"[Bb]earer\s+[A-Za-z0-9\-._~+/]{20,}")),
    ("password assignment", re.compile(r"(?i)\bpass(?:word|wd|phrase)\b\s*[:=]\s*\S+")),
    ("api key assignment", re.compile(r"(?i)\bapi[_-]?(?:key|secret|token)\b\s*[:=]\s*\S+")),
    ("client secret", re.compile(r"(?i)\bclient[_-]secret\b\s*[:=]\s*\S+")),
    ("cookie header", re.compile(r"(?i)^\s*set-cookie\s*:", re.MULTILINE)),
    ("session cookie", re.compile(r"(?i)\b(?:session[_-]?id|sessionid|jsessionid|phpsessid|auth[_-]?token)\b\s*[:=]\s*\S+")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("MFA seed", re.compile(r"(?i)\botpauth://|(?:\btotp[_-]?secret\b\s*[:=]\s*\S+)")),
]

CREDENTIAL_FILENAMES = [
    re.compile(r"(?i)^cookies?(\.|$)"),
    re.compile(r"(?i)^\.?env$"),
    re.compile(r"(?i)^credentials?(\.|$)"),
    re.compile(r"(?i)^secrets?(\.|$)"),
    re.compile(r"(?i)^id_(?:rsa|dsa|ecdsa|ed25519)"),
    re.compile(r"(?i)\.(?:pem|pfx|p12|keychain|jks)$"),
    re.compile(r"(?i)^token(s)?(\.|$)"),
    re.compile(r"(?i)^\.netrc$"),
    re.compile(r"(?i)^\.htpasswd$"),
]

#: Only text-ish files are opened. A retrieved client statement is not scanned
#: for secrets; it is client data, and its handling is Constitution IV's problem.
SCANNED_SUFFIXES = {
    "", ".json", ".jsonl", ".txt", ".log", ".yaml", ".yml", ".ini", ".cfg",
    ".conf", ".toml", ".csv", ".db", ".sqlite", ".sqlite3", ".html", ".xml",
}

MAX_SCAN_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class Finding:
    path: Path
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.kind} ({self.detail})"


class CredentialFound(RuntimeError):
    """Startup refuses to continue while a credential-shaped value is stored."""

    def __init__(self, findings: list[Finding]):
        self.findings = findings
        listed = "\n  - ".join(str(f) for f in findings)
        super().__init__(
            "startup refused: the application's storage holds credential-shaped "
            "values, and Constitution I says it never does.\n  - " + listed
            + "\n\nRemove them. The agent works inside sessions you have already "
              "authenticated; it never needs a stored secret."
        )


def scan(storage_dir: str | Path) -> list[Finding]:
    """Return every credential-shaped thing found in the application's storage."""
    root = Path(storage_dir)
    findings: list[Finding] = []
    if not root.exists():
        return findings

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        for pattern in CREDENTIAL_FILENAMES:
            if pattern.search(path.name):
                findings.append(Finding(path, "credential-shaped filename", path.name))
                break

        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if path.stat().st_size > MAX_SCAN_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in CREDENTIAL_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                findings.append(Finding(path, label, f"line {line}"))
    return findings


def assert_clean(storage_dir: str | Path) -> None:
    """Raise unless the application's storage holds no credential-shaped value."""
    findings = scan(storage_dir)
    if findings:
        raise CredentialFound(findings)
