# Tests

Two Playwright suites against `../index.html`. No build step, no server.

    node test/test.js     # 33 behavioural tests
    node test/test2.js    # 19 regression tests for the September audit fixes
    node test/test3.js    # 18 tests for the per-task workspace

`test.js` covers fresh load, tick and partial-credit maths, persistence across
reload, wipe-and-restore, the all-tasks-done edge case, every tab rendering,
theme toggle, and the page surviving blocked `localStorage`.

`test2.js` covers the audit fixes, the backup status indicator, the 30-day nudge,
and asserts that all 385 tasks have a unique title and a unique Do text.

`test3.js` covers the workspace: opening it, written steps, ticking steps off,
the list builder, the notes area, the link field, persistence across reload, and
marking a task done from inside it.

Requires Playwright and a Chromium binary; adjust the two paths at the top of
each file if yours differ.
