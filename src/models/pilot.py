from enum import Enum
import json
import pprint

class Pilot(object):
    def __init__(self, j):
        none_to_empty = j.replace('null', '"empty"')
        self.__dict__ = json.loads(none_to_empty)
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.__dict__)

#couple with getattr: 
#getattr(my_match, MVals.id.name)
class PVals(Enum):
    id = 1
    name = 2