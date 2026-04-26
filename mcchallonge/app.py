import os
import logging
import time
import sys
from flask import Flask, render_template, jsonify, redirect, url_for
from flask_frozen import Freezer

from mcchallonge import config
from mcchallonge.services.local_cache import load_cached_tournament_data, refresh_cached_tournament_data

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
def root_page():
    """Redirect root to /index.html for live server parity with static output."""
    return redirect(url_for('tournament_page'))

@app.route('/index.html')
def tournament_page():
    """Render the main tournament page shell. Data is loaded client-side from local cache."""
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Tournament Dashboard",
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        client_rendered=True
    )

@app.route('/participants')
def participants_page():
    """Render just the participants list shell. Data is loaded client-side from local cache."""
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Participants",
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        client_rendered=True,
        show_only="participants"  # Signal to template to only show participants section
    )

@app.route('/matches')
def matches_page():
    """Render the matches list shell. Data is loaded client-side from local cache."""
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Matches",
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        client_rendered=True,
        show_only="matches"  # Signal to template to only show matches section
    )

@app.route('/api/cache', methods=['GET'])
def cache_data():
    """Return locally cached tournament data."""
    data = load_cached_tournament_data()
    if data is None:
        return jsonify({"error": "Local cache file not found. Click 'Update Local Cache' to create it."}), 404
    return jsonify(data)

@app.route('/api/cache/update', methods=['POST'])
def cache_data_update():
    """Fetch latest data from Challonge and update local cache file."""
    tournament_id = app.config['TOURNAMENT_ID']
    if not tournament_id:
        return jsonify({"error": "Tournament ID is not configured."}), 500

    try:
        data = refresh_cached_tournament_data(tournament_id)
        return jsonify(data)
    except Exception as exc:
        logger.exception("Failed to refresh local cache data")
        return jsonify({"error": f"Failed to update local cache: {exc}"}), 500

@freezer.register_generator
def url_generator():
    # Generate URLs for freezer
    yield '/'
    yield '/index.html'
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

