"""The firm's naming convention, as an explicit rule set (Step 25).

Do not automate an ambiguous standard. If the firm names documents three
different ways today, the agent will apply one of them at machine speed and
corrupt the library faster than a person ever could (F-23).

So the convention is written down here as rules, and `dry_run` replays them over
documents the firm has already filed. Where the rules and history disagree, that
is the finding: either the rule is wrong or the human convention is, and someone
has to decide which before a single live filing happens.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass(frozen=True)
class Document:
    """What is known about a document at filing time."""

    household: str
    account: str
    period: str
    doc_type: str = "Statement"
    custodian: str = ""
    source_filename: str = ""

    @property
    def year(self) -> str:
        return self.period[:4] if self.period else ""


@dataclass(frozen=True)
class Convention:
    """One firm's rules. Configured per install, never guessed."""

    filename: str = "{period} {custodian} {doc_type} - {household} {account}.pdf"
    folder: str = "{household} / {doc_type}s / {year}"
    tags: tuple[str, ...] = ("{doc_type_lower}", "custodian")
    title_case_custodian: bool = True

    def render(self, document: Document) -> dict:
        values = {
            "period": document.period,
            "year": document.year,
            "household": document.household,
            "account": document.account,
            "doc_type": document.doc_type,
            "doc_type_lower": document.doc_type.lower(),
            "custodian": (document.custodian.title() if self.title_case_custodian
                          else document.custodian),
        }
        missing = [
            name for name in re.findall(r"{(\w+)}", self.filename + self.folder)
            if not values.get(name)
        ]
        if missing:
            raise IncompleteDocument(missing)
        return {
            "filename": _clean(self.filename.format(**values)),
            "folder": self.folder.format(**values),
            "linked_account": document.account,
            "tags": ", ".join(tag.format(**values) for tag in self.tags),
        }

    @classmethod
    def load(cls, path: str | Path) -> "Convention":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["tags"] = tuple(data.get("tags", ()))
        return cls(**data)

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"filename": self.filename, "folder": self.folder,
                   "tags": list(self.tags),
                   "title_case_custodian": self.title_case_custodian}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path


def _clean(name: str) -> str:
    return INVALID.sub("-", name).strip()


class IncompleteDocument(ValueError):
    """A name cannot be built from values that are not there. It is not guessed."""

    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(
            f"cannot name this document: no {', '.join(missing)}. "
            "The agent does not invent the missing part."
        )


# --- Step 25's gate --------------------------------------------------------


@dataclass
class Disagreement:
    document: Document
    filed_as: str
    rule_says: str


@dataclass
class DryRun:
    """What the rules would have done to documents already filed."""

    agreed: int = 0
    disagreements: list[Disagreement] = field(default_factory=list)
    unnameable: list[tuple[Document, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.agreed + len(self.disagreements) + len(self.unnameable)

    @property
    def agreement_rate(self) -> float | None:
        return self.agreed / self.total if self.total else None

    def passes(self, threshold: float = 0.95) -> bool:
        rate = self.agreement_rate
        return rate is not None and rate >= threshold

    def summary(self, threshold: float = 0.95) -> str:
        if not self.total:
            return "No history to replay. The convention has not been tested."
        lines = [
            f"Replayed {self.total} documents the firm already filed.",
            f"  the rules agree with history   {self.agreed} ({self.agreement_rate:.0%})",
            f"  the rules would rename         {len(self.disagreements)}",
            f"  the rules cannot name at all   {len(self.unnameable)}",
        ]
        if self.passes(threshold):
            lines.append("\nThe convention is consistent enough to automate.")
        else:
            lines.append(
                f"\nBelow {threshold:.0%}. Fix the human convention before automating it — "
                "the disagreements below are either a wrong rule or a wrong habit, "
                "and someone has to say which."
            )
        for item in self.disagreements[:15]:
            lines.append(f"  filed as   {item.filed_as}")
            lines.append(f"  rules say  {item.rule_says}")
        if len(self.disagreements) > 15:
            lines.append(f"  ... and {len(self.disagreements) - 15} more")
        return "\n".join(lines)


def dry_run(convention: Convention, history: list[tuple[Document, str]]) -> DryRun:
    """Replay the rules over documents already filed, before any live filing."""
    result = DryRun()
    for document, filed_as in history:
        try:
            proposed = convention.render(document)["filename"]
        except IncompleteDocument as failure:
            result.unnameable.append((document, str(failure)))
            continue
        if proposed == filed_as:
            result.agreed += 1
        else:
            result.disagreements.append(Disagreement(document, filed_as, proposed))
    return result
