import requests
import copy

from ..models.tournament import Tournament
from ..models.participant import Participant
from ..models.match import Match

from ..services import challonging

from typing import List

def count_outcomes(matches: List[Match], pilots: List[Participant]) -> List[Participant]:
    # Convert the list of pilots to a dictionary for faster lookup
    pilot_dict = {pilot.id: pilot for pilot in pilots}

    # Filter out the completed matches
    complete_matches = [match for match in matches if match.state == "complete"]

    def update_dict(winner, loser):
        # Only update wins if winner_id is valid and in our participants
        if winner and winner in pilot_dict:
            pilot_dict[winner].wins += 1
        
        # Only update losses if loser_id is valid and in our participants
        if loser and loser in pilot_dict:
            pilot_dict[loser].losses += 1

    # Process each match to update wins/losses
    for match in complete_matches:
        if hasattr(match, 'loser_id'):
            loser_id = match.loser_id
        else:
            # Determine loser_id from player IDs and winner_id
            if match.winner_id == match.player1_id:
                loser_id = match.player2_id
            elif match.winner_id == match.player2_id:
                loser_id = match.player1_id
            else:
                loser_id = None
        
        update_dict(match.winner_id, loser_id)

    return list(pilot_dict.values())