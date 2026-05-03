from __future__ import annotations

from .models import DROPDOWN_COL_END, DROPDOWN_COL_START, DROPDOWN_OPTIONS, HEADERS, SheetEvent
from .sheets import SheetsClient


def event_to_spreadsheet(
    event: SheetEvent,
    client: SheetsClient,
    spreadsheet_title: str | None = None,
) -> str:
    """Create a Google Spreadsheet from a SheetEvent. Returns the spreadsheet ID."""
    if not event.competitions:
        raise ValueError("Event has no competitions to export.")

    title = spreadsheet_title or f"RCE Event {event.event_id}"
    first_comp = event.competitions[0]

    spreadsheet_id, first_sheet_id = client.create_spreadsheet(
        title, first_comp.sheet_title
    )
    sheet_ids: dict[str, int] = {first_comp.competition_id: first_sheet_id}

    for comp in event.competitions[1:]:
        sheet_id = client.add_sheet(spreadsheet_id, comp.sheet_title)
        sheet_ids[comp.competition_id] = sheet_id

    for comp in event.competitions:
        rows = [HEADERS] + [bot.to_row() for bot in comp.bots]
        client.write_rows(spreadsheet_id, comp.sheet_title, rows)
        client.format_as_table(
            spreadsheet_id,
            sheet_ids[comp.competition_id],
            row_count=len(rows),
            col_count=len(HEADERS),
        )
        if comp.bots:
            client.apply_dropdown(
                spreadsheet_id,
                sheet_ids[comp.competition_id],
                start_row=1,
                end_row=1 + len(comp.bots),
                col_start=DROPDOWN_COL_START,
                col_end=DROPDOWN_COL_END,
                options=DROPDOWN_OPTIONS,
            )

    return spreadsheet_id
