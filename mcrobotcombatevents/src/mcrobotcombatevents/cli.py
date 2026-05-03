from __future__ import annotations

import argparse

from .workflow import scrape_event_to_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Robot Combat Events robots to nested JSON"
    )
    parser.add_argument("event_id", type=int, help="Robot Combat Events event ID")
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file path (default: event_<event_id>.json)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output or f"event_{args.event_id}.json"
    event = scrape_event_to_file(args.event_id, output, indent=args.indent)
    print(
        f"Exported event {event.event_id} with {len(event.competitions)} competitions to {output}"
    )
    return 0
