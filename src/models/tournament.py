from enum import Enum
import json
import pprint

class Tournament(object):
    def __init__(self, j):
        none_to_empty = j.replace('null', '"empty"')
        self.__dict__ = json.loads(none_to_empty)
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.__dict__)

#couple with getattr: 
#getattr(my_match, TKeys.id.name)
#reduces magic
class TKeys(Enum):
    id = 1
    name = 2
    state = 3