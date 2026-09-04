"""Identifier matching (Constitution V, F-17, F-21).

Substring matching on account numbers is banned in code, not by convention.
`1234-5678` and `51234-56789` share a substring and are different accounts, and
a statement filed to the right-looking wrong client is the failure nobody
notices until an audit.

Two rules:

1. Equality is exact, once separators are normalised away. Formatting differs
   between systems; identity does not.
2. Where the task does not say which account it means and the household has
   more than one, that is an ambiguity and the agent stops. It never picks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SEPARATORS = re.compile(r"[^0-9A-Za-z]")
_RUN = re.compile(r"[0-9A-Za-z]+")

#: Separators that join two runs into one identifier. A comma, a colon or a
#: newline separates identifiers; a hyphen inside one does not.
_JOINERS = {"-", "/", ".", "_"}


def normalise_account(value: str) -> str:
    """Strip formatting, keep identity. `1234-5678` and `1234 5678` agree."""
    return _SEPARATORS.sub("", value or "").upper()


def accounts_equal(left: str, right: str) -> bool:
    """Exact equality after normalisation. Never a prefix, never a substring."""
    left_key, right_key = normalise_account(left), normalise_account(right)
    return bool(left_key) and left_key == right_key


def _has_digit(text: str) -> bool:
    return any(character.isdigit() for character in text)


def identifier_groups(text: str) -> list[str]:
    """Split text into whole identifiers.

    Runs of letters and digits are joined into one identifier when the thing
    between them is a hyphen, slash, dot or underscore -- or a single space
    where both sides contain a digit, which is how some systems print an
    account. Anything else ends the identifier.

    Only *maximal* groups come back. `1234-5678-9012` yields one identifier, not
    three, so looking for `1234-5678` in it correctly finds nothing: that text
    is about a different account.
    """
    groups: list[list[str]] = []
    current: list[str] = []
    previous_end: int | None = None

    for match in _RUN.finditer(text or ""):
        run = match.group(0)
        if current and previous_end is not None:
            separator = text[previous_end:match.start()]
            joins = separator in _JOINERS or (
                separator == " " and _has_digit(run) and _has_digit(current[-1])
            )
            if joins:
                current.append(run)
            else:
                groups.append(current)
                current = [run]
        else:
            current = [run]
        previous_end = match.end()

    if current:
        groups.append(current)
    return ["".join(group) for group in groups]


def contains_account(text: str, account: str) -> bool:
    """Is this exact account present in this text as a whole identifier?

    Used to verify a retrieved document belongs to the account that was asked
    for (Step 21).
    """
    key = normalise_account(account)
    if not key:
        return False
    return any(normalise_account(group) == key for group in identifier_groups(text))


@dataclass(frozen=True)
class Match:
    """The result of resolving which account was meant."""

    value: str | None
    candidates: tuple[str, ...] = ()
    reason: str = ""

    @property
    def found(self) -> bool:
        return self.value is not None

    @property
    def ambiguous(self) -> bool:
        return self.value is None and len(self.candidates) > 1


def find_account(wanted: str, candidates: list[str]) -> Match:
    """Find `wanted` among `candidates` by exact identity.

    Every hit is by definition the same account -- exact equality allows nothing
    else -- so several hits mean the same account written more than one way, not
    a choice to make.
    """
    hits = tuple(candidate for candidate in candidates if accounts_equal(wanted, candidate))
    if hits:
        return Match(hits[0], hits)
    return Match(None, (), f"no account matching {wanted!r}")


def resolve_sole_account(candidates: list[str]) -> Match:
    """Pick the account when the task did not name one.

    Exactly one candidate is an answer. More than one is an ambiguity, and the
    caller turns it into a stop: the agent does not guess which of a
    household's accounts a task meant.
    """
    unique: list[str] = []
    for candidate in candidates:
        if not any(accounts_equal(candidate, seen) for seen in unique):
            unique.append(candidate)
    if len(unique) == 1:
        return Match(unique[0], tuple(unique))
    if not unique:
        return Match(None, (), "the task names no account")
    return Match(None, tuple(unique),
                 f"the task names no account and {len(unique)} are linked")


class AmbiguousMatch(Exception):
    """More than one account could have been meant. The agent stops."""

    def __init__(self, candidates: tuple[str, ...]):
        self.candidates = candidates
        super().__init__(
            f"{len(candidates)} accounts could have been meant: "
            f"{', '.join(candidates)}. Confirm which one, then re-run."
        )
