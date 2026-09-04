"""Command line entry points."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .export import export_csv, export_pdf
from .queue import Queue
from .seeded_errors import SeedRegistry, SeededErrorInjector
from .startup import Application


def _app(args) -> Application:
    return Application(
        storage_dir=args.home,
        model_version=args.model,
        operator=args.operator,
        role=args.role,
    )


def _queue(app: Application, args) -> Queue:
    registry = SeedRegistry(Path(app.storage_dir) / "seeds.jsonl")
    return Queue(
        app.log,
        model_version=app.model_version,
        approval_cap=getattr(args, "approval_cap", 20),
        done_cap=getattr(args, "done_cap", 8),
        seed_registry=registry,
    )


def cmd_serve(args) -> int:
    from .web import build_server

    app = _app(args)
    queue = _queue(app, args)
    server = build_server(app, queue, port=args.port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Review queue for {app.operator} at {url}")
    print(f"Storage: {app.storage_dir}")
    print("Loopback only. Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
        app.close()
    return 0


def cmd_seed(args) -> int:
    """Step 11: fill the queue with fake data and use it for a week."""
    from .synthetic import generate

    app = _app(args)
    receipts = generate(
        args.count, seed=args.seed, model_version=app.model_version,
        evidence_dir=app.evidence_dir,
    )
    registry = SeedRegistry(Path(app.storage_dir) / "seeds.jsonl")
    injector = SeededErrorInjector(
        registry, enabled=args.seeded_errors, rate=args.seeded_error_rate
    )
    planted = 0
    for receipt in receipts:
        receipt, fault = injector.maybe_seed(receipt)
        planted += bool(fault)
        app.log.append(receipt)
    print(f"Wrote {len(receipts)} synthetic receipts to {app.log.db_path}")
    if args.seeded_errors:
        print(f"{planted} of them were deliberately seeded with a fault.")
    app.close()
    return 0


def cmd_export(args) -> int:
    app = _app(args)
    filters = {
        key: value for key, value in (
            ("human_owner", args.person), ("workflow_id", args.workflow),
            ("outcome", args.outcome), ("since", args.since), ("until", args.until),
        ) if value
    }
    out = Path(args.out)
    if out.suffix.lower() == ".csv":
        written = export_csv(app.log, out, **filters)
    else:
        written = export_pdf(app.log, out, firm=args.firm, **filters)
    print(f"Wrote {written} ({written.stat().st_size} bytes)")
    app.close()
    return 0


def cmd_shadow(args) -> int:
    """Step 15: classify real tasks, take no action, log everything."""
    from .classifier import Classifier
    from .crm import FixtureCrm
    from .shadow import ShadowRunner

    app = _app(args)
    crm = FixtureCrm(path=args.tasks) if args.tasks else FixtureCrm.from_bundled_fixtures()
    runner = ShadowRunner(crm, Classifier(), app.log, operator=app.operator,
                          role=app.role, model_version=app.model_version)
    observations = runner.run(owner=args.owner)
    recognised = sum(1 for o in observations if o.recognised)
    print(f"Observed {len(observations)} tasks. No action was taken on any of them.")
    print(f"  recognised   {recognised}")
    print(f"  unrecognised {len(observations) - recognised}  (a success state)")
    print(f"\nReceipts are in {app.log.db_path}.")
    print("Review them, write a labels file, then run: ria-agent shadow-report")
    app.close()
    return 0


def cmd_shadow_report(args) -> int:
    """Step 16: score the shadow log against a human review."""
    from .shadow import build_report, observations_from_log
    from .whitelist import Whitelist

    app = _app(args)
    observations = observations_from_log(app.log)
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8")) if args.labels else {}
    labels = {
        task_id: (value if isinstance(value, dict) else {"workflow": value})
        for task_id, value in labels.items()
    }
    report = build_report(observations, labels)
    print(report.summary())
    if report.unlabelled:
        print(f"\n{len(report.unlabelled)} classifications are not yet reviewed "
              "and were not scored.")

    clean = report.clean_templates(min_samples=args.min_samples)
    print(f"\nFit to whitelist at n>={args.min_samples}: {len(clean)} template(s)")
    for template in sorted(clean):
        print(f"  {template}")

    if args.write_whitelist:
        path = Whitelist(clean).save(Path(app.storage_dir) / "whitelist.json")
        print(f"\nWrote {path}. The agent will act on these task types and no others.")
    else:
        print("\nNothing was locked in. Re-run with --write-whitelist to enforce this.")
    app.close()
    return 0


def _demo_portal():
    """The fake custodian portal.

    The real driver attaches to the operator's already-authenticated browser and
    slots in behind BrowserDriver. Until it exists, these commands drive the
    fake one, which is why they say so on every line of output.
    """
    from .browser import FakePortal, FakePortalConfig, Statement

    periods = [f"2026-{month:02d}" for month in range(1, 9)]
    statements = [Statement("1234-5678", period, "Helen Barrow") for period in periods]
    statements += [Statement("9983-3570", period, "Rosalind Whitcombe") for period in periods]
    return FakePortal(statements, FakePortalConfig())


def _retrieval(app, driver=None):
    from .promotion import PromotionRegistry
    from .retrieval import StatementRetrieval

    return StatementRetrieval(
        driver or _demo_portal(), app.log,
        operator=app.operator, role=app.role, model_version=app.model_version,
        allowed_domains={"portal.schwab.example"},
        evidence_dir=app.evidence_dir,
        promotions=PromotionRegistry(Path(app.storage_dir) / "promotions.jsonl"),
    )


def cmd_retrieve(args) -> int:
    """Steps 18-22: retrieve one statement and prove which one it was."""
    from .navigator import RetrievalGoal
    from .plain import as_text

    app = _app(args)
    goal = RetrievalGoal(args.account, args.period, args.holder or "")
    outcome = _retrieval(app).run(args.task, goal)
    print("Driving the FAKE custodian portal. No real custodian was contacted.\n")
    print(as_text(outcome.receipt))
    if outcome.verification and not outcome.verification.passed:
        print("\nChecks that failed:")
        for check in outcome.verification.failures:
            print(f"  {check.name}: {check.detail}")
    app.close()
    return 0 if outcome.succeeded else 1


def cmd_attend(args) -> int:
    """Steps 23-24: attended runs, every deviation logged, then the gate."""
    from .attended import AttendedHarness
    from .navigator import RetrievalGoal

    app = _app(args)
    periods = [f"2026-{month:02d}" for month in range(1, 9)]
    harness = AttendedHarness(_retrieval(app))
    cases = [
        (f"RT-A{index:03d}",
         RetrievalGoal("1234-5678", periods[index % len(periods)], "Helen Barrow"))
        for index in range(args.runs)
    ]
    print(f"Driving the FAKE custodian portal for {args.runs} runs.")
    print("A real pilot watches every one of these by hand.\n")
    report = harness.run_batch(cases)
    print(report.summary())
    app.close()
    return 0


def cmd_promotion(args) -> int:
    """Whether a workflow may run without a person, and why not."""
    from .promotion import PromotionRegistry, decide, gather
    from .seeded_errors import SeedRegistry

    app = _app(args)
    seeds = SeedRegistry(Path(app.storage_dir) / "seeds.jsonl")
    registry = PromotionRegistry(Path(app.storage_dir) / "promotions.jsonl")
    workflow_id, role_id = args.workflow, args.role or app.role

    evidence = gather(app.log, seeds, workflow_id, role_id)
    decision = decide(workflow_id, evidence)
    print(f"{workflow_id} for {role_id}")
    print(f"  currently: {'auto-executing' if registry.is_promoted(workflow_id, role_id) else 'approval-gated'}")
    print(f"  {decision.explain()}")

    if args.promote:
        if not decision.promote:
            print("\nNot promoting. The criteria above are not met.")
            app.close()
            return 1
        registry.promote(workflow_id, role_id, decision)
        print("\nPromoted. This is reversible, and one incorrect execution reverses it.")
    if args.demote:
        registry.demote(workflow_id, role_id, args.demote)
        print(f"\nDemoted: {args.demote}")
    app.close()
    return 0


def cmd_verify(args) -> int:
    """Check the log's two copies still agree, and report the catch rate."""
    app = _app(args)
    problems = app.log.verify_mirror()
    print(f"{app.log.count()} receipts in {app.log.db_path}")
    if problems:
        print("\nThe log does not verify:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("The database and the JSONL mirror agree.")

    registry = SeedRegistry(Path(app.storage_dir) / "seeds.jsonl")
    rate = registry.catch_rate()
    if rate.caught or rate.missed or rate.pending:
        print(f"\nSeeded-error catch rate: {rate}")
    app.close()
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ria-agent",
        description="Local operations agent. Read CONSTITUTION.md first.",
    )
    parser.add_argument("--home", default=None,
                        help="storage directory (default: $RIA_AGENT_HOME or ~/.ria-agent)")
    parser.add_argument("--model", default=None,
                        help="pinned model version (default: $RIA_AGENT_MODEL)")
    parser.add_argument("--operator", default=None,
                        help="the person this install acts for (default: $RIA_AGENT_OPERATOR)")
    parser.add_argument("--role", default=None,
                        help="their role (default: $RIA_AGENT_ROLE)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="run the review queue on localhost")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--approval-cap", type=int, default=20,
                       help="most items shown in the approval lane at once")
    serve.add_argument("--done-cap", type=int, default=8,
                       help="most finished items shown before linking to the export")
    serve.set_defaults(func=cmd_serve)

    seed = subparsers.add_parser("seed", help="fill the queue with synthetic items")
    seed.add_argument("--count", type=int, default=40)
    seed.add_argument("--seed", type=int, default=20260904)
    seed.add_argument("--seeded-errors", action="store_true",
                      help="also plant deliberately wrong items to measure catch rate")
    seed.add_argument("--seeded-error-rate", type=float, default=0.15)
    seed.set_defaults(func=cmd_seed)

    export = subparsers.add_parser("export", help="export the log to CSV or PDF")
    export.add_argument("out", help="output path; .csv or .pdf")
    export.add_argument("--person"), export.add_argument("--workflow")
    export.add_argument("--outcome"), export.add_argument("--since")
    export.add_argument("--until"), export.add_argument("--firm", default="")
    export.set_defaults(func=cmd_export)

    shadow = subparsers.add_parser(
        "shadow", help="classify real tasks and act on none of them")
    shadow.add_argument("--owner", default=None, help="only this person's tasks")
    shadow.add_argument("--tasks", default=None, help="task fixture JSON to read")
    shadow.set_defaults(func=cmd_shadow)

    report = subparsers.add_parser(
        "shadow-report", help="score the shadow log against a human review")
    report.add_argument("--labels", default=None,
                        help="JSON of task_id -> workflow, or -> {workflow, account, period}")
    report.add_argument("--min-samples", type=int, default=20,
                        help="samples a template needs before it can be whitelisted")
    report.add_argument("--write-whitelist", action="store_true",
                        help="lock the clean templates in as the whitelist")
    report.set_defaults(func=cmd_shadow_report)

    retrieve = subparsers.add_parser(
        "retrieve", help="retrieve one statement (against the fake portal)")
    retrieve.add_argument("--account", required=True)
    retrieve.add_argument("--period", required=True, help="e.g. 2026-08")
    retrieve.add_argument("--holder", default=None)
    retrieve.add_argument("--task", default="RT-0000", help="the CRM task id")
    retrieve.set_defaults(func=cmd_retrieve)

    attend = subparsers.add_parser(
        "attend", help="attended runs and the unattended gate")
    attend.add_argument("--runs", type=int, default=50)
    attend.set_defaults(func=cmd_attend)

    promotion = subparsers.add_parser(
        "promotion", help="may a workflow run without a person?")
    promotion.add_argument("workflow", help="e.g. statement_retrieval")
    promotion.add_argument("--role", default=None)
    promotion.add_argument("--promote", action="store_true")
    promotion.add_argument("--demote", metavar="REASON", default=None)
    promotion.set_defaults(func=cmd_promotion)

    verify = subparsers.add_parser("verify", help="check the log verifies")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
