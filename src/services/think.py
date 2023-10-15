import requests
import copy

from ..models.tournament import Tournament
from ..models.pilot import Pilot
from ..models.match import Match

from ..services import challonging

def count_outcomes(matches: [Match], pilots: [Pilot]) -> [Pilot]:
    pilot_outcomes = copy.deepcopy(pilots)    
    #get matches that are complete
    complete_matches = [match for match in matches if match.state == "complete"]
    #iterate over matches, hit pilot array for each record    
    for match in complete_matches:
        winner = match.winner_id
        loser = match.loser_id
        pilot_winner = next((pilot for pilot in pilot_outcomes if pilot.id == winner), None)
        pilot_loser = next((pilot for pilot in pilot_outcomes if pilot.id == loser), None)
        pilot_winner.wins = 1 if not (pilot_winner and hasattr(pilot_winner, "wins")) else pilot_winner.wins + 1
        pilot_loser.losses = 1 if not (pilot_loser and hasattr(pilot_loser, "losses")) else pilot_loser.losses + 1
#       if pilot_winner and hasattr(pilot_winner, "wins") : pilot_winner.wins += 1 else pilot_winner.wins = 1
#       if pilot_loser : pilot_loser.losses += 1
    return pilot_outcomes
