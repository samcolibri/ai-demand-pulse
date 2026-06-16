#!/usr/bin/env python3.11
"""
Scout worker: fetches real GitHub repos using GitHub Search API.
Saves deduplicated results to data/repos_raw.json
"""

import json
import time
import base64
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DATA_DIR = Path(__file__).parent.parent / "data"

SEARCH_QUERIES = [
    "anthropic claude agent language:Python pushed:>2026-05-01",
    "openai codex automation language:Python pushed:>2026-05-01",
    "gemini google ai agent language:Python pushed:>2026-05-01",
    "llm workflow automation pushed:>2026-05-01",
    "ai agent business pushed:>2026-05-01 stars:>5",
]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ai-demand-pulse-scout/1.0",
}


def gh_get(url: str) -> dict | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  [rate-limit] {url}")
        elif e.code == 404:
            pass
        else:
            print(f"  [http {e.code}] {url}")
        return None
    except Exception as e:
        print(f"  [error] {url}: {e}")
        return None


def get_readme_snippet(full_name: str) -> str:
    url = f"https://api.github.com/repos/{full_name}/readme"
    data = gh_get(url)
    if not data or "content" not in data:
        return ""
    try:
        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return content[:300].strip()
    except Exception:
        return ""


def search_repos(query: str) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&per_page=30"
    print(f"  Searching: {query[:60]}...")
    data = gh_get(url)
    if not data or "items" not in data:
        return []
    return data["items"]


def collect_repos() -> list[dict]:
    seen_ids: set[int] = set()
    all_repos: list[dict] = []

    for query in SEARCH_QUERIES:
        items = search_repos(query)
        new_count = 0
        for item in items:
            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])

            # Small delay to avoid secondary rate limit on README fetches
            readme = get_readme_snippet(item["full_name"])
            time.sleep(0.3)

            repo = {
                "id": item["id"],
                "full_name": item["full_name"],
                "description": item.get("description") or "",
                "topics": item.get("topics") or [],
                "language": item.get("language") or "",
                "stargazers_count": item.get("stargazers_count", 0),
                "pushed_at": item.get("pushed_at") or "",
                "html_url": item.get("html_url") or "",
                "readme_snippet": readme,
            }
            all_repos.append(repo)
            new_count += 1

        print(f"    -> {new_count} new repos (total so far: {len(all_repos)})")
        time.sleep(1)  # between queries

    return all_repos


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("SCOUT: starting GitHub search...")
    repos = collect_repos()

    out_path = DATA_DIR / "repos_raw.json"
    with open(out_path, "w") as f:
        json.dump(repos, f, indent=2)

    print(f"SCOUT: collected {len(repos)} unique repos -> {out_path}")


if __name__ == "__main__":
    main()
