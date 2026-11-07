#!/usr/bin/env python
"""CLI to bulk-add approved participants from a sheet-read JSON to a Challonge tournament."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dotenv import load_dotenv

from ..services.challonging import bulk_add_participants, prepare_session, prepare_session_from_env


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description=(
            "Bulk-add approved participants (exported by rce2sheet-read) "
            "to a Challonge tournament"
        )
    )
    parser.add_argument(
        "participants_json",
        help="Path to JSON file produced by rce2sheet-read",
    )
    parser.add_argument(
        "tournament_id",
        help="Challonge tournament ID or URL slug",
    )
    parser.add_argument(
        "--competition",
        help=(
            "Sheet/competition name to import (default: all competitions). "
            "Matches the sheet tab title exactly."
        ),
    )
    parser.add_argument(
        "-u", "--user",
        help="Challonge username (default: challonge_user env var)",
    )
    parser.add_argument(
        "-k", "--key",
        help="Challonge API key (default: challonge_key env var)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print request URL, body params, and raw API response",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)

    if args.user and args.key:
        session = prepare_session(args.user, args.key)
    else:
        try:
            session = prepare_session_from_env()
        except ValueError as exc:
            print(f"Error: {exc}. Use -u/-k or set challonge_user/challonge_key.")
            return 1

    with open(args.participants_json, encoding="utf-8") as f:
        data = json.load(f)

    competitions = data.get("competitions", [])
    if args.competition:
        competitions = [c for c in competitions if c["sheet_title"] == args.competition]
        if not competitions:
            print(f"Error: no competition named '{args.competition}' found in JSON.")
            return 1

    total_added = 0
    for comp in competitions:
        participants = comp.get("approved_participants", [])
        if not participants:
            print(f"  {comp['sheet_title']}: no approved participants, skipping.")
            continue

        requested_count = len(participants)
        print(f"  {comp['sheet_title']}: adding {requested_count} participant(s)...")
        results = bulk_add_participants(session, args.tournament_id, participants, verbose=getattr(args, 'verbose', False))
        created_count = len(results)
        if created_count == 0 and requested_count > 0:
            print(
                f"Error: Challonge returned no created participants for '{comp['sheet_title']}'. "
                "Enable -v for request/response details."
            )
            return 1

        if created_count != requested_count:
            print(
                f"Warning: Requested {requested_count}, created {created_count} for '{comp['sheet_title']}'."
            )

        total_added += len(results)
        for entry in results:
            print(f"    + {entry.get('name', '?')} (id={entry.get('id')})")

    print(f"Done. Added {total_added} participant(s) to tournament '{args.tournament_id}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
