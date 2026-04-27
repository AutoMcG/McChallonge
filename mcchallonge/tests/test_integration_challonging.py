import os
import pytest
import requests
from dotenv import load_dotenv
from mcchallonge.services import challonging
from mcchallonge.models.tournament import Tournament
from mcchallonge.models.participant import Participant
from mcchallonge.models.match import Match

load_dotenv()

# All tests in this module require live Challonge credentials and are excluded
# from the default test run.  Run them explicitly with: pytest -m integration
pytestmark = pytest.mark.integration


def _get_credentials():
    """Return (user, key) or skip the test if credentials are not available."""
    user = os.environ.get("challonge_user")
    key = os.environ.get("challonge_key")
    if not user or not key:
        pytest.skip("challonge_user and challonge_key must be set in environment")
    return user, key


class IntegrationTestChallonging:
    def test_real_prepare_session(self):
        user, key = _get_credentials()
        session = challonging.prepare_session(user, key)
        assert isinstance(session, requests.Session)

    def test_get_tournaments_real(self):
        user, key = _get_credentials()
        session = challonging.prepare_session(user, key)
        tournaments = challonging.get_tournaments(session)
        assert isinstance(tournaments, list)
        assert all(isinstance(t, Tournament) for t in tournaments)
        if tournaments:
            print(f"First tournament: {tournaments[0]}")

    def test_get_tournament_data_real(self):
        user, key = _get_credentials()
        session = challonging.prepare_session(user, key)
        tournaments = challonging.get_tournaments(session)
        if not tournaments:
            pytest.skip("No tournaments available for integration test")
        tournament_id = tournaments[0].id
        tournament = challonging.get_tournament_data(session, tournament_id)
        assert isinstance(tournament, Tournament)
        print(f"Tournament: {tournament}")

    def test_get_participants_data_real(self):
        user, key = _get_credentials()
        session = challonging.prepare_session(user, key)
        tournaments = challonging.get_tournaments(session)
        if not tournaments:
            pytest.skip("No tournaments available for integration test")
        tournament_id = tournaments[0].id
        participants = challonging.get_participants_data(session, tournament_id)
        assert isinstance(participants, list)
        assert all(isinstance(p, Participant) for p in participants)
        if participants:
            print(f"First participant: {participants[0]}")

    def test_get_match_data_real(self):
        user, key = _get_credentials()
        session = challonging.prepare_session(user, key)
        tournaments = challonging.get_tournaments(session)
        if not tournaments:
            pytest.skip("No tournaments available for integration test")
        tournament_id = tournaments[0].id
        matches = challonging.get_match_data(session, tournament_id)
        assert isinstance(matches, list)
        assert all(isinstance(m, Match) for m in matches)
        if matches:
            print(f"First match: {matches[0]}")
