import json
import logging
import os
import pprint
import pytest
import requests
import time

import requests
from requests_oauthlib import OAuth2Session

from dotenv import load_dotenv 

from ..services import challonging
from ..services import think
from ..services import templater
from ..services import packager
from ..models import *
from ..models.participant import Participant
from ..models.tournament import Tournament
from ..models.match import Match

logger = logging.getLogger(__name__)

class TestHighestLevel:
#test challonge class

    #real constants
    TT_URL = ""
    TT_ID = ""
    user = ""
    key = ""

    @classmethod
    def setup_class(cls):
        load_dotenv()        
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
    
    def test_get_tournament_data(cls, caplog):
        caplog.set_level(logging.INFO)
        tourn_data = challonging.get_tournament_data(cls.session, cls.TT_ID)
        errors = []
        # Use Tournament dataclass fields
        for field in Tournament.__dataclass_fields__:
            if not hasattr(tourn_data, field):
                errors.append(f"Field '{field}' not found in returned tournament object.")
        assert not errors, "Missing tournament fields:\n{}".format("\n".join(errors))
    
    def test_get_tournaments(cls, caplog):
        caplog.set_level(logging.INFO)
        tournaments = challonging.get_tournaments(cls.session)
        logger.info(f"tournament info: {tournaments}")

    def test_get_oauth_token(cls, caplog):
        caplog.set_level(logging.INFO)
        challonge_oauth_session = challonging.prepare_oauth_session() 
        logger.info(f"Session info: {challonge_oauth_session}")

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
        # Check all pilots have all Pilot fields
        bad_pilots = [this_pilot
                      for this_pilot in pilots
                      if any([not hasattr(this_pilot, field) for field in Participant.__dataclass_fields__])]
        assert len(bad_pilots) == 0, f"Some pilots were missing values: {[str(result) for result in bad_pilots]}"

    def test_fail_participants_data(cls):
        with pytest.raises(AssertionError):
            pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
            del pilots[0].__dict__["id"]
            bad_pilots = [this_pilot
                          for this_pilot in pilots
                          if any([not hasattr(this_pilot, field) for field in Participant.__dataclass_fields__])]
            assert len(bad_pilots) == 0, f"Some pilots were missing values: {[str(result) for result in bad_pilots]}"

    def test_get_match_data(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        # Check all matches have all Match fields
        matches_values = [{field: getattr(this_match, field, None) for field in Match.__dataclass_fields__}
                          for this_match in matches]
        match_results = [all([match_values.get(field) is not None for field in Match.__dataclass_fields__])
                         for match_values in matches_values]
        assert all(match_results), f"One of these is missing values: {matches_values}" #todo: report which are missing what lol

    def test_think_count_outcomes(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
        updated_pilots = think.count_outcomes(matches, pilots)
        print(f'Here is the new data: {[str(mpilot) for mpilot in updated_pilots]}')
        assert True

    def test_templater_table(cls):
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
        updated_pilots = think.count_outcomes(matches, pilots)
        print(templater.run_table_template(
            table_template_name="main_table.jinja.html",
            title="FirstTemplateRun",
            relative_static_dir="static",
            schema=list(Participant.__dataclass_fields__.keys()),
            main_data_source=updated_pilots))
        pass

    def test_packager(cls):
        create_files = False #change this to true to actually create files        
        output_path = f'build/{time.strftime("%Y%m%d-%H%M%S")}/'
        html_path = f'build/first_output.html' #dependent on static file existing
        all_statics = [this_file.path for this_file in (os.scandir('src/web/static/'))]
        if (create_files):
            packager.create_output_folder(output_path=output_path, html_path=html_path, static_paths=all_statics)
        pass

    def test_new_html(cls):
        #get table data
        matches = challonging.get_match_data(cls.session, cls.TT_ID)
        pilots = challonging.get_participants_data(cls.session, cls.TT_ID)
        updated_pilots = think.count_outcomes(matches, pilots)

        #put pilot
        html_output = templater.run_table_template(
            table_template_name="new_main_table.jinja.html",
            title=f"Last Update: {time.strftime('%Y%m%d-%H%M%S')}",
            relative_static_dir="static",
            schema=list(Participant.__dataclass_fields__.keys()),
            main_data_source=updated_pilots)        
        
        create_files = False #change this to true to actually create files        
        
        file_timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_path = f'./build/{file_timestamp}/'
        html_path = f'{output_path}index.html' 

        if (create_files):
            os.makedirs(output_path, exist_ok=True)
            with open(html_path, 'w') as f:
                f.write(html_output)

        all_statics = ['./src/web/static/new_main_table_styles.css']
        
        if (create_files):
            packager.create_output_folder(output_path=output_path, html_path=html_path, static_paths=all_statics)
        pass