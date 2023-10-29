import requests
import copy

from ..models.tournament import Tournament
from ..models.pilot import Pilot
from ..models.match import Match

from ..services import challonging

from typing import List

def count_outcomes(matches: List[Match], pilots: List[Pilot]) -> List[Pilot]:
    # convert the list of pilots to a dictionary for faster lookup
    pilot_dict = {pilot.id: pilot for pilot in pilots}

    # filter out the completed matches
    complete_matches = [match for match in matches if match.state == "complete"]

    def update_dict(winner, loser):        
        pilot_dict[winner].wins += 1
        pilot_dict[loser].losses += 1

    [update_dict(match.winner_id, match.loser_id) for match in complete_matches]

    return list(pilot_dict.values())