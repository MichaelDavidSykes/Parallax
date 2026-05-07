from __future__ import annotations

import argparse

from parallax_engine_prefect.flows import parallax_backtest_pipeline, parallax_ingestion_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Parallax Prefect flows locally.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Sync Polymarket markets and scan opportunities.")
    ingest.add_argument("--market-limit", type=int, default=80)
    ingest.add_argument("--min-edge", type=float, default=0.04)
    ingest.add_argument("--backend-url", default=None)

    backtest = subparsers.add_parser("backtest", help="Run the default backtest pipeline.")
    backtest.add_argument("--name", default="Prefect stat arb replay")
    backtest.add_argument("--initial-cash", type=float, default=10000)
    backtest.add_argument("--market-limit", type=int, default=100)
    backtest.add_argument("--min-edge", type=float, default=0.04)
    backtest.add_argument("--backend-url", default=None)

    args = parser.parse_args()
    if args.command == "ingest":
        parallax_ingestion_pipeline(
            market_limit=args.market_limit,
            min_edge=args.min_edge,
            backend_url=args.backend_url,
        )
    elif args.command == "backtest":
        parallax_backtest_pipeline(
            name=args.name,
            initial_cash=args.initial_cash,
            market_limit=args.market_limit,
            min_edge=args.min_edge,
            backend_url=args.backend_url,
        )

