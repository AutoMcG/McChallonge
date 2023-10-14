from enum import Enum
import json
import pprint

class Tournament(object):
    def __init__(self, j):
        self.__dict__ = json.loads(j)
    def __str__(self):
        pp = pprint.PrettyPrinter()
        return pp.pformat(self.__dict__)

class TVals(Enum):
    id = 1
    name = 2
    state = 3