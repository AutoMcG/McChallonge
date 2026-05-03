"""Read back an rce2sheet spreadsheet and export approved participants to JSON."""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field

from .sheets import SheetsClient

# Column indices (0-based) matching HEADERS in models.py
_IMAGE_URL_COL = 0
_BOT_NAME_COL = 1
_TEAM_NAME_COL = 2
_PASSED_WEIGHT_COL = 4
_PASSED_SAFETY_COL = 5
_PAID_COL = 6
_MIN_COLS = 7

_SPREADSHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")


def _spreadsheet_id_from_url(url: str) -> str:
    m = _SPREADSHEET_ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot parse spreadsheet ID from URL: {url}")
    return m.group(1)


def _is_yes(value: str) -> bool:
    return (value or "").strip().lower() == "yes"


@dataclass
class ApprovedParticipant:
    bot_name: str
    team_name: str | None = None
    image_url: str | None = None

    def to_dict(self) -> dict:
        return {
            "bot_name": self.bot_name,
            "team_name": self.team_name,
            "image_url": self.image_url,
        }


@dataclass
class ApprovedCompetition:
    sheet_title: str
    approved_participants: list[ApprovedParticipant] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sheet_title": self.sheet_title,
            "approved_participants": [p.to_dict() for p in self.approved_participants],
        }


@dataclass
class ApprovedParticipantList:
    spreadsheet_id: str
    competitions: list[ApprovedCompetition] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "spreadsheet_id": self.spreadsheet_id,
            "competitions": [c.to_dict() for c in self.competitions],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovedParticipantList":
        competitions = [
            ApprovedCompetition(
                sheet_title=c["sheet_title"],
                approved_participants=[
                    ApprovedParticipant(
                        bot_name=p["bot_name"],
                        team_name=p.get("team_name"),
                        image_url=p.get("image_url"),
                    )
                    for p in c.get("approved_participants", [])
                ],
            )
            for c in data.get("competitions", [])
        ]
        return cls(spreadsheet_id=data["spreadsheet_id"], competitions=competitions)

    @classmethod
    def from_json_file(cls, path: str) -> "ApprovedParticipantList":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def read_approved_participants(
    spreadsheet_url: str, client: SheetsClient
) -> ApprovedParticipantList:
    """Read a spreadsheet and return participants approved in all 3 columns."""
    spreadsheet_id = _spreadsheet_id_from_url(spreadsheet_url)

    meta = (
        client._svc.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    sheet_titles = [s["properties"]["title"] for s in meta.get("sheets", [])]

    competitions: list[ApprovedCompetition] = []
    for title in sheet_titles:
        resp = (
            client._svc.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=f"'{title}'")
            .execute()
        )
        rows = resp.get("values", [])
        # rows[0] is the header; skip it
        approved: list[ApprovedParticipant] = []
        for row in rows[1:]:
            padded = row + [""] * (_MIN_COLS - len(row))
            if (
                _is_yes(padded[_PASSED_WEIGHT_COL])
                and _is_yes(padded[_PASSED_SAFETY_COL])
                and _is_yes(padded[_PAID_COL])
            ):
                approved.append(
                    ApprovedParticipant(
                        image_url=padded[_IMAGE_URL_COL] or None,
                        bot_name=padded[_BOT_NAME_COL],
                        team_name=padded[_TEAM_NAME_COL] or None,
                    )
                )
        competitions.append(
            ApprovedCompetition(sheet_title=title, approved_participants=approved)
        )

    return ApprovedParticipantList(
        spreadsheet_id=spreadsheet_id, competitions=competitions
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read an rce2sheet spreadsheet and export approved participants to JSON"
    )
    parser.add_argument(
        "spreadsheet_url",
        help="Full Google Sheets URL (e.g. https://docs.google.com/spreadsheets/d/...)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="approved_participants.json",
        help="Output JSON file path (default: approved_participants.json)",
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
        "--credentials",
        help="Path to Google service account credentials JSON "
        "(default: GOOGLE_APPLICATION_CREDENTIALS env var)",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    # Determine OAuth client secrets path: explicit arg > env var > None
    oauth_client_secrets = args.oauth_client_secrets or os.environ.get(
        "GOOGLE_OAUTH_CLIENT_SECRETS"
    )
    if oauth_client_secrets:
        client = SheetsClient.from_user_oauth(
            oauth_client_secrets, token_path=args.oauth_token
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

    result = read_approved_participants(args.spreadsheet_url, client)

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result.to_json())

    total = sum(len(c.approved_participants) for c in result.competitions)
    print(f"Wrote {total} approved participant(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
