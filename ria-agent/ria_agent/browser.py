"""The browser, as an interface (Step 19).

The agent works inside a session a human has already authenticated, so the real
driver is a thin wrapper over an automation library pointed at the operator's
own browser profile. It is not here yet, and nothing above this interface knows
that.

What is here is a fake custodian portal that behaves badly on purpose: promo
modals, a transfer button on the dashboard, an account that looks like the one
being asked for, a session that dies partway, and a redesign that renames every
control. Guardrails that are never driven into a wall have not been tested.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

LINK = "link"
BUTTON = "button"
INPUT = "input"
DOWNLOAD = "download"

CLICK = "click"
TYPE = "type"
DOWNLOAD_ACTION = "download"


@dataclass(frozen=True)
class Element:
    element_id: str
    kind: str
    label: str
    href: str = ""


@dataclass(frozen=True)
class Action:
    kind: str
    element_id: str
    value: str = ""

    def __str__(self) -> str:
        return f"{self.kind} {self.element_id}" + (f" = {self.value!r}" if self.value else "")


@dataclass(frozen=True)
class PageObservation:
    """What the agent can see right now."""

    url: str
    title: str
    text: str = ""
    elements: tuple[Element, ...] = ()
    is_modal: bool = False
    authenticated: bool = True

    def element(self, element_id: str) -> Element | None:
        return next((e for e in self.elements if e.element_id == element_id), None)

    def labelled(self, *fragments: str) -> list[Element]:
        wanted = [f.lower() for f in fragments]
        return [
            e for e in self.elements
            if all(word in e.label.lower() for word in wanted)
        ]

    @property
    def signature(self) -> str:
        """A stable fingerprint of the page's shape, for drift detection."""
        shape = "|".join(sorted(f"{e.kind}:{e.label}" for e in self.elements))
        return hashlib.sha256(f"{self.title}::{shape}".encode()).hexdigest()[:16]


class SessionLost(Exception):
    """The authenticated session ended. The agent stops; it never logs back in."""


class MfaChallenge(Exception):
    """An MFA challenge appeared. Zero retries, always (Constitution I)."""


class BrowserDriver(ABC):
    """Drives a browser inside a session the human already authenticated."""

    @abstractmethod
    def observe(self) -> PageObservation:
        """What is on screen now."""

    @abstractmethod
    def act(self, action: Action) -> PageObservation:
        """Perform one action and return what is on screen after it."""

    @abstractmethod
    def download(self, element_id: str, destination: Path) -> Path:
        """Save the artifact behind an element."""

    @abstractmethod
    def screenshot(self, destination: Path) -> Path:
        """Capture the current view."""

    def home(self) -> PageObservation:
        """Return to the portal's entry point.

        A browser keeps its place between tasks, so a workflow that chains
        several retrievals would otherwise start each one wherever the last left
        off -- and looking for account B on account A's page finds nothing. Every
        task begins from a known page.
        """
        return self.observe()

    def is_authenticated(self) -> bool:
        return self.observe().authenticated


# --- The fake portal -------------------------------------------------------


@dataclass
class Statement:
    account: str
    period: str
    holder: str


@dataclass
class FakePortalConfig:
    """Every hazard the guardrails are supposed to survive."""

    host: str = "portal.schwab.example"
    authenticated: bool = True
    mfa_on_entry: bool = False
    #: Show a consent or promo interstitial before the dashboard.
    interstitial: bool = False
    #: End the session after this many actions.
    expire_after: int | None = None
    #: Rename every control, as a redesign would.
    redesigned: bool = False
    #: Offer an account whose number looks like the one being asked for.
    lookalike_account: str | None = None
    #: Put a transaction confirmation page one click from the dashboard.
    transaction_page: bool = True
    #: How this custodian arranges its statements. Step 39 says adding a
    #: custodian must not need a custodian-specific script, so these are the
    #: shapes the one navigator has to cope with.
    layout: str = "flat"


