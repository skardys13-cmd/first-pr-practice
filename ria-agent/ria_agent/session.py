"""Session detection (Step 18, F-11 to F-14).

The agent works inside a session the human already authenticated. It never logs
in, never answers an MFA challenge, and never retries either. When the session
is not there, that is a stop with instructions, not a problem to solve.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import stops
from .browser import BrowserDriver, MfaChallenge, PageObservation, SessionLost


@dataclass(frozen=True)
class SessionState:
    live: bool
    stop_reason: str | None = None
    detail: str = ""

    @property
    def next_step(self) -> str | None:
        return stops.next_step_for(self.stop_reason) if self.stop_reason else None


LIVE = SessionState(True)


class HumanPresence:
    """Whether the operator is using this session right now.

    F-13 and F-14: interleaved clicks make actions unattributable, and the
    agent yields rather than racing its own human. The real implementation
    watches input activity; this default assumes the human is away, and an
    install that cannot tell should say so rather than assume.
    """

    def is_active(self) -> bool:
        return False


def detect(driver: BrowserDriver, presence: HumanPresence | None = None) -> SessionState:
    """Is there a live authenticated session to work in?"""
    if (presence or HumanPresence()).is_active():
        return SessionState(
            False, stops.HUMAN_ACTIVE,
            "you are working in this session, so the agent stood down",
        )

    try:
        observation = driver.observe()
    except SessionLost as lost:
        return SessionState(False, stops.SESSION_EXPIRED, str(lost))
    except MfaChallenge as challenge:
        return SessionState(False, stops.MFA_CHALLENGE, str(challenge))

    if _looks_like_mfa(observation):
        return SessionState(
            False, stops.MFA_CHALLENGE,
            "the portal is asking for a second factor. The agent will not "
            "attempt it, and will not retry.",
        )
    if not observation.authenticated:
        return SessionState(
            False, stops.NOT_LOGGED_IN,
            f"there is no signed-in session at {observation.url}",
        )
    return LIVE


def _looks_like_mfa(observation: PageObservation) -> bool:
    haystack = f"{observation.title} {observation.text}".lower()
    return any(
        phrase in haystack
        for phrase in ("security code", "verification code", "two-factor",
                       "verify it's you", "authenticator", "one-time code")
    )
