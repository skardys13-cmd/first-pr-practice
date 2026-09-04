"""Stop taxonomy (Step 10).

A stop is a success state. Every stop names a specific, actionable reason and
tells the human what to do next -- "Schwab session expired at 10:42", never
"error". A stop with no suggested next step is rejected by the receipt
validator.
"""

# --- The eight core reasons named in Step 10 -------------------------------

SESSION_EXPIRED = "session_expired"
ELEMENT_NOT_FOUND = "element_not_found"
AMBIGUOUS_MATCH = "ambiguous_match"
DATA_MISMATCH = "data_mismatch"
PERMISSION_DENIED = "permission_denied"
UNEXPECTED_PAGE = "unexpected_page"
TIMEOUT = "timeout"
LOW_CONFIDENCE = "low_confidence"

# --- Stops introduced by later steps ---------------------------------------

MFA_CHALLENGE = "mfa_challenge"                    # Constitution I, F-12
NOT_LOGGED_IN = "not_logged_in"                    # Step 18
OFF_ALLOWLIST = "off_allowlist_navigation"         # Step 20
FORBIDDEN_ELEMENT = "forbidden_element"            # Step 20, Constitution VIII
TRANSACTION_PAGE = "transaction_confirmation_page"  # Step 20
CLICK_BUDGET_EXCEEDED = "click_budget_exceeded"    # Step 20, F-20
REPEAT_ACTION = "repeat_action_detected"           # F-20
CONSENT_INTERSTITIAL = "consent_interstitial"      # F-18
VERIFICATION_FAILED = "verification_failed"        # Step 21
UNRECOGNISED_TASK = "unrecognised_task"            # Step 14
NOT_WHITELISTED = "task_type_not_whitelisted"      # Step 17
ROLE_NOT_PERMITTED = "role_not_permitted"          # Constitution VI
HUMAN_ACTIVE = "human_active_in_session"           # F-13, F-14
ENVIRONMENT_INTERRUPTED = "environment_interrupted"  # F-44
EXTRACTION_FAILED = "extraction_failed"            # F-30, Constitution V
MISSING_INFORMATION = "missing_information"        # Step 13, an unresolved entity

STOP_REASONS = frozenset({
    SESSION_EXPIRED, ELEMENT_NOT_FOUND, AMBIGUOUS_MATCH, DATA_MISMATCH,
    PERMISSION_DENIED, UNEXPECTED_PAGE, TIMEOUT, LOW_CONFIDENCE,
    MFA_CHALLENGE, NOT_LOGGED_IN, OFF_ALLOWLIST, FORBIDDEN_ELEMENT,
    TRANSACTION_PAGE, CLICK_BUDGET_EXCEEDED, REPEAT_ACTION,
    CONSENT_INTERSTITIAL, VERIFICATION_FAILED, UNRECOGNISED_TASK,
    NOT_WHITELISTED, ROLE_NOT_PERMITTED, HUMAN_ACTIVE,
    ENVIRONMENT_INTERRUPTED, EXTRACTION_FAILED, MISSING_INFORMATION,
})

# Default next step per reason. A caller may pass something more specific, but
# it may never leave the next step blank.
SUGGESTED_NEXT_STEP = {
    SESSION_EXPIRED: "Log back into the custodian site, then re-run this task.",
    ELEMENT_NOT_FOUND: "Open the page yourself and check whether the site has changed. If it has, report it before re-running.",
    AMBIGUOUS_MATCH: "Confirm which account was meant, then re-run with the exact account number.",
    DATA_MISMATCH: "Compare the two values by hand and decide which source is correct. The agent will not resolve this.",
    PERMISSION_DENIED: "Check whether your login has access to this household. The agent has exactly your permissions.",
    UNEXPECTED_PAGE: "Open the site and see where the flow now leads. Report the change before re-running.",
    TIMEOUT: "Check the site is responding, then re-run.",
    LOW_CONFIDENCE: "Do this one by hand. Tell us what the task meant so the classifier can learn it.",
    MFA_CHALLENGE: "Complete the MFA challenge yourself, then re-run. The agent will never attempt MFA.",
    NOT_LOGGED_IN: "Log into the custodian site in your browser, then re-run.",
    OFF_ALLOWLIST: "The agent navigated off the approved domain list and stopped. Report this -- it should not happen.",
    FORBIDDEN_ELEMENT: "The agent reached a control it is never allowed to touch and stopped. Do this step by hand.",
    TRANSACTION_PAGE: "The agent reached a transaction confirmation page and stopped immediately. Check nothing was submitted, then report this.",
    CLICK_BUDGET_EXCEEDED: "The task took more steps than allowed and was stopped. Do it by hand and report how many steps it took.",
    REPEAT_ACTION: "The agent repeated the same failed action and stopped. The site has probably changed.",
    CONSENT_INTERSTITIAL: "A consent, survey, or terms dialog is blocking the flow. Accept or dismiss it yourself -- the agent will never accept terms on the firm's behalf.",
    VERIFICATION_FAILED: "The retrieved file failed its checks and was not accepted. Retrieve it by hand and compare.",
    UNRECOGNISED_TASK: "The agent does not recognise this task type. Do it by hand.",
    NOT_WHITELISTED: "This task type is not yet approved for the agent. Do it by hand.",
    ROLE_NOT_PERMITTED: "This workflow is not part of your role's capabilities. Ask whoever owns role configuration.",
    HUMAN_ACTIVE: "You were working in the same session, so the agent yielded. Re-run when you are done.",
    ENVIRONMENT_INTERRUPTED: "The machine slept, the browser closed, or the connection dropped. Re-run when the environment is stable.",
    EXTRACTION_FAILED: "The agent could not read a value and refused to guess. Read it yourself.",
    MISSING_INFORMATION: "The task does not say enough to act on. Add the missing detail to the task, then re-run.",
}


def next_step_for(reason: str) -> str:
    """Return the default suggested next step for a stop reason."""
    if reason not in STOP_REASONS:
        raise ValueError(f"unknown stop reason: {reason!r}")
    return SUGGESTED_NEXT_STEP[reason]
