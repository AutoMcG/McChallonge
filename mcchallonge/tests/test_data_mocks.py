class ChallongeMocks:
    """Mock responses for Challonge API testing"""
    
    TOURNAMENT_LIST_RESPONSE = [
        {
            "tournament": {
                "id": 1,
                "name": "Test Tournament",
                "url": "test_tourney",
                "state": "in_progress",
                "started_at": "2023-10-18T10:00:00.000Z",
                "completed_at": None
            }
        }
    ]

    SINGLE_TOURNAMENT_RESPONSE = {
        "tournament": {
            "id": 1,
            "name": "Test Tournament",
            "url": "test_tourney",
            "state": "in_progress",
            "started_at": "2023-10-18T10:00:00.000Z",
            "completed_at": None
        }
    }

    PARTICIPANTS_RESPONSE = [
        {
            "participant": {
                "id": 1,
                "name": "Test Pilot 1",
                "wins": 2,
                "losses": 1
            }
        },
        {
            "participant": {
                "id": 2,
                "name": "Test Pilot 2",
                "wins": 1,
                "losses": 2
            }
        }
    ]

    MATCHES_RESPONSE = [
        {
            "match": {
                "id": 1,
                "state": "complete",
                "player1_id": 1,
                "player2_id": 2,
                "winner_id": 1,
                "loser_id": 2,
                "scheduled_time": "2023-10-18T11:00:00.000Z",
                "completed_at": "2023-10-18T11:30:00.000Z"
            }
        }
    ]

class ThinkServiceMocks:
    """Mock data for testing the think service"""
    
    PILOT_LIST = [
        {
            "id": 1,
            "name": "Test Pilot 1",
            "wins": 0,
            "losses": 0
        },
        {
            "id": 2,
            "name": "Test Pilot 2",
            "wins": 0,
            "losses": 0
        }
    ]

    MATCH_LIST = [
        {
            "id": 1,
            "state": "complete",
            "player1_id": 1,
            "player2_id": 2,
            "winner_id": 1,
            "loser_id": 2
        }
    ]

class TemplaterMocks:
    """Mock data for testing the templater service"""
    
    TABLE_DATA = {
        "title": "Test Tournament Results",
        "schema": ["Name", "Wins", "Losses"],
        "pilots": [
            {"name": "Test Pilot 1", "wins": 2, "losses": 1},
            {"name": "Test Pilot 2", "wins": 1, "losses": 2}
        ]
    }