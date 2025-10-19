import os
import logging
from flask import Flask, render_template, url_for
from flask_frozen import Freezer

from mcchallonge import config
from mcchallonge.services import challonging, think

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           template_folder="mcchallonge/web/templates",
           static_folder="mcchallonge/web/static")

# Configuration
app.config.from_object('mcchallonge.config')
app.config['TOURNAMENT_ID'] = config.CHALLONGE_TOURNAMENT_ID
freezer = Freezer(app, with_static_files=True, with_no_argument_rules=True)

@app.route('/')
def tournament_page():
    """Render the main tournament page"""
    # Create API session
    session = challonging.prepare_session_from_env()
    
    # Get tournament data
    tournament_id = app.config['TOURNAMENT_ID']
    tournament = challonging.get_tournament_data(session, tournament_id)
    participants = challonging.get_participants_data(session, tournament_id)
    matches = challonging.get_match_data(session, tournament_id)
    
    # Process data
    updated_participants = think.count_outcomes(matches, participants)
    
    # Render template
    return render_template(
        'new_main_table.jinja.html',
        title=f"Tournament: {tournament.name}",
        schema=["Name", "Wins", "Losses"],
        main_data_source=updated_participants
    )

@app.route('/participants')
def participants_page():
    """Render just the participants list"""
    session = challonging.prepare_session_from_env()
    tournament_id = app.config['TOURNAMENT_ID']
    participants = challonging.get_participants_data(session, tournament_id)
    
    return render_template(
        'separate_table.jinja.html',
        title="Participants",
        main_data_source=participants
    )

@app.route('/matches')
def matches_page():
    """Render the matches list"""
    session = challonging.prepare_session_from_env()
    tournament_id = app.config['TOURNAMENT_ID']
    matches = challonging.get_match_data(session, tournament_id)
    
    return render_template(
        'separate_table.jinja.html',
        title="Matches",
        main_data_source=matches
    )

@freezer.register_generator
def url_generator():
    # Generate URLs for freezer
    yield '/'
    yield '/participants'
    yield '/matches'

if __name__ == '__main__':
    # Check if we should generate static files or run the development server
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        logger.info("Generating static site...")
        freezer.freeze()
        logger.info("Static site generated in 'build' directory")
    else:
        logger.info("Starting development server...")
        app.run(debug=True)

