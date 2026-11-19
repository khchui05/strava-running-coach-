"""Download your running activities from the Strava API into data/00-raw/.

One-time setup (see README "Connecting to Strava"):
  1. Create an API app at https://www.strava.com/settings/api
  2. Copy .env.example to .env and fill in STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET
  3. Run:  python modules/get_data.py --auth
     Follow the link, approve access, and paste the `code=` value from the redirect URL.
     This saves STRAVA_REFRESH_TOKEN to .env.

After that, just run:
    python modules/get_data.py

Your .env file holds secrets. It is listed in .gitignore. Never commit it.
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request

ENV_PATH = ".env"
RAW_PATH = os.path.join("data", "00-raw", "strava_activities.json")
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"


def load_env(path=ENV_PATH):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def save_env_value(key, value, path=ENV_PATH):
    lines = open(path).read().splitlines() if os.path.exists(path) else []
    lines = [l for l in lines if not l.startswith(f"{key}=")] + [f"{key}={value}"]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def authorize(env):
    """One-time OAuth flow: get a refresh token with permission to read your activities."""
    params = {
        "client_id": env["STRAVA_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": "http://localhost",
        "approval_prompt": "force",
        "scope": "activity:read_all",
    }
    print("Open this link, click Authorize, then copy the `code=` value from the URL you land on")
    print("(the page itself will fail to load; that's expected):\n")
    print("https://www.strava.com/oauth/authorize?" + urllib.parse.urlencode(params) + "\n")
    code = input("Paste the code here: ").strip()
    tok = post(TOKEN_URL, {
        "client_id": env["STRAVA_CLIENT_ID"],
        "client_secret": env["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
    })
    save_env_value("STRAVA_REFRESH_TOKEN", tok["refresh_token"])
    print("Saved STRAVA_REFRESH_TOKEN to .env")


def access_token(env):
    tok = post(TOKEN_URL, {
        "client_id": env["STRAVA_CLIENT_ID"],
        "client_secret": env["STRAVA_CLIENT_SECRET"],
        "refresh_token": env["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    if tok.get("refresh_token") and tok["refresh_token"] != env["STRAVA_REFRESH_TOKEN"]:
        save_env_value("STRAVA_REFRESH_TOKEN", tok["refresh_token"])  # Strava may rotate it
    return tok["access_token"]


def fetch_all_activities(token, per_page=200):
    """Page through every activity. Strava allows roughly 100 requests per 15 minutes."""
    activities, page = [], 1
    while True:
        url = f"{ACTIVITIES_URL}?{urllib.parse.urlencode({'per_page': per_page, 'page': page})}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as r:
            batch = json.load(r)
        if not batch:
            break
        activities.extend(batch)
        print(f"page {page}: {len(batch)} activities (total {len(activities)})")
        page += 1
        time.sleep(1)
    return activities


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--auth", action="store_true", help="run the one-time authorization step")
    args = parser.parse_args()

    env = load_env()
    missing = [k for k in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET") if not env.get(k)]
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)} in .env (copy .env.example to .env first).")

    if args.auth or not env.get("STRAVA_REFRESH_TOKEN"):
        authorize(env)
        env = load_env()

    acts = fetch_all_activities(access_token(env))
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    with open(RAW_PATH, "w") as f:
        json.dump(acts, f)
    print(f"Saved {len(acts)} activities to {RAW_PATH}")
