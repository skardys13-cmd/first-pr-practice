# Tests

Two Playwright suites against `../index.html`. No build step, no server.

    node test/test.js     # 33 behavioural tests
    node test/test2.js    # 16 regression tests for the September audit fixes

`test.js` covers fresh load, tick and partial-credit maths, persistence across
reload, wipe-and-restore, the all-tasks-done edge case, every tab rendering,
theme toggle, and the page surviving blocked `localStorage`.

`test2.js` covers the four audit fixes plus the backup status indicator and the
30-day nudge.

Requires Playwright and a Chromium binary; adjust the two paths at the top of
each file if yours differ.
