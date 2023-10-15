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

    # iterae over the completed matches and update the win/loss counts
    for match in complete_matches:
        winner = match.winner_id
        loser = match.loser_id

        # update win/loss counts
        pilot_dict[winner].wins += 1
        pilot_dict[loser].losses += 1

    # optionally? convert the dictionary back to a list if needed
    updated_pilots = list(pilot_dict.values())

    return updated_pilots
