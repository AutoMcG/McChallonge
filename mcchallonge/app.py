import os
import logging
import time
import sys
import argparse
import importlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_frozen import Freezer

from mcchallonge import config
from mcchallonge.services.local_cache import (
    get_cache_file_path,
    load_cached_tournament_data,
    refresh_all_cached_tournaments,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve template and static folders relative to this package file so they
# work consistently regardless of execution mode or current working directory.
package_dir = os.path.dirname(__file__)
template_folder = os.path.join(package_dir, 'web', 'templates')
static_folder = os.path.join(package_dir, 'web', 'static')

# Initialize Flask app
app = Flask(__name__, 
           template_folder=template_folder,
           static_folder=static_folder)

# Configuration
app.config.from_object('mcchallonge.config')
app.config['TOURNAMENT_IDS'] = config.CHALLONGE_TOURNAMENT_IDS
app.config['FREEZER_RELATIVE_URLS'] = True  # Use relative URLs for links
freezer = Freezer(app, with_static_files=True, with_no_argument_rules=True)


def _resolve_logo_url() -> str | None:
    configured_logo = config.MCCHALLONGE_LOGO_URL
    if not configured_logo:
        return None

    # Absolute URLs can be used directly.
    if configured_logo.startswith(('http://', 'https://', '/')):
        return configured_logo

    # Relative paths are treated as files under Flask static/.
    return url_for('static', filename=configured_logo)


def _client_data_mode() -> str:
    mode = (app.config.get('MCCHALLONGE_CLIENT_DATA_MODE') or 'api').strip().lower()
    return mode if mode in {'api', 'fixed'} else 'api'


def _client_data_root() -> str:
    root = (app.config.get('MCCHALLONGE_CLIENT_DATA_ROOT') or '/data').strip()
    if not root.startswith('/'):
        root = f'/{root}'
    return root.rstrip('/') or '/data'

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
        client_rendered=True,
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        logo_url=_resolve_logo_url(),
    )

@app.route('/participants')
def participants_page():
    """Render just the participants list shell. Data is loaded client-side from local cache."""
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Participants",
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        client_rendered=True,
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        show_only="participants",  # Signal to template to only show participants section
        logo_url=_resolve_logo_url(),
    )

@app.route('/matches')
def matches_page():
    """Render the matches list shell. Data is loaded client-side from local cache."""
    return render_template(
        'tournament_dashboard.jinja.html',
        title="Matches",
        current_date=time.strftime("%Y-%m-%d %H:%M"),
        client_rendered=True,
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        show_only="matches",  # Signal to template to only show matches section
        logo_url=_resolve_logo_url(),
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
    body = request.get_json(silent=True) or {}
    requested_id = body.get('tournament_id')

    if requested_id:
        tournament_ids = [requested_id]
    else:
        tournament_ids = app.config['TOURNAMENT_IDS']

    if not tournament_ids:
        return jsonify({"error": "No tournament IDs are configured."}), 500

    try:
        data = refresh_all_cached_tournaments(tournament_ids)
        return jsonify(data)
    except Exception as exc:
        logger.exception("Failed to refresh local cache data")
        return jsonify({"error": f"Failed to update local cache: {exc}"}), 500

@app.route('/api/cache/clear', methods=['POST'])
def cache_data_clear():
    """Delete the local cache file."""
    cache_path = get_cache_file_path()
    if cache_path.exists():
        cache_path.unlink()
    return jsonify({"message": "Cache cleared."})

@freezer.register_generator
def url_generator():
    # Generate URLs for freezer
    yield '/'
    yield '/index.html'
    yield '/participants'
    yield '/matches'
    # Freeze the cache JSON so the static build can serve tournament data.
    # Only yield when the cache file already exists so freeze() doesn't fail
    # with a 404 on machines that haven't populated the cache yet.
    if get_cache_file_path().exists():
        yield '/api/cache'


def _run_dev_server() -> None:
    logger.info("Starting development server...")
    app.run(debug=True)


def _run_static_build() -> None:
    logger.info("Generating static site...")

    # Static hosting (S3/CloudFront) uses fixed JSON filenames under /data.
    app.config['MCCHALLONGE_CLIENT_DATA_MODE'] = 'fixed'

    freezer.freeze()
    logger.info("Static site generated in 'build' directory")


def _run_waitress_server(host: str, port: int, threads: int) -> None:
    try:
        waitress_module = importlib.import_module("waitress")
    except ImportError as exc:
        logger.error(
            "Waitress is required for 'serve' mode. Install it with: pip install waitress"
        )
        raise SystemExit(1) from exc

    serve = getattr(waitress_module, "serve")

    logger.info(
        "Starting production WSGI server on %s:%s (threads=%s)",
        host,
        port,
        threads,
    )
    serve(app, host=host, port=port, threads=threads)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mcchallonge.app",
        description="Run the McChallonge dashboard app.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("build", help="Generate a static site using Frozen-Flask.")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run a production WSGI server (recommended behind Nginx).",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    serve_parser.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Number of Waitress worker threads.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.command == "build":
        _run_static_build()
        return

    if args.command == "serve":
        _run_waitress_server(args.host, args.port, args.threads)
        return

    _run_dev_server()

if __name__ == '__main__':
    main()

