import os
import argparse
from dotenv import load_dotenv
from ..services.oauth_client import get_challonge_oauth_session

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Challonge OAuth CLI Tool")
    parser.add_argument("--client-id", type=str, default=os.environ.get("CHALLONGE_CLIENT_ID"), help="Challonge Client ID")
    parser.add_argument("--client-secret", type=str, default=os.environ.get("CHALLONGE_CLIENT_SECRET"), help="Challonge Client Secret")
    parser.add_argument("--redirect-uri", type=str, default=os.environ.get("CHALLONGE_REDIRECT_URI", "http://localhost:8080/callback"), help="Redirect URI")
    parser.add_argument("--api-url", type=str, default="https://api.challonge.com/v1/me.json", help="Challonge API endpoint to call after login")
    args = parser.parse_args()

    oauth_session = get_challonge_oauth_session(args.client_id, args.client_secret, args.redirect_uri)
    response = oauth_session.get(args.api_url)
    print("API Response:")
    print(response.json())

if __name__ == "__main__":
    main()