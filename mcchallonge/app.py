import os
import logging
import time
import sys
from flask import Flask, render_template, url_for
from flask_frozen import Freezer

from mcchallonge import config
from mcchallonge.services import challonging, think, templating

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine template and static folder paths based on execution context
if __name__ == '__main__' or 'mcchallonge.app' in sys.argv:
    # Running as a module (-m mcchallonge.app)
    template_folder = os.path.join(os.path.dirname(__file__), 'web', 'templates')
    static_folder = os.path.join(os.path.dirname(__file__), 'web', 'static')
else:
    # Running as import or from another module
    template_folder = "mcchallonge/web/templates"
    static_folder = "mcchallonge/web/static"

# Initialize Flask app
app = Flask(__name__, 
           template_folder=template_folder,
           static_folder=static_folder)

# Configuration
app.config.from_object('mcchallonge.config')
app.config['TOURNAMENT_ID'] = config.CHALLONGE_TOURNAMENT_ID
app.config['FREEZER_RELATIVE_URLS'] = True  # Use relative URLs for links
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
        'tournament_dashboard.jinja.html',
        title=f"Tournament: {tournament.name}",
        tournament=tournament,
        participants=updated_participants,
        matches=matches,
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        get_participant_by_id=lambda pid: next((p for p in updated_participants if p.id == pid), None)
    )

@app.route('/participants')
def participants_page():
    """Render just the participants list"""
    session = challonging.prepare_session_from_env()
    tournament_id = app.config['TOURNAMENT_ID']
    tournament = challonging.get_tournament_data(session, tournament_id)
    participants = challonging.get_participants_data(session, tournament_id)
    matches = []  # Empty matches list for this view
    
    # Process data
    updated_participants = think.count_outcomes([], participants)  # No matches to count
    
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Participants",
        tournament=tournament,
        participants=updated_participants,
        matches=matches,
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        get_participant_by_id=lambda pid: next((p for p in updated_participants if p.id == pid), None),
        show_only="participants"  # Signal to template to only show participants section
    )

@app.route('/matches')
def matches_page():
    """Render the matches list"""
    session = challonging.prepare_session_from_env()
    tournament_id = app.config['TOURNAMENT_ID']
    tournament = challonging.get_tournament_data(session, tournament_id)
    participants = challonging.get_participants_data(session, tournament_id)
    matches = challonging.get_match_data(session, tournament_id)
    
    # Process data
    updated_participants = think.count_outcomes(matches, participants)
    
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Matches",
        tournament=tournament,
        participants=updated_participants,
        matches=matches,
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        get_participant_by_id=lambda pid: next((p for p in updated_participants if p.id == pid), None),
        show_only="matches"  # Signal to template to only show matches section
    )

@freezer.register_generator
def url_generator():
    # Generate URLs for freezer
    yield '/'
    yield '/participants'
    yield '/matches'
    
# We will handle static URLs manually in the templates
# Flask-Freezer doesn't provide a simple way to transform URLs during freeze

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

