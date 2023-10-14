import logging
import os
import pprint

import requests

from ..services import challonge
from ..models import *

class TestHighestLevel:
#test challonge class

    #real constants
    TT_URL = "test_testerton_ant"
    TT_ID = "13581036"
    user = ""
    key = ""

    @classmethod
    def setup_class(cls):        
        cls.user = os.environ['challonge_user']
        cls.key = os.environ['challonge_key']
        cls.session = challonge.prepare_session(cls.user, cls.key)


    def test_prepare_session(cls):
        #set up test data
        user = "Testman"
        key = "herpaderpa"

        headers = {'User-Agent': 'McChallonger', 'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json', 'Connection': 'keep-alive'}

        #do the thing
        testSession = challonge.prepare_session(user, key)

        #multi-assert appropriate for one action -> multiple data points
        #error string MUST have expected/actual
        errors = []
        if not testSession.auth == (user, key):
            errors.append(f"Auth was not set correctly for session.\nExpected: {user}, {key}\nActual: {testSession.auth}")        
        if not testSession.headers == headers:
            errors.append(f"Headers for session were not what was expected.\nExpected: {headers}\nActual: {testSession.headers}")
        assert not errors, "Shit's fucked: \n{}".format("\n".join(errors))
    
    def test_get_tournament_data(cls):
        tourn_data = challonge.get_tournament_data(cls.session, cls.TT_ID)
        errors = []        
        #should be a list comprehension instead of a for loop
        for val in tournament.TVals:
            if not getattr(tourn_data, val.name, False):
                errors.append(f"Field in TVals not found in returned tournament json.\nMissing Value:{val}")
        assert not errors, "Shit's fucked: \n{}".format("\n".join(errors))

    def test_get_participants_data(cls):
        pilots = challonge.get_participants_data(cls.session, cls.TT_ID)

        #for every pilot, run every enum, return new list of pilots comprehended by all enum values
        pilots_values = [{pval.name:getattr(this_pilot, pval.name) for pval in pilot.PVals if hasattr(this_pilot, pval.name)} 
                        for this_pilot in pilots]
        
        #does every pilot have every field in enum?
        pilot_results = [all([pilot_values.get(pval.name) for pval in pilot.PVals]) for pilot_values in pilots_values]
        assert all(pilot_results), f"One of these is missing values: {pilots_values}"

    #test still broken
    def test_get_match_data(cls):
        matches = challonge.get_match_data(cls.session, cls.TT_ID)

        #for every match, run every enum, return new list of matches comprehended by all enum values

        single_match = matches[0]
        id_name = match.MVals.loser_id.name
        print(f"{single_match} hasattr({id_name}): {hasattr(single_match, id_name)}\r\n")
        
        matches_values = [{mval.name:getattr(this_match, mval.name) for mval in match.MVals if hasattr(this_match, mval.name)} 
                        for this_match in matches]
        print(f"matches_values: {matches_values}\r\n")
        
        match_results = [print([match_values.get(mval.name) for mval in match.MVals]) for match_values in matches_values]
        print(f"match_results: {match_results}\r\n")
        assert all(match_results), f"One of these is missing values: {matches_values}"
