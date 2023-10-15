from enum import Enum
import json
import pprint

class Pilot(object):
    def __init__(self, j):
        none_to_empty = j.replace('null', '"empty"')
        self.__dict__ = json.loads(none_to_empty)
        self.wins = 0
        self.losses = 0
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.__dict__)

#couple with getattr: 
#getattr(my_match, MVals.id.name)
#reduces magic
class PVals(Enum):
    id = 1
    name = 2
    wins = 3    #extended data
    losses = 4  #extended data