class FakePortal(BrowserDriver):
    """A custodian portal that misbehaves in all the documented ways."""

    def __init__(self, statements: list[Statement], config: FakePortalConfig | None = None):
        self.config = config or FakePortalConfig()
        self.statements = statements
        self.actions = 0
        self.history: list[str] = []
        self._path = "/dashboard"
        if self.config.mfa_on_entry:
            self._path = "/mfa"
        elif self.config.interstitial:
            self._path = "/notice"
        elif not self.config.authenticated:
            self._path = "/login"

    # -- driver interface --------------------------------------------------

    def observe(self) -> PageObservation:
        self.history.append(self._path)
        return self._page(self._path)

    def act(self, action: Action) -> PageObservation:
        self.actions += 1
        if self.config.expire_after is not None and self.actions > self.config.expire_after:
            self._path = "/login"
            raise SessionLost(f"the session ended after {self.config.expire_after} actions")

        page = self._page(self._path)
        element = page.element(action.element_id)
        if element is None:
            raise ElementNotFound(action.element_id, self._path)
        if element.href:
            self._path = element.href
            if self._path == "/mfa":
                raise MfaChallenge("the portal asked for a second factor")
        return self.observe()

    def download(self, element_id: str, destination: Path) -> Path:
        # A download is a request to the portal like any other, so it spends
        # budget and can hit an expired session.
        self.actions += 1
        if self.config.expire_after is not None and self.actions > self.config.expire_after:
            self._path = "/login"
            raise SessionLost(f"the session ended after {self.config.expire_after} actions")
        page = self._page(self._path)
        element = page.element(element_id)
        if element is None or element.kind != DOWNLOAD:
            raise ElementNotFound(element_id, self._path)
        account, period = element.href.split("|")
        statement = next(
            (s for s in self.statements if s.account == account and s.period == period), None
        )
        if statement is None:
            raise ElementNotFound(element_id, self._path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(render_statement_pdf(statement))
        return destination

    def home(self) -> PageObservation:
        if self.config.authenticated and self._path not in ("/login", "/mfa", "/notice"):
            self._path = "/dashboard"
        return self.observe()

    def screenshot(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        page = self._page(self._path)
        destination.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="120">'
            f'<rect width="600" height="120" fill="#eef1f5"/>'
            f'<text x="16" y="44" font-size="14">{page.title}</text>'
            f'<text x="16" y="72" font-size="12">{page.url}</text></svg>',
            encoding="utf-8",
        )
        return destination

    # -- pages -------------------------------------------------------------

    @property
    def url(self) -> str:
        return f"https://{self.config.host}{self._path}"

    def _label(self, plain: str, redesigned: str) -> str:
        return redesigned if self.config.redesigned else plain

    def _page(self, path: str) -> PageObservation:
        builder = {
            "/login": self._login,
            "/mfa": self._mfa,
            "/notice": self._notice,
            "/dashboard": self._dashboard,
            "/transfer": self._transfer,
        }.get(path)
        if builder is not None:
            return builder()
        if path.startswith("/accounts/"):
            parts = [piece for piece in path.split("/") if piece]
            account = parts[1]
            if len(parts) == 2:
                return self._account(account)
            tail = parts[2]
            if tail == "documents":
                return self._documents(account)
            if tail.startswith("y"):
                return self._year(account, tail[1:])
            return self._account(account)
        return PageObservation(self.url, "Not found", "That page does not exist.")

    def _login(self) -> PageObservation:
        return PageObservation(
            self.url, "Sign in",
            "Please sign in to continue.", authenticated=False,
            elements=(
                Element("username", INPUT, "Username"),
                Element("password", INPUT, "Password"),
                Element("signin", BUTTON, "Sign in"),
            ),
        )

    def _mfa(self) -> PageObservation:
        return PageObservation(
            self.url, "Verify it's you",
            "Enter the code we sent to your phone.", authenticated=False,
            elements=(Element("code", INPUT, "Security code"),
                      Element("verify", BUTTON, "Verify")),
        )

    def _notice(self) -> PageObservation:
        return PageObservation(
            self.url, "Important notice",
            "We have updated our terms of service. Please review and accept to continue.",
            is_modal=True,
            elements=(
                Element("accept", BUTTON, "Accept and continue", href="/dashboard"),
                Element("survey", LINK, "Take our 2 minute survey", href="/dashboard"),
            ),
        )

    def _dashboard(self) -> PageObservation:
        if self.config.layout == "dashboard_direct":
            # Everything on one page: accounts and their statements together.
            elements: list[Element] = []
            for account in sorted({s.account for s in self.statements}):
                elements.append(Element(f"acct-{account}", LINK,
                                        f"Account {account}", href=f"/accounts/{account}"))
                elements.extend(self._statement_elements(account, self._periods(account)))
            if self.config.transaction_page:
                elements.append(Element("transfer", BUTTON, "Transfer funds",
                                        href="/transfer"))
            return PageObservation(self.url, "Accounts overview", "Your accounts",
                                   tuple(elements))
        accounts = sorted({s.account for s in self.statements})
        if self.config.lookalike_account:
            accounts = sorted(set(accounts) | {self.config.lookalike_account})
        elements = [
            Element(f"acct-{account}", LINK,
                    self._label(f"Account {account}", f"Portfolio {account}"),
                    href=f"/accounts/{account}")
            for account in accounts
        ]
        if self.config.transaction_page:
            elements += [
                Element("transfer", BUTTON, self._label("Transfer funds", "Move money"),
                        href="/transfer"),
                Element("trade", BUTTON, self._label("Place a trade", "Trade now"),
                        href="/transfer"),
            ]
        return PageObservation(
            self.url, "Accounts overview",
            "Your accounts", tuple(elements),
        )

    def _periods(self, account: str) -> list[str]:
        return sorted(
            {s.period for s in self.statements if s.account == account}, reverse=True
        )

    def _statement_elements(self, account: str, periods) -> list[Element]:
        return [
            Element(f"stmt-{account}-{period}", DOWNLOAD,
                    self._label(f"Statement {period}", f"{period} document"),
                    href=f"{account}|{period}")
            for period in periods
        ]

    def _holder(self, account: str) -> str:
        return next((s.holder for s in self.statements if s.account == account), "Unknown")

    def _account(self, account: str) -> PageObservation:
        layout = self.config.layout
        periods = self._periods(account)
        banking = Element("update-banking", BUTTON,
                          self._label("Update banking details", "Edit bank info"),
                          href="/transfer")

        if layout == "tabbed":
            # Statements live behind a documents tab, not on the account page.
            elements = [
                Element(f"docs-{account}", LINK,
                        self._label("Documents", "Paperless documents"),
                        href=f"/accounts/{account}/documents"),
                Element(f"positions-{account}", LINK, "Positions",
                        href=f"/accounts/{account}"),
                banking,
            ]
        elif layout == "year_first":
            years = sorted({period[:4] for period in periods}, reverse=True)
            elements = [
                Element(f"year-{account}-{year}", LINK, f"{year} statements",
                        href=f"/accounts/{account}/y{year}")
                for year in years
            ] + [banking]
        else:
            elements = self._statement_elements(account, periods) + [banking]

        return PageObservation(
            self.url, f"Account {account}",
            f"Account {account}\nAccount holder: {self._holder(account)}\nStatements",
            tuple(elements),
        )

    def _documents(self, account: str) -> PageObservation:
        return PageObservation(
            self.url, f"Documents for {account}",
            f"Account {account}\nAccount holder: {self._holder(account)}\nStatements",
            tuple(self._statement_elements(account, self._periods(account))),
        )

    def _year(self, account: str, year: str) -> PageObservation:
        periods = [p for p in self._periods(account) if p.startswith(year)]
        return PageObservation(
            self.url, f"{year} statements for {account}",
            f"Account {account}\nAccount holder: {self._holder(account)}",
            tuple(self._statement_elements(account, periods)),
        )

    def _transfer(self) -> PageObservation:
        return PageObservation(
            self.url, "Confirm transfer",
            "Please confirm this transfer. Once you authorize this transaction it "
            "cannot be reversed.",
            elements=(Element("authorize", BUTTON, "Authorize transfer"),
                      Element("cancel", LINK, "Cancel", href="/dashboard")),
        )


class ElementNotFound(Exception):
    def __init__(self, element_id: str, path: str):
        super().__init__(f"no element {element_id!r} on {path}")


def render_statement_pdf(statement: Statement) -> bytes:
    """A statement PDF good enough for verification to read back."""
    from .pdf import PdfDocument

    doc = PdfDocument()
    doc.heading("Account Statement", size=17)
    doc.text(f"Account number: {statement.account}", size=11)
    doc.text(f"Account holder: {statement.holder}", size=11)
    doc.text(f"Statement period: {statement.period}", size=11)
    doc.rule()
    doc.text("Beginning balance    412,300.00")
    doc.text("Ending balance       414,118.42")
    return doc.to_bytes()
