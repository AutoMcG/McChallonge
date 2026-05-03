from __future__ import annotations

import json
import logging
import os
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    import keyring
except Exception:  # pragma: no cover - optional dependency at runtime
    keyring = None

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_SERVICE_NAME = "rce2sheet.google.oauth"

logger = logging.getLogger(__name__)


def _build_service(credentials_path: str):
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _token_backend() -> str:
    backend = os.environ.get("RCE2SHEET_TOKEN_BACKEND", "auto").strip().lower()
    if backend not in {"auto", "keyring", "file"}:
        backend = "auto"

    if backend == "auto":
        return "keyring" if keyring is not None else "file"

    if backend == "keyring" and keyring is None:
        logger.warning("keyring is unavailable; falling back to file token storage")
        return "file"

    return backend


def _save_token_file(token_path: str, token_json: str) -> None:
    token_dir = os.path.dirname(token_path)
    if token_dir:
        os.makedirs(token_dir, exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as token_file:
        token_file.write(token_json)


def _load_oauth_token(token_path: str) -> str | None:
    backend = _token_backend()

    if backend == "keyring":
        try:
            token_json = keyring.get_password(TOKEN_SERVICE_NAME, token_path)
        except Exception as exc:
            logger.warning("keyring read failed; falling back to file token storage: %s", exc)
            token_json = None

        if token_json:
            return token_json

        # One-way migration path from existing token files.
        if os.path.exists(token_path):
            with open(token_path, encoding="utf-8") as token_file:
                token_json = token_file.read()
            try:
                keyring.set_password(TOKEN_SERVICE_NAME, token_path, token_json)
            except Exception as exc:
                logger.warning("keyring write failed during migration: %s", exc)
            return token_json

        return None

    if os.path.exists(token_path):
        with open(token_path, encoding="utf-8") as token_file:
            return token_file.read()
    return None


def _save_oauth_token(token_path: str, token_json: str) -> None:
    backend = _token_backend()
    if backend == "keyring":
        try:
            keyring.set_password(TOKEN_SERVICE_NAME, token_path, token_json)
            return
        except Exception as exc:
            logger.warning("keyring write failed; falling back to file token storage: %s", exc)

    _save_token_file(token_path, token_json)


def _build_service_from_user_oauth(
    client_secrets_path: str | None, token_path: str
):
    """Build a Sheets service using OAuth user credentials.

    If a valid token is already stored (keyring or file), ``client_secrets_path``
    is not needed and may be ``None``.  It is only required when no stored token
    exists and an interactive browser-based authorization must be performed.
    """
    creds = None

    token_json = _load_oauth_token(token_path)
    if token_json:
        try:
            token_info = json.loads(token_json)
            creds = UserCredentials.from_authorized_user_info(token_info, SCOPES)
        except (ValueError, TypeError) as exc:
            logger.warning("Ignoring invalid stored OAuth token data: %s", exc)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not client_secrets_path:
            raise RuntimeError(
                "No stored OAuth token found for key '%s'. "
                "Run with --oauth-client-secrets to authorize for the first time."
                % token_path
            )
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        creds = flow.run_local_server(port=0)

    _save_oauth_token(token_path, creds.to_json())

    return build("sheets", "v4", credentials=creds)


class SheetsClient:
    """Thin wrapper around the Google Sheets v4 API resource."""

    def __init__(self, service):
        self._svc = service

    @classmethod
    def from_credentials_file(cls, credentials_path: str) -> "SheetsClient":
        return cls(_build_service(credentials_path))

    @classmethod
    def from_user_oauth(
        cls,
        client_secrets_path: str | None,
        token_path: str = "rce2sheet_token.json",
    ) -> "SheetsClient":
        """Build a client using OAuth user credentials.

        Pass ``client_secrets_path=None`` to use a previously stored token
        (keyring or file) without re-authorizing.
        """
        return cls(_build_service_from_user_oauth(client_secrets_path, token_path))

    def list_sheet_titles(self, spreadsheet_id: str) -> list[str]:
        """Return the titles of all sheets in the spreadsheet."""
        meta = (
            self._svc.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
            .execute()
        )
        return [s["properties"]["title"] for s in meta.get("sheets", [])]

    def get_values(self, spreadsheet_id: str, range_name: str) -> list[list[Any]]:
        """Return the cell values for the given range (A1 notation or sheet title)."""
        resp = (
            self._svc.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return resp.get("values", [])

    def create_spreadsheet(self, title: str, first_sheet_title: str) -> tuple[str, int]:
        """Create a new spreadsheet. Returns (spreadsheet_id, first_sheet_id)."""
        body = {
            "properties": {"title": title},
            "sheets": [{"properties": {"title": first_sheet_title}}],
        }
        resp = self._svc.spreadsheets().create(body=body).execute()
        spreadsheet_id = resp["spreadsheetId"]
        sheet_id = resp["sheets"][0]["properties"]["sheetId"]
        return spreadsheet_id, sheet_id

    def add_sheet(self, spreadsheet_id: str, title: str) -> int:
        """Add a new sheet tab. Returns the new sheet_id."""
        resp = (
            self._svc.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
            )
            .execute()
        )
        return resp["replies"][0]["addSheet"]["properties"]["sheetId"]

    def write_rows(
        self, spreadsheet_id: str, sheet_title: str, rows: list[list]
    ) -> None:
        """Write rows starting at A1 of the given sheet."""
        self._svc.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_title}'!A1",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()

    def format_as_table(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        row_count: int,
        col_count: int,
    ) -> None:
        """Apply table-like formatting (header, filter, frozen row, banding)."""
        if row_count <= 0 or col_count <= 0:
            return

        table_range = {
            "sheetId": sheet_id,
            "startRowIndex": 0,
            "endRowIndex": row_count,
            "startColumnIndex": 0,
            "endColumnIndex": col_count,
        }

        self._svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": sheet_id,
                                "gridProperties": {"frozenRowCount": 1},
                            },
                            "fields": "gridProperties.frozenRowCount",
                        }
                    },
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": col_count,
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {
                                        "red": 0.86,
                                        "green": 0.9,
                                        "blue": 0.98,
                                    },
                                    "textFormat": {
                                        "bold": True,
                                    },
                                }
                            },
                            "fields": "userEnteredFormat(backgroundColor,textFormat.bold)",
                        }
                    },
                    {
                        "setBasicFilter": {
                            "filter": {
                                "range": table_range,
                            }
                        }
                    },
                    {
                        "addBanding": {
                            "bandedRange": {
                                "range": table_range,
                                "rowProperties": {
                                    "headerColor": {
                                        "red": 0.86,
                                        "green": 0.9,
                                        "blue": 0.98,
                                    },
                                    "firstBandColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0,
                                    },
                                    "secondBandColor": {
                                        "red": 0.96,
                                        "green": 0.97,
                                        "blue": 0.99,
                                    },
                                },
                            }
                        }
                    },
                ]
            },
        ).execute()

    def apply_dropdown(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        col_start: int,
        col_end: int,
        options: list[str],
    ) -> None:
        """Apply a one-of-list dropdown validation to a column range."""
        self._svc.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "setDataValidation": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": start_row,
                                "endRowIndex": end_row,
                                "startColumnIndex": col_start,
                                "endColumnIndex": col_end,
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_LIST",
                                    "values": [
                                        {"userEnteredValue": o} for o in options
                                    ],
                                },
                                "showCustomUi": True,
                                "strict": True,
                            },
                        }
                    }
                ]
            },
        ).execute()
