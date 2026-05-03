import json
import tempfile
from argparse import Namespace
from unittest.mock import MagicMock

from rce2sheet.models import HEADERS, SheetBot, SheetEvent
from rce2sheet.workflow import event_to_spreadsheet
import rce2sheet.cli as cli


SAMPLE_EVENT_DICT = {
    "event_id": 7187,
    "event_url": "https://www.robotcombatevents.com/events/7187",
    "competitions": [
        {
            "competition_id": "101",
            "competition_url": "https://www.robotcombatevents.com/events/7187/competitions/101",
            "competition_name": "Featherweight",
            "bots": [
                {
                    "image_url": "https://example.com/bot1.png",
                    "bot_name": "Crusher",
                    "team_name": "Team Alpha",
                    "status": "Registered",
                }
            ],
        },
        {
            "competition_id": "102",
            "competition_url": "https://www.robotcombatevents.com/events/7187/competitions/102",
            "competition_name": "Beetleweight",
            "bots": [
                {
                    "image_url": None,
                    "bot_name": "Spin Doctor",
                    "team_name": "Team Beta",
                    "status": "Waitlist",
                }
            ],
        },
    ],
}


def test_sheet_event_from_dict():
    event = SheetEvent.from_dict(SAMPLE_EVENT_DICT)
    assert event.event_id == 7187
    assert len(event.competitions) == 2
    assert event.competitions[0].competition_name == "Featherweight"
    assert event.competitions[0].sheet_title == "Featherweight"
    assert len(event.competitions[0].bots) == 1
    assert event.competitions[0].bots[0].bot_name == "Crusher"
    assert event.competitions[1].competition_name == "Beetleweight"


def test_sheet_competition_sheet_title_falls_back_to_id():
    event = SheetEvent.from_dict(
        {
            "event_id": 1,
            "competitions": [
                {"competition_id": "99", "competition_name": None, "bots": []}
            ],
        }
    )
    assert event.competitions[0].sheet_title == "99"


def test_sheet_bot_to_row_matches_headers():
    bot = SheetBot(
        image_url="https://img.com/a.png",
        bot_name="Crusher",
        team_name="Team Alpha",
        status="Registered",
    )
    row = bot.to_row()
    assert row == ["https://img.com/a.png", "Crusher", "Team Alpha", "Registered", "", "", ""]
    assert len(row) == len(HEADERS)


def test_sheet_bot_to_row_handles_none_fields():
    row = SheetBot().to_row()
    assert row == ["", "", "", "", "", "", ""]


def test_sheet_event_from_json_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(SAMPLE_EVENT_DICT, f)
        path = f.name
    event = SheetEvent.from_json_file(path)
    assert event.event_id == 7187
    assert len(event.competitions) == 2


def test_event_to_spreadsheet_api_calls():
    mock_client = MagicMock()
    mock_client.create_spreadsheet.return_value = ("sheet_abc", 0)
    mock_client.add_sheet.return_value = 1

    event = SheetEvent.from_dict(SAMPLE_EVENT_DICT)
    spreadsheet_id = event_to_spreadsheet(event, mock_client, spreadsheet_title="Test Event")

    assert spreadsheet_id == "sheet_abc"

    mock_client.create_spreadsheet.assert_called_once_with("Test Event", "Featherweight")
    mock_client.add_sheet.assert_called_once_with("sheet_abc", "Beetleweight")

    assert mock_client.write_rows.call_count == 2
    first_write_rows = mock_client.write_rows.call_args_list[0]
    rows_written = first_write_rows.args[2]
    assert rows_written[0] == HEADERS
    assert rows_written[1][1] == "Crusher"

    assert mock_client.format_as_table.call_count == 2
    first_table_call = mock_client.format_as_table.call_args_list[0]
    assert first_table_call.kwargs["row_count"] == 2
    assert first_table_call.kwargs["col_count"] == len(HEADERS)

    assert mock_client.apply_dropdown.call_count == 2
    first_dropdown_call = mock_client.apply_dropdown.call_args_list[0]
    assert first_dropdown_call.kwargs["options"] == ["Yes", "No"]
    assert first_dropdown_call.kwargs["start_row"] == 1
    assert first_dropdown_call.kwargs["end_row"] == 2
    assert first_dropdown_call.kwargs["col_start"] == 4
    assert first_dropdown_call.kwargs["col_end"] == 7


