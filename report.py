#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

REPOS = [
    "https://github.com/Grimfeather/azerothcore-wotlk",
    "https://github.com/Grimfeather/mod-individual-progression",
    "https://github.com/mod-playerbots/mod-playerbots",
    "https://github.com/hermensbas/mod_weather_vibe",
    "https://github.com/jrad7/mod-dungeon-clear",
    "https://github.com/silviu20092/mod-easy-respawn",
    "https://github.com/buildthehomelab/wow-mod-junk-to-gold-plus",
    "https://github.com/Lichborne-AC/mod-levelsync",
    "https://github.com/azerothcore/mod-morphsummon",
    "https://github.com/Wishmaster117/mod-multibot-bridge",
    "https://github.com/pangolp/mod-quest-loot-party",
    "https://github.com/buildthehomelab/mod-reagent-bank-account",
    "https://github.com/Zerathane/mod-token-turnin",
    "https://github.com/buildthehomelab/wow-mod-transmog-plus",
    "https://github.com/ThiagoSBarreto/mod-travelers-recall",
    "https://github.com/buildthehomelab/wow-mod-ah-bot-plus",
    "https://github.com/buildthehomelab/wow-mod-retail-ah",
    "https://github.com/buildthehomelab/wow-mod-retail-professions",
]

def get_repo_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Bad repo URL: {url}")
    return parts[0], parts[1]

def repo_emoji(count):
    if count >= 10:
        return "🟢"
    elif count >= 5:
        return "🔵"
    elif count >= 2:
        return "🟠"
    elif count == 1:
        return "🟡"
    return "⚪"

def overall_embed_color(rows):
    if not rows:
        return 0x7F8C8D  # gray

    highest_count = max(count for count, _ in rows)

    if highest_count >= 10:
        return 0x2ECC71  # green
    elif highest_count >= 5:
        return 0x3498DB  # blue
    elif highest_count >= 2:
        return 0xF39C12  # orange
    else:
        return 0xE67E22  # dark orange

def count_commits_last_24h(owner, repo):
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "commit-report-bot",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    params = {"since": since, "per_page": 100}
    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 404:
        return 0

    if response.status_code == 403:
        print(f"GitHub API issue for {owner}/{repo}: {response.text}")
        return 0

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError:
        print(f"Could not parse JSON for {owner}/{repo}")
        return 0

    if isinstance(data, list):
        return len(data)
    return 0

def build_embed():
    rows = []
    for repo_url in REPOS:
        owner, repo = get_repo_from_url(repo_url)
        count = count_commits_last_24h(owner, repo)
        if count > 0:
            rows.append((count, repo_url))

    rows.sort(key=lambda x: (-x[0], x[1]))

    if not rows:
        embed = {
            "title": "Daily Commit Report",
            "description": "No repositories had commits in the last 24 hours.",
            "color": 0x7F8C8D,
            "author": {
                "name": "Commit Watcher"
            },
            "footer": {
                "text": "Last 24 hours • UTC"
            }
        }
        return {
            "content": "",
            "embeds": [embed],
        }

    fields = []
    for count, repo_url in rows:
        emoji = repo_emoji(count)
        label = f"{count} commit{'s' if count != 1 else ''}"
        fields.append({
            "name": f"{emoji} {label}",
            "value": repo_url,
            "inline": False
        })

    embed = {
        "title": "Daily Commit Report",
        "description": "Repositories with new commits in the last 24 hours.",
        "color": overall_embed_color(rows),
        "author": {
            "name": "Commit Watcher"
        },
        "fields": fields,
        "footer": {
            "text": "Last 24 hours • UTC"
        }
    }

    return {
        "content": "",
        "embeds": [embed],
    }

def send_to_discord(payload):
    if not DISCORD_WEBHOOK:
        raise RuntimeError("DISCORD_WEBHOOK_URL is missing")

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        DISCORD_WEBHOOK,
        data=json.dumps(payload),
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    print("Discord message sent")

if __name__ == "__main__":
    payload = build_embed()
    send_to_discord(payload)
