from enum import Enum
import json
import pprint

class Match(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.__dict__)

#couple with getattr
class MVals(Enum):
    id = 1
    state = 2
    player1_id = 3
    player2_id = 4
    winner_id = 5
    loser_id = 6
    scheduled_time = 7
    location = 8
    underway_at = 9
    completed_at = 10