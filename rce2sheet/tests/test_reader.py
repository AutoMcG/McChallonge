"""Unit tests for rce2sheet reader (sheet → approved participants JSON)."""
from __future__ import annotations

import json
import tempfile
from unittest.mock import MagicMock

from rce2sheet.reader import (
    ApprovedParticipant,
    ApprovedParticipantList,
    _is_yes,
    _spreadsheet_id_from_url,
    read_approved_participants,
)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/abc123XYZ/edit#gid=0"

# Rows: [image_url, bot_name, team_name, status, passed_weight, passed_safety, paid]
_HEADER = ["Image URL", "Bot Name", "Team Name", "Status", "Passed Weight", "Passed Safety", "Paid"]
_ALL_YES = ["https://img/a.png", "Crusher", "Team Alpha", "Registered", "Yes", "Yes", "Yes"]
_ONLY_WEIGHT_YES = ["", "Spinner", "Team B", "Registered", "Yes", "No", "No"]
_ALL_YES_2 = ["", "Smasher", "Team C", "Registered", "Yes", "Yes", "Yes"]


def _make_mock_client(sheets_data: dict[str, list[list]]) -> MagicMock:
    """Build a mock SheetsClient that returns given row data per sheet title."""
    client = MagicMock()
    sheet_titles = list(sheets_data.keys())

    client._svc.spreadsheets().get().execute.return_value = {
        "sheets": [{"properties": {"title": t}} for t in sheet_titles]
    }

    def values_get_side_effect(**kwargs):
        title = kwargs["range"].strip("'")
        rows = sheets_data.get(title, [])
        mock = MagicMock()
        mock.execute.return_value = {"values": rows}
        return mock

    client._svc.spreadsheets().values().get.side_effect = values_get_side_effect
    return client


def test_spreadsheet_id_from_url():
    assert _spreadsheet_id_from_url(SPREADSHEET_URL) == "abc123XYZ"


def test_spreadsheet_id_from_url_raises_on_bad_url():
    try:
        _spreadsheet_id_from_url("https://example.com/notasheeturl")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_is_yes():
    assert _is_yes("Yes")
    assert _is_yes("yes")
    assert _is_yes(" YES ")
    assert not _is_yes("No")
    assert not _is_yes("")
    assert not _is_yes(None)


def test_read_approved_participants_filters_correctly():
    client = _make_mock_client({
        "Featherweight": [_HEADER, _ALL_YES, _ONLY_WEIGHT_YES, _ALL_YES_2],
    })
    result = read_approved_participants(SPREADSHEET_URL, client)
    assert result.spreadsheet_id == "abc123XYZ"
    assert len(result.competitions) == 1
    comp = result.competitions[0]
    assert comp.sheet_title == "Featherweight"
    assert len(comp.approved_participants) == 2
    names = [p.bot_name for p in comp.approved_participants]
    assert "Crusher" in names
    assert "Smasher" in names
    assert "Spinner" not in names


def test_read_approved_participants_multiple_sheets():
    client = _make_mock_client({
        "Featherweight": [_HEADER, _ALL_YES],
        "Beetleweight": [_HEADER, _ONLY_WEIGHT_YES],
        "Antweight": [_HEADER, _ALL_YES_2],
    })
    result = read_approved_participants(SPREADSHEET_URL, client)
    assert len(result.competitions) == 3
    feather = next(c for c in result.competitions if c.sheet_title == "Featherweight")
    assert len(feather.approved_participants) == 1
    beetle = next(c for c in result.competitions if c.sheet_title == "Beetleweight")
    assert len(beetle.approved_participants) == 0
    ant = next(c for c in result.competitions if c.sheet_title == "Antweight")
    assert len(ant.approved_participants) == 1


def test_read_approved_participants_pads_short_rows():
    """Rows shorter than 7 cols should be padded and not crash."""
    short_row = ["", "ShortBot", "Team S"]  # no status or dropdown cols
    client = _make_mock_client({"Misc": [_HEADER, short_row]})
    result = read_approved_participants(SPREADSHEET_URL, client)
    assert result.competitions[0].approved_participants == []


def test_approved_participant_list_round_trip_json():
    original = ApprovedParticipantList(
        spreadsheet_id="abc",
        competitions=[],
    )
    original.competitions.append(
        __import__("rce2sheet.reader", fromlist=["ApprovedCompetition"]).ApprovedCompetition(
            sheet_title="Test",
            approved_participants=[ApprovedParticipant(bot_name="Bot", team_name="Team")],
        )
    )
    restored = ApprovedParticipantList.from_dict(json.loads(original.to_json()))
    assert restored.spreadsheet_id == "abc"
    assert len(restored.competitions) == 1
    assert restored.competitions[0].approved_participants[0].bot_name == "Bot"


def test_approved_participant_list_from_json_file():
    data = {
        "spreadsheet_id": "xyz",
        "competitions": [
            {"sheet_title": "FW", "approved_participants": [{"bot_name": "A", "team_name": None, "image_url": None}]},
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    result = ApprovedParticipantList.from_json_file(path)
    assert result.spreadsheet_id == "xyz"
    assert result.competitions[0].approved_participants[0].bot_name == "A"