def test_event_to_spreadsheet_skips_dropdown_for_empty_bot_lists():
    mock_client = MagicMock()
    mock_client.create_spreadsheet.return_value = ("sheet_abc", 0)

    event = SheetEvent.from_dict(
        {
            "event_id": 7187,
            "competitions": [
                {
                    "competition_id": "101",
                    "competition_name": "Featherweight",
                    "bots": [],
                }
            ],
        }
    )

    spreadsheet_id = event_to_spreadsheet(event, mock_client)

    assert spreadsheet_id == "sheet_abc"
    mock_client.write_rows.assert_called_once()
    mock_client.format_as_table.assert_called_once()
    mock_client.apply_dropdown.assert_not_called()


def test_event_to_spreadsheet_raises_on_empty_competitions():
    mock_client = MagicMock()
    event = SheetEvent(event_id=1, competitions=[])
    try:
        event_to_spreadsheet(event, mock_client)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_cli_uses_user_oauth_when_provided(monkeypatch):
    parser_mock = MagicMock()
    parser_mock.parse_args.return_value = Namespace(
        event_json="event.json",
        credentials=None,
        oauth_client_secrets="client_secret.json",
        oauth_token="token.json",
        title="Event Title",
    )
    monkeypatch.setattr(cli, "build_parser", lambda: parser_mock)

    event = SheetEvent.from_dict(SAMPLE_EVENT_DICT)
    from_json_mock = MagicMock(return_value=event)
    monkeypatch.setattr(cli.SheetEvent, "from_json_file", from_json_mock)

    oauth_client = MagicMock()
    oauth_ctor = MagicMock(return_value=oauth_client)
    svc_ctor = MagicMock()
    monkeypatch.setattr(cli.SheetsClient, "from_user_oauth", oauth_ctor)
    monkeypatch.setattr(cli.SheetsClient, "from_credentials_file", svc_ctor)

    export_mock = MagicMock(return_value="spreadsheet_123")
    monkeypatch.setattr(cli, "event_to_spreadsheet", export_mock)

    exit_code = cli.main()

    assert exit_code == 0
    oauth_ctor.assert_called_once_with("client_secret.json", token_path="token.json")
    svc_ctor.assert_not_called()
    export_mock.assert_called_once_with(event, oauth_client, spreadsheet_title="Event Title")


def test_cli_uses_service_account_when_oauth_not_provided(monkeypatch):
    parser_mock = MagicMock()
    parser_mock.parse_args.return_value = Namespace(
        event_json="event.json",
        credentials="svc.json",
        oauth_client_secrets=None,
        oauth_token="rce2sheet_token.json",
        title=None,
    )
    monkeypatch.setattr(cli, "build_parser", lambda: parser_mock)

    event = SheetEvent.from_dict(SAMPLE_EVENT_DICT)
    from_json_mock = MagicMock(return_value=event)
    monkeypatch.setattr(cli.SheetEvent, "from_json_file", from_json_mock)

    svc_client = MagicMock()
    svc_ctor = MagicMock(return_value=svc_client)
    oauth_ctor = MagicMock()
    monkeypatch.setattr(cli.SheetsClient, "from_credentials_file", svc_ctor)
    monkeypatch.setattr(cli.SheetsClient, "from_user_oauth", oauth_ctor)

    export_mock = MagicMock(return_value="spreadsheet_123")
    monkeypatch.setattr(cli, "event_to_spreadsheet", export_mock)

    exit_code = cli.main()

    assert exit_code == 0
    svc_ctor.assert_called_once_with("svc.json")
    oauth_ctor.assert_not_called()
    export_mock.assert_called_once_with(event, svc_client, spreadsheet_title=None)


def test_cli_requires_auth_arguments(monkeypatch, capsys):
    parser_mock = MagicMock()
    parser_mock.parse_args.return_value = Namespace(
        event_json="event.json",
        credentials=None,
        oauth_client_secrets=None,
        oauth_token="rce2sheet_token.json",
        title=None,
    )
    monkeypatch.setattr(cli, "build_parser", lambda: parser_mock)

    event = SheetEvent.from_dict(SAMPLE_EVENT_DICT)
    monkeypatch.setattr(cli.SheetEvent, "from_json_file", MagicMock(return_value=event))

    exit_code = cli.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Google auth required" in captured.out
