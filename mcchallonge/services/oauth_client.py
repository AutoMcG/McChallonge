from requests_oauthlib import OAuth2Session

CHALLONGE_AUTH_BASE_URL = "https://api.challonge.com/oauth/authorize"
CHALLONGE_TOKEN_URL = "https://api.challonge.com/oauth/token"

def get_challonge_oauth_session(client_id, client_secret, redirect_uri, scope=None):
    # Step 1: User Authorization.
    scope = "me tournaments:read matches:read participants:read communities:manage"
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope, pkce="S256")
    authorization_url, state = oauth.authorization_url(CHALLONGE_AUTH_BASE_URL, community_id="McChallonge")

    print(f"Go to the following URL to authorize: {authorization_url}")    

    # Step 2: Get the authorization verifier code from the callback url
    redirect_response = input("Paste the full redirect URL here: ")

    # Step 3: Fetch the access token
    token = oauth.fetch_token(
        CHALLONGE_TOKEN_URL,
        authorization_response=redirect_response,
        client_secret=client_secret,
    )

    print("Access token obtained:", token)
    return oauth  # This session can be used for authenticated requests

# Usage example:
# client_id = os.environ["CHALLONGE_CLIENT_ID"]
# client_secret = os.environ["CHALLONGE_CLIENT_SECRET"]
# redirect_uri = "http://localhost:8080/callback"
# oauth_session = get_challonge_oauth_session(client_id, client_secret, redirect_uri)
# response = oauth_session.get("https://api.challonge.com/v1/me.json")
# print(response.json())