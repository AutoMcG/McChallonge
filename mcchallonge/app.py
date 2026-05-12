import os
import logging
import time
import sys
import argparse
import importlib
from flask import Flask, render_template, jsonify, request, redirect, url_for, abort, has_request_context, send_from_directory
from flask_frozen import Freezer

from mcchallonge import config
from mcchallonge.services.local_cache import (
    get_cache_file_path,
    load_cached_tournament_data,
    refresh_all_cached_tournaments,
)
from mcchallonge.services.underway_banners import (
    generate_underway_banners,
    get_underway_dir,
    load_underway_manifest,
)
from mcchallonge.services.participant_images import (
    get_image_cache_dir,
    load_approved_participants_index,
    prewarm_approved_participant_images,
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


def _underway_source_mode() -> str:
    mode = (app.config.get('MCCHALLONGE_UNDERWAY_SOURCE_MODE') or 'challonge').strip().lower()
    return mode if mode in {'challonge', 'cache'} else 'challonge'


def _admin_enabled() -> bool:
    # Inside a request: only loopback visitors get admin controls.
    if has_request_context():
        addr = request.remote_addr or ''
        return addr == '127.0.0.1' or addr == '::1' or addr.startswith('127.')
    # Outside a request context (e.g. static build): read config flag.
    val = app.config.get('MCCHALLONGE_ADMIN_ENABLED')
    return val if isinstance(val, bool) else True

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
        underway_source_mode=_underway_source_mode(),
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        admin_enabled=_admin_enabled(),
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
        underway_source_mode=_underway_source_mode(),
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        admin_enabled=_admin_enabled(),
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
        underway_source_mode=_underway_source_mode(),
        client_data_mode=_client_data_mode(),
        client_data_root=_client_data_root(),
        admin_enabled=_admin_enabled(),
        show_only="matches",  # Signal to template to only show matches section
        logo_url=_resolve_logo_url(),
    )


@app.route('/underway')
def underway_page():
    """Render PNG banners for currently underway matches."""
    manifest = _refresh_underway_from_cache()

    return render_template(
        'underway.jinja.html',
        title="Underway Matches",
        generated_at=manifest.get("generated_at"),
        banners=manifest.get("banners") or [],
    )


def _refresh_underway_from_cache() -> dict:
    """Generate underway manifest from local cache only (no Challonge API calls)."""
    if _underway_source_mode() == 'cache':
        existing = load_underway_manifest()
        return existing or {"generated_at": None, "banners": []}

    data = load_cached_tournament_data()
    if data is None:
        existing = load_underway_manifest()
        return existing or {"generated_at": None, "banners": []}

    try:
        return generate_underway_banners(data)
    except Exception:
        logger.exception("Failed to generate underway banners from local cache")
        existing = load_underway_manifest()
        return existing or {"generated_at": None, "banners": []}


@app.route('/api/underway', methods=['GET'])
def underway_data():
    """Refresh and return underway banners from local cache only."""
    return jsonify(_refresh_underway_from_cache())


@app.route('/underway/banner/<path:filename>')
def underway_banner_file(filename: str):
    """Serve generated underway banner PNGs."""
    return send_from_directory(get_underway_dir(), filename)


@app.route('/img/<path:filename>')
def participant_image_file(filename: str):
    """Serve cached participant images."""
    return send_from_directory(get_image_cache_dir(), filename, max_age=86400)

@app.route('/api/cache', methods=['GET'])
def cache_data():
    """Return locally cached tournament data."""
    data = load_cached_tournament_data()
    if data is None:
        return jsonify({"error": "Local cache file not found. Click 'Update Local Cache' to create it."}), 404
    return jsonify(data)


def _require_loopback():
    """Abort with 403 if the request did not originate from loopback."""
    addr = request.remote_addr
    if addr not in ('127.0.0.1', '::1') and not (addr or '').startswith('127.'):
        abort(403)


@app.route('/api/cache/update', methods=['POST'])
def cache_data_update():
    """Fetch latest data from Challonge and update local cache file."""
    _require_loopback()
    body = request.get_json(silent=True) or {}
    requested_id = body.get('tournament_id')
    requested_underway_mode = (body.get('underway_source_mode') or _underway_source_mode()).strip().lower()
    underway_mode = requested_underway_mode if requested_underway_mode in {'challonge', 'cache'} else 'challonge'
    app.config['MCCHALLONGE_UNDERWAY_SOURCE_MODE'] = underway_mode

    if requested_id:
        tournament_ids = [requested_id]
    else:
        tournament_ids = app.config['TOURNAMENT_IDS']

    if not tournament_ids:
        return jsonify({"error": "No tournament IDs are configured."}), 500

    try:
        data = refresh_all_cached_tournaments(tournament_ids)
        if underway_mode == 'challonge':
            try:
                generate_underway_banners(data)
            except Exception:
                logger.exception("Cache refresh succeeded, but underway banner generation failed")
        else:
            logger.info("Cache refresh succeeded; skipped underway banner regeneration due to server cache override mode")
        return jsonify(data)
    except Exception as exc:
        logger.exception("Failed to refresh local cache data")
        return jsonify({"error": f"Failed to update local cache: {exc}"}), 500

@app.route('/api/cache/clear', methods=['POST'])
def cache_data_clear():
    """Delete the local cache file."""
    _require_loopback()
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
    yield '/underway'
    # Freeze the cache JSON so the static build can serve tournament data.
    # Only yield when the cache file already exists so freeze() doesn't fail
    # with a 404 on machines that haven't populated the cache yet.
    if get_cache_file_path().exists():
        yield '/api/cache'


def _run_dev_server() -> None:
    _initialize_participant_image_cache()
    logger.info("Starting development server...")
    app.run(debug=True)


def _run_static_build() -> None:
    logger.info("Generating static site...")

    # Static hosting (S3/CloudFront) uses fixed JSON filenames under /data.
    # Admin controls are never available in a static build — there's no server to call.
    app.config['MCCHALLONGE_CLIENT_DATA_MODE'] = 'fixed'
    app.config['MCCHALLONGE_ADMIN_ENABLED'] = False

    freezer.freeze()
    logger.info("Static site generated in 'build' directory")


def _run_waitress_server(port: int, threads: int) -> None:
    try:
        waitress_module = importlib.import_module("waitress")
    except ImportError as exc:
        logger.error(
            "Waitress is required for 'serve' mode. Install it with: pip install waitress"
        )
        raise SystemExit(1) from exc

    serve = getattr(waitress_module, "serve")

    _initialize_participant_image_cache()

    # Bind on all interfaces so LAN clients can reach the app, and explicitly
    # on loopback so the admin can use 127.0.0.1 to access cache-update controls.
    listen = f"0.0.0.0:{port} 127.0.0.1:{port}"
    logger.info("Starting production WSGI server on %s (threads=%s)", listen, threads)
    serve(app, listen=listen, threads=threads)


def _initialize_participant_image_cache() -> None:
    """Preload approved participant images once per process startup."""
    try:
        index = load_approved_participants_index()
        warmed = prewarm_approved_participant_images(index)
        if warmed:
            logger.info("Participant image cache warmup complete: %s image(s) available", warmed)
    except Exception:
        logger.exception("Participant image cache warmup failed")


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
        _run_waitress_server(args.port, args.threads)
        return

    _run_dev_server()

if __name__ == '__main__':
    main()

