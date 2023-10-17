import logging
import os
import pprint
import pytest

import requests

from ..services import challonging
from ..services import think
from ..services import templater
from ..models import *

class TestHighestLevel:
#test challonge class

    #real constants
    TT_URL = ""
    TT_ID = ""
    user = ""
    key = ""

    @classmethod
    def setup_class(cls):        
        cls.user = os.environ['challonge_user']
        cls.key = os.environ['challonge_key']
        cls.TT_URL = os.environ['challonge_tt_url']
        cls.TT_ID = os.environ['challonge_tt_id']
        cls.session = challonging.prepare_session(cls.user, cls.key)

    def test_prepare_session(cls):
        #set up test data
        user = "Testman"
        key = "herpaderpa"

        headers = {'User-Agent': 'McChallonger', 'Accept-Encoding': 'gzip, deflate', 'Accept': 'application/json', 'Connection': 'keep-alive'}

        #do the thing
        testSession = challonging.prepare_session(user, key)

        #multi-assert appropriate for one action -> multiple data points
        #error string MUST have expected/actual
        errors = []
        if not testSession.auth == (user, key):
            errors.append(f"Auth was not set correctly for session.\nExpected: {user}, {key}\nActual: {testSession.auth}")        
        if not testSession.headers == headers:
            errors.append(f"Headers for session were not what was expected.\nExpected: {headers}\nActual: {testSession.headers}")
        assert not errors, "Shit's fucked: \n{}".format("\n".join(errors))
    
    def test_get_tournament_data(cls):
        tourn_data = challonging.get_tournament_data(cls.session, cls.TT_ID)
        errors = []        
        #should be a list comprehension instead of a for loop
        for val in tournament.TKeys:
            if not getattr(tourn_data, val.name, False):
                errors.append(f"Field in tkeys not found in returned tournament json.\nMissing Value:{val}")
        assert not errors, "Shit's fucked: \n{}".format("\n".join(errors))

    def test_fail_tournament_data(cls):
        with pytest.raises(AssertionError):
            tourn_data = challonging.get_tournament_data(cls.session, cls.TT_ID)
            del tourn_data.__dict__["id"]
            del tourn_data.__dict__["name"]
            del tourn_data.__dict__["state"]
            errors = []        
            #should be a list comprehension instead of a for loop
            for val in tournament.TKeys:
                if not getattr(tourn_data, val.name, False):
                    errors.append(f"Field in tkeys not found in returned tournament json.\nMissing Value:{val}")
            assert not errors, "Shit's fucked: \n{}".format("\n".join(errors))

    def test_get_participants_data(cls):
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)

        #for every pilot, run every enum, return new list of pilots parsed by all enum values
        pilots_values = [{pkey.name:getattr(this_pilot, pkey.name) for pkey in pilot.PKeys if hasattr(this_pilot, pkey.name)} 
                        for this_pilot in pilots]        
        
        #does every pilot have every field in enum?
        pilot_results = [all([pilot_values.get(pkey.name) for pkey in pilot.PKeys]) 
                         for pilot_values in pilots_values] #does not handle 0 or None values well
        assert all(pilot_results), f"One of these is missing values: {pilots_values}" #todo: report which are missing what lol

    def test_get_match_data(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)

        #for every match, run every enum, return new list of matches comprehended by all enum values        
        matches_values = [{mkey.name:getattr(this_match, mkey.name) for mkey in match.MKeys if hasattr(this_match, mkey.name)} 
                        for this_match in matches]

        #does every match have every field? 
        match_results = [all([match_values.get(mkey.name) for mkey in match.MKeys]) 
                         for match_values in matches_values] #does not handle 0 or None values well
        
        assert all(match_results), f"One of these is missing values: {matches_values}" #todo: report which are missing what lol

    def test_think_count_outcomes(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
        updated_pilots = think.count_outcomes(matches, pilots)
        print(f'Here is the new data: {[str(mpilot) for mpilot in updated_pilots]}')

    def test_templater_table(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
        updated_pilots = think.count_outcomes(matches, pilots)
        templater.run_table_template(title="FirstTemplateRun", relative_static_dir="static", schema=[value.name for value in pilot.PKeys], main_data_source=updated_pilots)
        pass