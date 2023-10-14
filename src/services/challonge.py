import json
import requests
from ..models.tournament import Tournament
from ..models.pilot import Pilot
from ..models.match import Match

CHALLONGE_API_V1= "https://api.challonge.com/v1/"

def prepare_session(user: str, api_key: str) -> requests.Session:
    challonger = (user, api_key)
    headers = {"Accept" : "application/json", "User-Agent" : "McChallonger", "Accept-Encoding" :"gzip, deflate"}
    s = requests.Session() 
    s.auth = challonger
    s.headers.update(headers)
    return s

def get_tournament_data(session: requests.Session, tournament_id_or_url: str) -> Tournament :
    URL = f'{CHALLONGE_API_V1}tournaments/{tournament_id_or_url}.json'    
    response = session.get(URL).json()["tournament"]        
    return Tournament(json.dumps(response))

def get_participants_data(session: requests.Session, tournament_id_or_url: str) -> [Pilot]:
    URL = f'{CHALLONGE_API_V1}tournaments/{tournament_id_or_url}/participants.json'
    response = session.get(URL).json()
    pilots = [Pilot(json.dumps(value["participant"])) for value in response]
    return pilots

def get_match_data(session: requests.Session, tournament_id_or_url: str) -> [Match]:
    URL = f'{CHALLONGE_API_V1}tournaments/{tournament_id_or_url}/matches.json'
    response = session.get(URL).json()
    matches = [Match(json.dumps(value["match"])) for value in response]     
    return matches