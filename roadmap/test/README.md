# Tests

Six Playwright suites against `../index.html`. No build step, no server.

    node test/test.js     # 33 behavioural tests
    node test/test2.js    # 19 regression tests for the September audit fixes
    node test/test3.js    # 15 tests for the per-task workspace
    node test/test4.js    # 42 tests for destinations, ledgers and the detail panel
    node test/test5.js    # 13 tests that every walkthrough still matches its task
    node test/test6.js    # 33 tests that date-bound work lands before its date

`test.js` covers fresh load, tick and partial-credit maths, persistence across
reload, wipe-and-restore, the all-tasks-done edge case, every tab rendering,
theme toggle, and the page surviving blocked `localStorage`.

`test2.js` covers the audit fixes, the backup status indicator, the 30-day nudge,
and asserts that all 385 tasks have a unique title and a unique Do text.

`test3.js` covers the workspace: opening it, written steps, ticking steps off,
the list builder, the notes area, the link field, persistence across reload, and
marking a task done from inside it.

`test4.js` covers what a task can reach and what it records. It pins the bug
where a generated walkthrough streamed in and then vanished on the next render:
the panel now has to survive a re-render, a reload, and a step being ticked. It
also asserts the link registry is clean and https-only, that all 106 tasks with
written walkthroughs link somewhere, that cross-task links only ever point
backwards, that a saved tool URL turns into a button on the tasks that need it,
that sending a row to a section prefills and lands on the right view, that the
four ledgers and the SOP library round-trip through storage, and that a v3 save
upgrades without losing anything.

Requires Playwright and a Chromium binary; adjust the two paths at the top of
each file if yours differ.

`test5.js` exists because of a real bug. Tasks get retargeted; `STEPS` is
keyed by position (`"1-3"`), so a rewritten task silently inherited the
previous task's walkthrough — task 1-3 became the Form ADV reading key while
still showing steps for setting a Series 65 exam date. Each entry is now
`{t: "<the exact task title it was written for>", s: [...]}`, `stepList()`
returns the steps only when that title still matches, and the workspace says
"Withheld" rather than showing steps for a task that no longer exists.

`steps-fingerprints.json` holds a hash of title + Do + Output for all 106.
`test5.js` fails if any task with a walkthrough has been reworded at all, so a
change to the plan forces a re-read of the steps rather than silently
invalidating them. After re-reading and updating them, regenerate with:

    python3 test/fingerprint.py

`test6.js` guards the sequencing. The plan is 426 hours run at three to four
evening hours a week, so it is a two-year plan, not a one-year one, and the
tasks written for a specific date have to land before that date. It asserts
the December kit (decision criteria, the call, licence clock, comp model,
internal-as-outside-offer, negotiation scripts, Florida breakeven) all fall
before ~week 23, that the credential pair straddles the exam, and that nine
real dependency pairs still run in order. It also asserts the id migration:
tasks were swapped between blocks, so `done`, `prog` and `work` keys had to be
remapped, and a save written before the re-sequence must still show the same
tasks ticked -- including when migrated twice.
