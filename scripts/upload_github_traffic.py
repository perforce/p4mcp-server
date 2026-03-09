"""
Fetch GitHub repo traffic (views, clones) and stars,
then upload to the Logstash endpoint as NDJSON — the same format
used by src/telemetry/upload_logs.py.

Intended to be run daily via GitHub Actions.
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def github_get(url, headers, params=None):
    """Make a GET request to the GitHub API with error handling."""
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_to_logstash(endpoint, docs):
    """Send a list of JSON-serialisable dicts to Logstash as NDJSON.

    This mirrors the format used by src/telemetry/upload_logs.send_request().
    """
    if not docs:
        logger.info("No documents to send — skipping.")
        return True

    ndjson_data = "\n".join(json.dumps(d) for d in docs) + "\n"

    resp = requests.post(
        endpoint,
        data=ndjson_data,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=30,
    )

    if resp.status_code != 200:
        logger.error(f"Logstash upload failed: {resp.status_code} {resp.text}")
        return False

    # Accept plain-text "ok" as well as JSON responses
    body = resp.text.strip()
    if body.lower() in ("ok", "success", "accepted"):
        logger.info(f"Upload successful (plain text): {body}")
        return True

    try:
        resp_json = resp.json()
        if resp_json.get("errors"):
            logger.error(f"Upload contained errors: {resp_json}")
            return False
        logger.info(f"Upload successful: {resp_json}")
    except json.JSONDecodeError:
        logger.warning(f"Non-JSON response (status 200): {body[:200]}")

    return True


def collect_stars(owner, repo, headers):
    """Fetch repo metadata (stars, forks, watchers, open issues)."""
    data = github_get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers)
    return {
        "event_type": "github_repo_stars",
        "repo": f"{owner}/{repo}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stargazers_count": data.get("stargazers_count", 0),
        "forks_count": data.get("forks_count", 0),
        "open_issues_count": data.get("open_issues_count", 0),
        "watchers_count": data.get("watchers_count", 0),
    }


def collect_traffic_views(owner, repo, headers):
    """Fetch daily traffic views — returns one doc per day bucket."""
    data = github_get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/traffic/views",
        headers,
        params={"per": "day"},
    )
    docs = []
    for bucket in data.get("views", []):
        docs.append({
            "event_type": "github_repo_traffic_views",
            "repo": f"{owner}/{repo}",
            "timestamp": bucket.get("timestamp"),
            "count": bucket.get("count", 0),
            "uniques": bucket.get("uniques", 0),
        })
    return docs


def collect_traffic_clones(owner, repo, headers):
    """Fetch daily traffic clones — returns one doc per day bucket."""
    data = github_get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/traffic/clones",
        headers,
        params={"per": "day"},
    )
    docs = []
    for bucket in data.get("clones", []):
        docs.append({
            "event_type": "github_repo_traffic_clones",
            "repo": f"{owner}/{repo}",
            "timestamp": bucket.get("timestamp"),
            "count": bucket.get("count", 0),
            "uniques": bucket.get("uniques", 0),
        })
    return docs


def main():
    # ── Read configuration from environment variables ──
    github_token = os.environ.get("GITHUB_TOKEN")
    logstash_endpoint = os.environ.get("LOGSTASH_ENDPOINT", "https://api.p4mcp.perforce.com")
    owner = os.environ.get("REPO_OWNER", "perforce")
    repo = os.environ.get("REPO_NAME", "p4mcp-server")

    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "p4mcp-traffic-uploader",
    }

    full_repo = f"{owner}/{repo}"
    all_docs = []
    had_errors = False

    # 1) Stars / repo metadata
    try:
        stars_doc = collect_stars(owner, repo, headers)
        all_docs.append(stars_doc)
        logger.info(f"Collected stars for {full_repo}: {stars_doc['stargazers_count']}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch repo metadata: {e}")
        had_errors = True

    # 2) Traffic views
    try:
        views_docs = collect_traffic_views(owner, repo, headers)
        all_docs.extend(views_docs)
        logger.info(f"Collected {len(views_docs)} traffic views records for {full_repo}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch traffic views: {e}")
        had_errors = True

    # 3) Traffic clones
    try:
        clones_docs = collect_traffic_clones(owner, repo, headers)
        all_docs.extend(clones_docs)
        logger.info(f"Collected {len(clones_docs)} traffic clones records for {full_repo}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch traffic clones: {e}")
        had_errors = True

    # ── Upload everything to Logstash in a single NDJSON request ──
    if all_docs:
        logger.info(f"Uploading {len(all_docs)} documents to {logstash_endpoint}")
        if not send_to_logstash(logstash_endpoint, all_docs):
            had_errors = True
    else:
        logger.warning("No data collected — nothing to upload.")

    if had_errors:
        logger.error("Completed with errors.")
        sys.exit(1)

    logger.info("All traffic data uploaded successfully.")


if __name__ == "__main__":
    main()
