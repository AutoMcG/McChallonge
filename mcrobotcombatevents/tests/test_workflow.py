import json

from mcrobotcombatevents.workflow import event_to_json, scrape_event


class FakeClient:
    BASE_URL = "https://www.robotcombatevents.com"

    def __init__(self, html_by_url: dict[str, str]):
        self.html_by_url = html_by_url

    def event_url(self, event_id: int) -> str:
        return f"{self.BASE_URL}/events/{event_id}"

    def get_event_html(self, event_id: int) -> str:
        return self.html_by_url[self.event_url(event_id)]

    def get_competition_html(self, competition_url: str) -> str:
        return self.html_by_url[competition_url]


def test_scrape_event_builds_nested_dataclasses():
    event_id = 7187
    event_url = f"https://www.robotcombatevents.com/events/{event_id}"
    comp_url = f"https://www.robotcombatevents.com/events/{event_id}/competitions/1001"

    html_by_url = {
        event_url: """
        <a href=\"/events/7187/competitions/1001\">Main Competition</a>
        """,
        comp_url: """
        <div class="info-panel-subtitle"><p>Main Competition</p></div>
        <table>
          <tr><th>Image</th><th>Robot</th><th>Team</th><th>Status</th></tr>
          <tr><td><img src=\"/img/bot.png\"></td><td>Crusher</td><td>Team Alpha</td><td>Registered</td></tr>
        </table>
        """,
    }

    event = scrape_event(event_id=event_id, client=FakeClient(html_by_url))

    assert event.event_id == event_id
    assert event.event_url == event_url
    assert len(event.competitions) == 1
    assert event.competitions[0].competition_id == "1001"
    assert len(event.competitions[0].bots) == 1
    assert event.competitions[0].bots[0].bot_name == "Crusher"

    payload = json.loads(event_to_json(event))
    assert payload["event_id"] == event_id
    assert payload["competitions"][0]["bots"][0]["team_name"] == "Team Alpha"
