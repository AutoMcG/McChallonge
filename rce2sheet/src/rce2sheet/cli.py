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
        help="Path to OAuth client secrets JSON for user login flow. "
        "Falls back to GOOGLE_OAUTH_CLIENT_SECRETS env var if not provided.",
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

    # Determine OAuth client secrets path: explicit arg > env var > None
    oauth_client_secrets = args.oauth_client_secrets or os.environ.get(
        "GOOGLE_OAUTH_CLIENT_SECRETS"
    )
    if oauth_client_secrets:
        client = SheetsClient.from_user_oauth(
            oauth_client_secrets,
            token_path=args.oauth_token,
        )
    else:
        credentials_path = args.credentials or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if credentials_path:
            client = SheetsClient.from_credentials_file(credentials_path)
        else:
            # No explicit auth flag — try a previously stored OAuth token.
            try:
                client = SheetsClient.from_user_oauth(
                    None, token_path=args.oauth_token
                )
            except RuntimeError as exc:
                print(
                    f"Error: {exc}\n"
                    "Use --oauth-client-secrets or set GOOGLE_OAUTH_CLIENT_SECRETS env var "
                    "to authorize for the first time, or --credentials / GOOGLE_APPLICATION_CREDENTIALS "
                    "for service account auth."
                )
                return 1

    spreadsheet_id = event_to_spreadsheet(event, client, spreadsheet_title=args.title)
    print(
        f"Created spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
