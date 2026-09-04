"""Command line entry points."""

from __future__ import annotations

import argparse
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

    verify = subparsers.add_parser("verify", help="check the log verifies")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
