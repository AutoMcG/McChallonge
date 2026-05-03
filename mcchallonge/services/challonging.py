import os
import requests
import logging  
from requests_oauthlib import OAuth2Session
from .oauth_client import get_challonge_oauth_session
from ..models.tournament import Tournament
from ..models.participant import Participant
from ..models.match import Match

logger = logging.getLogger(__name__) 

CHALLONGE_API_V1= "https://api.challonge.com/v1"

def prepare_session(user: str, api_key: str) -> requests.Session:
    challonger = (user, api_key)
    headers = {"Accept": "application/json", 
              "User-Agent": "McChallonger", 
              "Accept-Encoding": "gzip, deflate"}
    s = requests.Session() 
    s.auth = challonger
    s.headers.update(headers)
    return s

def prepare_session_from_env() -> requests.Session:
    challonger = (os.environ['challonge_user'], os.environ['challonge_key'])
    headers = {"Accept": "application/json", 
              "User-Agent": "McChallonger", 
              "Accept-Encoding": "gzip, deflate"}
    s = requests.Session() 
    s.auth = challonger
    s.headers.update(headers)
    return s

def prepare_oauth_session() -> OAuth2Session:
    client_id = os.environ["CHALLONGE_CLIENT_ID"]
    client_secret = os.environ["CHALLONGE_CLIENT_SECRET"]
    redirect_uri = os.environ.get("CHALLONGE_REDIRECT_URI", "http://localhost:8080/callback")
    oauth_session = get_challonge_oauth_session(client_id, client_secret, redirect_uri)
    return oauth_session

def get_tournaments(session: requests.Session) -> list[Tournament]:
    URL = f'{CHALLONGE_API_V1}/tournaments.json'
    tournaments_request = requests.Request('GET', URL, params={"state": "in_progress"})
    logger.info(f"Getting tournaments from Challonge API at {tournaments_request.prepare().url}")
    
    response = session.send(session.prepare_request(tournaments_request))
    response.raise_for_status()
    logger.info(f"Received response: {response.status_code} {response.reason}")
    
    response_data = response.json()
    tournaments = [Tournament(**value["tournament"]) for value in response_data]
    
    logger.info(f"Retrieved {len(tournaments)} tournaments from Challonge API")
    return tournaments

def get_tournament_data(session: requests.Session, tournament_id_or_url: str) -> Tournament:
    URL = f'{CHALLONGE_API_V1}/tournaments/{tournament_id_or_url}.json'
    logger.info(f"Getting tournament data from Challonge API at {URL}")
    
    response = session.get(URL)
    response.raise_for_status()
    logger.info(f"Received response: {response.status_code} {response.reason}")
    
    tournament_data = response.json()["tournament"]
    return Tournament(**tournament_data)

def get_participants_data(session: requests.Session, tournament_id_or_url: str) -> list[Participant]:
    URL = f'{CHALLONGE_API_V1}/tournaments/{tournament_id_or_url}/participants.json'
    
    response = session.get(URL)
    response.raise_for_status()
    response_data = response.json()
    
    pilots = [Participant(**value["participant"]) for value in response_data]
    logger.info(f"Retrieved {len(pilots)} participants")
    return pilots

def get_match_data(
    session: requests.Session,
    tournament_id_or_url: str,
    states: str | list[str] | None = None,
) -> list[Match]:
    URL = f'{CHALLONGE_API_V1}/tournaments/{tournament_id_or_url}/matches.json'
    
    response = session.get(URL)
    response.raise_for_status()
    response_data = response.json()
    
    matches = [Match(**value["match"]) for value in response_data]
    logger.info(f"Retrieved {len(matches)} matches")

    if states is not None:
        filter_states = {states} if isinstance(states, str) else set(states)
        matches = [match for match in matches if match.state in filter_states]
        logger.info(f"Filtered to {len(matches)} matches with state(s): {filter_states}")

    return matches


def bulk_add_participants(
    session: requests.Session,
    tournament_id_or_url: str,
    participants: list[dict],
    verbose: bool = False,
) -> list[dict]:
    """Add participants to a tournament one at a time via the Challonge v1 API.

    Each entry in *participants* must have a ``bot_name`` key (used as the
    display name).

    Returns the list of created participant dicts as returned by the API.
    """
    from urllib.parse import quote

    URL = f"{CHALLONGE_API_V1}/tournaments/{tournament_id_or_url}/participants.json"

    created = []
    for p in participants:
        url_with_params = f"{URL}?participant[name]={quote(str(p['bot_name']), safe='')}"
        if verbose:
            logger.info(f"POST {url_with_params}")

        response = session.post(url_with_params)

        if verbose:
            logger.info(f"Response status: {response.status_code} {response.reason}")
            logger.info(f"Response body: {response.text[:500]}")

        response.raise_for_status()

        resp_data = response.json()
        if isinstance(resp_data, dict) and "participant" in resp_data:
            created.append(resp_data["participant"])
        elif isinstance(resp_data, list):
            created.extend(item["participant"] for item in resp_data if "participant" in item)
        else:
            logger.warning(f"Unexpected API response shape for '{p['bot_name']}': {resp_data}")

    logger.info(f"Added {len(created)} participant(s) to tournament '{tournament_id_or_url}'")
    return created