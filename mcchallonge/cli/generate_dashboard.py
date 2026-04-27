#!/usr/bin/env python
import os
import argparse
import json
from dotenv import load_dotenv

from ..services.challonging import prepare_session, prepare_session_from_env, get_tournament_data, get_participants_data, get_match_data
from ..services.think import count_outcomes
from ..services.static_generator import generate_static_tournament_page
from ..models.tournament import Tournament
from ..models.participant import Participant
from ..models.match import Match


def write_json_outputs(output_file, tournament, participants, matches):
    """Write normalized JSON artifacts next to the generated dashboard HTML."""
    output_dir = os.path.dirname(output_file) or os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    artifacts = {
        "tournament.json": tournament.__dict__,
        "participants.json": [participant.__dict__ for participant in participants],
        "matches.json": [match.__dict__ for match in matches],
    }

    for file_name, payload in artifacts.items():
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as output_handle:
            json.dump(payload, output_handle, indent=2)
        print(f"Wrote {file_name}: {os.path.abspath(file_path)}")

def main():
    """CLI tool to generate tournament dashboard HTML files"""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Generate a static tournament dashboard HTML file"
    )
    
    # Required tournament ID or URL
    parser.add_argument(
        "tournament_id",
        help="Tournament ID or URL from Challonge"
    )
    
    # Output file path
    parser.add_argument(
        "-o", "--output",
        default="tournament_dashboard.html",
        help="Output HTML file path (default: tournament_dashboard.html)"
    )
    
    # Optional custom logo URL
    parser.add_argument(
        "--logo",
        help="URL for tournament logo image"
    )
    
    # Optional credentials (if not using environment variables)
    parser.add_argument(
        "-u", "--user",
        help="Challonge username (default: from environment variable)"
    )
    
    parser.add_argument(
        "-k", "--key",
        help="Challonge API key (default: from environment variable)"
    )
    
    # Optional custom HTML content file
    parser.add_argument(
        "--custom-content",
        help="Path to HTML file with custom content to include in the dashboard"
    )
    
    # Optional: Load from JSON files instead of API
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use local JSON files instead of API (requires --tournament-file, --participants-file, and --matches-file)"
    )
    
    parser.add_argument(
        "--tournament-file",
        help="JSON file with tournament data (for offline mode)"
    )
    
    parser.add_argument(
        "--participants-file",
        help="JSON file with participants data (for offline mode)"
    )
    
    parser.add_argument(
        "--matches-file",
        help="JSON file with matches data (for offline mode)"
    )
    
    args = parser.parse_args()
    
    # Load custom content if provided
    custom_content = None
    if args.custom_content and os.path.exists(args.custom_content):
        with open(args.custom_content, 'r', encoding='utf-8') as f:
            custom_content = f.read()
    
    # Get tournament data
    if args.offline:
        # Validate required files for offline mode
        if not all([args.tournament_file, args.participants_file, args.matches_file]):
            parser.error("Offline mode requires --tournament-file, --participants-file, and --matches-file")
            
        # Load from JSON files
        print(f"Loading data from local JSON files...")
        
        with open(args.tournament_file, 'r', encoding='utf-8') as f:
            tournament_data = json.load(f)
            if "tournament" in tournament_data:
                tournament_data = tournament_data["tournament"]
            tournament = Tournament(**tournament_data)
        
        with open(args.participants_file, 'r', encoding='utf-8') as f:
            participants_data = json.load(f)
            if all("participant" in item for item in participants_data):
                participants_data = [item["participant"] for item in participants_data]
            participants = [Participant(**p) for p in participants_data]
        
        with open(args.matches_file, 'r', encoding='utf-8') as f:
            matches_data = json.load(f)
            if all("match" in item for item in matches_data):
                matches_data = [item["match"] for item in matches_data]
            matches = [Match(**m) for m in matches_data]
    else:
        # Get session
        if args.user and args.key:
            session = prepare_session(args.user, args.key)
        else:
            session = prepare_session_from_env()
        
        # Fetch data from API
        print(f"Fetching tournament data for {args.tournament_id}...")
        tournament = get_tournament_data(session, args.tournament_id)
        
        print(f"Fetching participants for tournament {tournament.name}...")
        participants = get_participants_data(session, args.tournament_id)
        
        print(f"Fetching matches for tournament {tournament.name}...")
        matches = get_match_data(session, args.tournament_id)

        print("Writing tournament data JSON artifacts...")
        write_json_outputs(args.output, tournament, participants, matches)
    
    # Process the data (count wins/losses)
    print("Processing match outcomes...")
    updated_participants = count_outcomes(matches, participants)
    
    # Generate HTML
    print("Generating tournament dashboard HTML...")
    generate_static_tournament_page(
        tournament, 
        updated_participants, 
        matches, 
        args.output,
        custom_content=custom_content,
        logo_url=args.logo
    )
    
    print(f"Tournament dashboard generated: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()