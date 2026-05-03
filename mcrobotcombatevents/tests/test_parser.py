from mcrobotcombatevents.parser import parse_competition_links, parse_competition_page


def test_parse_competition_links_extracts_unique_event_links():
    event_html = """
    <html>
      <body>
        <a href="/events/7187/competitions/12345">Comp A</a>
        <a href="https://www.robotcombatevents.com/events/7187/competitions/12346?tab=teams">Comp B</a>
        <a href="/events/7187/competitions/12345#details">Comp A duplicate</a>
        <a href="/events/9000/competitions/99999">Other event</a>
      </body>
    </html>
    """

    links = parse_competition_links(
        event_id=7187,
        event_html=event_html,
        base_url="https://www.robotcombatevents.com",
    )

    assert links == [
        "https://www.robotcombatevents.com/events/7187/competitions/12345",
        "https://www.robotcombatevents.com/events/7187/competitions/12346",
    ]


def test_parse_competition_page_extracts_robot_rows():
    competition_html = """
    <html>
      <head><title>Featherweight Division</title></head>
      <body>
        <div class="info-panel-subtitle"><p>Featherweight Division</p></div>
        <table>
          <thead>
            <tr>
              <th>Image</th>
              <th>Robot</th>
              <th>Team</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><img src="/images/bot1.png" /></td>
              <td>Hammer Time</td>
              <td>Team Steel</td>
              <td>Registered</td>
            </tr>
            <tr>
              <td><img src="https://cdn.example.com/bot2.jpg" /></td>
              <td>Spin Doctor</td>
              <td>Team Torque</td>
              <td>Waitlist</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    competition = parse_competition_page(
        "https://www.robotcombatevents.com/events/7187/competitions/445566",
        competition_html,
    )

    assert competition.competition_id == "445566"
    assert competition.competition_name == "Featherweight Division"
    assert len(competition.bots) == 2

    assert competition.bots[0].image_url == "https://www.robotcombatevents.com/images/bot1.png"
    assert competition.bots[0].bot_name == "Hammer Time"
    assert competition.bots[0].team_name == "Team Steel"
    assert competition.bots[0].status == "Registered"
