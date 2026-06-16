#!/usr/bin/env python3
"""
SCOUT — GitHub repo collector for ai-demand-pulse.
Uses industry-targeted queries to find AI being applied in REAL business verticals.
"""
import os, json, time, urllib.request, urllib.parse
from pathlib import Path

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DATA_DIR = Path(__file__).parent.parent / "data"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ai-demand-pulse-forge"
}

# Industry-targeted queries — designed to surface VERTICAL AI use cases, not just dev tools
QUERIES = [
    # Financial Services
    ("ai finance compliance", "Financial Services"),
    ("claude openai banking risk", "Financial Services"),
    ("llm invoice accounting", "Financial Services"),
    ("ai fraud detection insurance", "Financial Services"),
    # Healthcare
    ("ai healthcare clinical", "Healthcare"),
    ("llm medical diagnosis patient", "Healthcare"),
    ("claude health records ehr", "Healthcare"),
    ("openai radiology pathology", "Healthcare"),
    # Legal
    ("ai legal contract review", "Legal"),
    ("llm lawyer document analysis", "Legal"),
    ("claude legal compliance", "Legal"),
    # Education
    ("ai education tutor student", "Education"),
    ("llm learning personalized", "Education"),
    ("openai coursework grading", "Education"),
    # Sales & CRM
    ("ai sales outreach crm hubspot", "Sales"),
    ("claude sdr email personalized", "Sales"),
    ("llm lead generation pipeline", "Sales"),
    # Customer Support
    ("ai customer support chatbot", "Customer Support"),
    ("llm helpdesk ticket triage", "Customer Support"),
    ("claude support automation", "Customer Support"),
    # HR & Recruiting
    ("ai recruiting resume screening", "HR"),
    ("llm hr onboarding employee", "HR"),
    # Real Estate
    ("ai real estate property", "Real Estate"),
    # Retail & E-commerce
    ("ai ecommerce product recommendation", "Retail"),
    ("llm shopping customer retail", "Retail"),
    # DevTools (keep some)
    ("claude code agent developer", "DevTools"),
    ("codex automation workflow", "DevTools"),
    ("gemini developer tool api", "DevTools"),
]

def search_github(query: str, per_page: int = 15) -> list:
    encoded = urllib.parse.quote(query + " pushed:>2026-04-01")
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=updated&per_page={per_page}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("items", [])
    except Exception as e:
        print(f"  [SCOUT] search failed for '{query}': {e}")
        return []

def get_readme(full_name: str) -> str:
    url = f"https://api.github.com/repos/{full_name}/readme"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            import base64
            content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
            return content[:400].strip()
    except:
        return ""

def main():
    DATA_DIR.mkdir(exist_ok=True)
    seen_ids = set()
    repos = []
    
    for query, hint_industry in QUERIES:
        print(f"  [SCOUT] searching: {query}")
        items = search_github(query)
        new = 0
        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                readme = get_readme(item["full_name"])
                repos.append({
                    "id": item["id"],
                    "full_name": item["full_name"],
                    "name": item["full_name"].split("/")[-1],
                    "description": item.get("description") or "",
                    "topics": item.get("topics", []),
                    "language": item.get("language", ""),
                    "stars": item.get("stargazers_count", 0),
                    "pushed_at": item.get("pushed_at", ""),
                    "html_url": item.get("html_url", ""),
                    "readme_snippet": readme,
                    "hint_industry": hint_industry,
                })
                new += 1
        print(f"  [SCOUT] +{new} new repos (total: {len(repos)})")
        time.sleep(2)  # respect rate limits
    
    out = DATA_DIR / "repos_raw.json"
    out.write_text(json.dumps(repos, indent=2))
    print(f"\n[SCOUT] Done. {len(repos)} unique repos saved to {out}")

if __name__ == "__main__":
    main()
