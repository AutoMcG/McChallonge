"""
Test cases for the CLI dashboard generator
"""
import os
import json
import tempfile
import subprocess
import pytest
from unittest.mock import patch

from ..models.tournament import Tournament
from ..models.participant import Participant
from ..models.match import Match
from ..services.static_generator import generate_static_tournament_page

# Sample data for testing
SAMPLE_TOURNAMENT = {
    "id": 12345,
    "name": "Test Tournament",
    "url": "test_tournament",
    "state": "complete",
    "started_at": "2023-10-15T10:00:00",
    "completed_at": "2023-10-15T18:00:00"
}

SAMPLE_PARTICIPANTS = [
    {
        "id": 101,
        "name": "Player 1",
        "tournament_id": 12345,
        "wins": 0,
        "losses": 0
    },
    {
        "id": 102,
        "name": "Player 2",
        "tournament_id": 12345,
        "wins": 0,
        "losses": 0
    },
    {
        "id": 103,
        "name": "Player 3",
        "tournament_id": 12345,
        "wins": 0,
        "losses": 0
    }
]

SAMPLE_MATCHES = [
    {
        "id": 201,
        "tournament_id": 12345,
        "player1_id": 101,
        "player2_id": 102,
        "winner_id": 101,
        "state": "complete",
        "completed_at": "2023-10-15T11:00:00"
    },
    {
        "id": 202,
        "tournament_id": 12345,
        "player1_id": 101,
        "player2_id": 103,
        "winner_id": 101,
        "state": "complete",
        "completed_at": "2023-10-15T12:00:00"
    },
    {
        "id": 203,
        "tournament_id": 12345,
        "player1_id": 102,
        "player2_id": 103,
        "winner_id": 102,
        "state": "complete",
        "completed_at": "2023-10-15T13:00:00"
    }
]

def create_test_files(temp_dir):
    """Create test JSON files in the given directory"""
    tournament_file = os.path.join(temp_dir, "tournament.json")
    participants_file = os.path.join(temp_dir, "participants.json")
    matches_file = os.path.join(temp_dir, "matches.json")
    
    with open(tournament_file, 'w') as f:
        json.dump(SAMPLE_TOURNAMENT, f)
    
    with open(participants_file, 'w') as f:
        json.dump(SAMPLE_PARTICIPANTS, f)
        
    with open(matches_file, 'w') as f:
        json.dump(SAMPLE_MATCHES, f)
        
    return tournament_file, participants_file, matches_file

def test_cli_generate_dashboard():
    """Test the CLI dashboard generator with offline JSON files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test JSON files
        tournament_file, participants_file, matches_file = create_test_files(temp_dir)
        output_file = os.path.join(temp_dir, "test_dashboard.html")
        participants_page = os.path.join(temp_dir, "participants")
        matches_page = os.path.join(temp_dir, "matches")
        
        # Run the CLI tool using subprocess to capture return code
        cmd = [
            "python", "-m", "mcchallonge.cli.generate_dashboard",
            "test_tournament",
            "--offline",
            "--tournament-file", tournament_file,
            "--participants-file", participants_file,
            "--matches-file", matches_file,
            "-o", output_file
        ]
        
        # Run the command and verify it succeeds
        process = subprocess.run(cmd, capture_output=True, text=True)
        assert process.returncode == 0, f"Command failed with error: {process.stderr}"
        
        # Check if the output file was created
        assert os.path.exists(output_file), "Output HTML file was not created"
        assert os.path.exists(participants_page), "Participants page was not created"
        assert os.path.exists(matches_page), "Matches page was not created"
        
        # Check file contents for expected elements
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for required elements in HTML output
            assert "Test Tournament" in content, "Tournament name not found in output"
            assert "Player 1" in content, "Player 1 not found in output"
            assert "Player 2" in content, "Player 2 not found in output"
            assert "Player 3" in content, "Player 3 not found in output"

        with open(participants_page, 'r', encoding='utf-8') as f:
            participants_content = f.read()
            assert "Test Tournament - Participants" in participants_content
            assert "./static/css/bootstrap.min.css" in participants_content
            assert "href=\"./matches\"" in participants_content

        with open(matches_page, 'r', encoding='utf-8') as f:
            matches_content = f.read()
            assert "Test Tournament - Matches" in matches_content
            assert "./static/js/bootstrap.bundle.min.js" in matches_content
            assert "href=\"./participants\"" in matches_content

def test_static_generator_direct():
    """Test the static generator function directly without CLI"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create objects from sample data
        tournament = Tournament.from_dict(SAMPLE_TOURNAMENT)
        participants = [Participant.from_dict(p) for p in SAMPLE_PARTICIPANTS]
        matches = [Match.from_dict(m) for m in SAMPLE_MATCHES]
        
        output_file = os.path.join(temp_dir, "direct_dashboard.html")
        participants_page = os.path.join(temp_dir, "participants")
        matches_page = os.path.join(temp_dir, "matches")
        
        # Call the function directly
        generate_static_tournament_page(tournament, participants, matches, output_file)
        
        # Verify the output was created
        assert os.path.exists(output_file), "Output HTML file was not created"
        assert os.path.exists(participants_page), "Participants page was not created"
        assert os.path.exists(matches_page), "Matches page was not created"
        
        # Check content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "<title>Test Tournament</title>" in content
            assert "Player 1" in content
            assert "Player 2" in content
            assert "Player 3" in content


@patch("mcchallonge.cli.generate_dashboard.get_match_data")
@patch("mcchallonge.cli.generate_dashboard.get_participants_data")
@patch("mcchallonge.cli.generate_dashboard.get_tournament_data")
@patch("mcchallonge.cli.generate_dashboard.prepare_session_from_env")
def test_cli_generate_dashboard_writes_json_artifacts(
    mock_prepare_session,
    mock_get_tournament_data,
    mock_get_participants_data,
    mock_get_match_data,
):
    """Test that live-mode CLI generation writes JSON artifacts next to the dashboard."""
    mock_prepare_session.return_value = object()
    mock_get_tournament_data.return_value = Tournament.from_dict(SAMPLE_TOURNAMENT)
    mock_get_participants_data.return_value = [Participant.from_dict(participant) for participant in SAMPLE_PARTICIPANTS]
    mock_get_match_data.return_value = [Match.from_dict(match) for match in SAMPLE_MATCHES]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "generated_dashboard.html")

        with patch("sys.argv", [
            "generate_dashboard",
            "test_tournament",
            "-o",
            output_file,
        ]):
            from ..cli.generate_dashboard import main

            main()

        tournament_json = os.path.join(temp_dir, "tournament.json")
        participants_json = os.path.join(temp_dir, "participants.json")
        matches_json = os.path.join(temp_dir, "matches.json")

        assert os.path.exists(output_file), "Output HTML file was not created"
        assert os.path.exists(tournament_json), "Tournament JSON file was not created"
        assert os.path.exists(participants_json), "Participants JSON file was not created"
        assert os.path.exists(matches_json), "Matches JSON file was not created"

        with open(tournament_json, 'r', encoding='utf-8') as handle:
            assert json.load(handle)["name"] == "Test Tournament"

        with open(participants_json, 'r', encoding='utf-8') as handle:
            participants = json.load(handle)
            assert [participant["name"] for participant in participants] == ["Player 1", "Player 2", "Player 3"]

        with open(matches_json, 'r', encoding='utf-8') as handle:
            matches = json.load(handle)
            assert [match["id"] for match in matches] == [201, 202, 203]

if __name__ == "__main__":
    # Allow running this test directly for debugging
    test_cli_generate_dashboard()
    test_static_generator_direct()
    print("All tests passed!")