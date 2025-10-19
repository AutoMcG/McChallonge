import os
from dotenv import load_dotenv

load_dotenv()

# Challonge API settings
CHALLONGE_USER = os.environ.get('challonge_user')
CHALLONGE_KEY = os.environ.get('challonge_key')
CHALLONGE_TOURNAMENT_ID = os.environ.get('challonge_tt_id')

# Output settings
BUILD_DIR = os.environ.get('BUILD_DIR', 'build')