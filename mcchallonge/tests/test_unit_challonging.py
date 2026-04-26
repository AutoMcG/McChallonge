import json
import logging
import os
import pytest
from unittest.mock import patch, MagicMock
import requests
from requests_oauthlib import OAuth2Session

from ..services import challonging
from ..models.tournament import Tournament
from ..models.participant import Participant
from ..models.match import Match
from .test_data_mocks import ChallongeMocks

logger = logging.getLogger(__name__)

class UnitTestChallonging:
    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=requests.Session)

    def test_prepare_session(self):
        """Test session preparation with user and key"""
        user = "testuser"
        key = "testkey"
        session = challonging.prepare_session(user, key)
        
        assert isinstance(session, requests.Session)
        assert session.auth == (user, key)
        assert session.headers["User-Agent"] == "McChallonger"
        assert session.headers["Accept"] == "application/json"

    def test_prepare_session_from_env(self, monkeypatch):
        """Test session preparation from environment variables"""
        monkeypatch.setenv("challonge_user", "envuser")
        monkeypatch.setenv("challonge_key", "envkey")
        
        session = challonging.prepare_session_from_env()
        
        assert isinstance(session, requests.Session)
        assert session.auth == ("envuser", "envkey")

    def test_get_tournaments(self, mock_session):
        """Test getting tournaments list"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ChallongeMocks.TOURNAMENT_LIST_RESPONSE
        
        # Configure mock session
        mock_session.send.return_value = mock_response

        tournaments = challonging.get_tournaments(mock_session)
        
        assert len(tournaments) == 1
        assert isinstance(tournaments[0], Tournament)
        assert tournaments[0].id == 1
        assert tournaments[0].name == "Test Tournament"
        mock_session.prepare_request.assert_called_once()

    def test_get_tournament_data(self, mock_session):
        """Test getting single tournament data"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ChallongeMocks.SINGLE_TOURNAMENT_RESPONSE
        
        # Configure mock session
        mock_session.get.return_value = mock_response

        tournament = challonging.get_tournament_data(mock_session, "test-id")
        
        assert isinstance(tournament, Tournament)
        assert tournament.id == 1
        assert tournament.name == "Test Tournament"
        assert tournament.url == "test_tourney"
        mock_session.get.assert_called_once()

    def test_get_participants_data(self, mock_session):
        """Test getting participants data"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ChallongeMocks.PARTICIPANTS_RESPONSE
        
        # Configure mock session
        mock_session.get.return_value = mock_response

        pilots = challonging.get_participants_data(mock_session, "test-id")
        
        assert len(pilots) == 2
        assert isinstance(pilots[0], Participant)
        assert pilots[0].id == 1
        assert pilots[0].name == "Test Pilot 1"
        assert pilots[0].wins == 2
        mock_session.get.assert_called_once()

    def test_get_match_data(self, mock_session):
        """Test getting match data"""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ChallongeMocks.MATCHES_RESPONSE
        
        # Configure mock session
        mock_session.get.return_value = mock_response

        matches = challonging.get_match_data(mock_session, "test-id")
        
        assert len(matches) == 1
        assert isinstance(matches[0], Match)
        assert matches[0].id == 1
        assert matches[0].state == "complete"
        assert matches[0].winner_id == 1
        mock_session.get.assert_called_once()

    def test_prepare_oauth_session(self, monkeypatch):
        """Test OAuth session preparation"""
        monkeypatch.setenv("CHALLONGE_CLIENT_ID", "test_id")
        monkeypatch.setenv("CHALLONGE_CLIENT_SECRET", "test_secret")
        
        with patch("mcchallonge.services.challonging.get_challonge_oauth_session") as mock_oauth:
            mock_oauth.return_value = MagicMock(spec=OAuth2Session)
            session = challonging.prepare_oauth_session()
            
            assert isinstance(session, OAuth2Session)
            mock_oauth.assert_called_once()
