from __future__ import annotations

import argparse
import os

from .models import SheetEvent
from .sheets import SheetsClient
from .workflow import event_to_spreadsheet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a Google Sheet from an mcrobotcombatevents JSON export"
    )
    parser.add_argument(
        "event_json",
        help="Path to event JSON file produced by mcrobotcombatevents",
    )
    parser.add_argument(
        "--credentials",
        help="Path to Google service account credentials JSON "
        "(default: GOOGLE_APPLICATION_CREDENTIALS env var)",
    )
    parser.add_argument(
        "--oauth-client-secrets",
        help="Path to OAuth client secrets JSON for user login flow",
    )
    parser.add_argument(
        "--oauth-token",
        default="rce2sheet_token.json",
        help=(
            "Token key identifier (keyring backend) or fallback file path "
            "(default: rce2sheet_token.json)"
        ),
    )
    parser.add_argument(
        "--title",
        help="Spreadsheet title (default: RCE Event <event_id>)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    event = SheetEvent.from_json_file(args.event_json)

    if args.oauth_client_secrets:
        client = SheetsClient.from_user_oauth(
            args.oauth_client_secrets,
            token_path=args.oauth_token,
        )
    else:
        credentials_path = args.credentials or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if not credentials_path:
            print(
                "Error: Google auth required. Use either --oauth-client-secrets "
                "for user login or --credentials / GOOGLE_APPLICATION_CREDENTIALS "
                "for service account auth."
            )
            return 1
        client = SheetsClient.from_credentials_file(credentials_path)

    spreadsheet_id = event_to_spreadsheet(event, client, spreadsheet_title=args.title)
    print(
        f"Created spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
