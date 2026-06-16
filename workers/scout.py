#!/usr/bin/env python3
"""SCOUT v2 — targets 500+ repos across all major AI verticals"""
import os, json, time, urllib.request, urllib.parse
from pathlib import Path

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DATA_DIR = Path(__file__).parent.parent / "data"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ai-demand-pulse-forge"
}

QUERIES = [
    # Financial Services
    ("ai finance compliance automation", "Financial Services"),
    ("claude openai banking risk management", "Financial Services"),
    ("llm invoice accounts payable", "Financial Services"),
    ("ai fraud detection insurance claims", "Financial Services"),
    ("openai fintech payments", "Financial Services"),
    ("llm tax accounting automation", "Financial Services"),
    ("ai trading crypto investment", "Financial Services"),
    # Healthcare
    ("ai healthcare clinical decision support", "Healthcare"),
    ("llm medical diagnosis ehr", "Healthcare"),
    ("claude health records patient", "Healthcare"),
    ("openai radiology pathology imaging", "Healthcare"),
    ("ai mental health therapy chatbot", "Healthcare"),
    ("llm drug discovery pharma", "Healthcare"),
    # Legal
    ("ai legal contract review analysis", "Legal"),
    ("llm lawyer document legal", "Legal"),
    ("claude compliance contract ai", "Legal"),
    ("openai legal research case", "Legal"),
    ("ai paralegal automation", "Legal"),
    # Education
    ("ai education tutor personalized learning", "Education"),
    ("llm student teacher grading", "Education"),
    ("openai coursework curriculum", "Education"),
    ("ai homework quiz generator", "Education"),
    ("claude tutoring adaptive", "Education"),
    # Sales & CRM
    ("ai sales outreach personalization crm", "Sales"),
    ("claude sdr email sequence", "Sales"),
    ("llm lead generation pipeline sales", "Sales"),
    ("openai sales copilot hubspot", "Sales"),
    # Customer Support
    ("ai customer support helpdesk chatbot", "Customer Support"),
    ("llm ticket triage support automation", "Customer Support"),
    ("claude customer service agent", "Customer Support"),
    ("openai support whatsapp telegram bot", "Customer Support"),
    ("ai call center voice agent", "Customer Support"),
    # HR & Recruiting
    ("ai recruiting resume screening ats", "HR"),
    ("llm hr onboarding employee", "HR"),
    ("openai job description interview", "HR"),
    ("ai talent acquisition workforce", "HR"),
    # Real Estate
    ("ai real estate property listing", "Real Estate"),
    ("llm mortgage property valuation", "Real Estate"),
    ("openai real estate agent assistant", "Real Estate"),
    # Retail & E-commerce
    ("ai ecommerce product recommendation", "Retail"),
    ("llm shopping assistant retail", "Retail"),
    ("openai inventory pricing retail", "Retail"),
    # Media & Content
    ("ai content creation marketing copy", "Media"),
    ("llm social media post generator", "Media"),
    ("claude copywriting content", "Media"),
    # DevTools (keep some)
    ("claude code agent developer tools", "DevTools"),
    ("codex automation workflow", "DevTools"),
    ("gemini developer api assistant", "DevTools"),
]

def search_github(query, per_page=20):
    encoded = urllib.parse.quote(query + " pushed:>2026-03-01")
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=updated&per_page={per_page}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("items", [])
    except Exception as e:
        print(f"  [SCOUT] failed: {query[:40]} — {e}")
        return []

def get_readme(full_name):
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{full_name}/readme",
            headers=HEADERS
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            import base64
            content = base64.b64decode(json.loads(r.read()).get("content","")).decode("utf-8", errors="ignore")
            return content[:500].strip()
    except:
        return ""

def main():
    DATA_DIR.mkdir(exist_ok=True)
    seen_ids = set()
    repos = []
    for i, (query, hint) in enumerate(QUERIES):
        print(f"  [{i+1}/{len(QUERIES)}] {query[:50]}")
        items = search_github(query, per_page=20)
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
                    "hint_industry": hint,
                })
                new += 1
        print(f"     +{new} new (total: {len(repos)})")
        time.sleep(1.5)
    (DATA_DIR / "repos_raw.json").write_text(json.dumps(repos, indent=2))
    print(f"\n[SCOUT] Done. {len(repos)} repos saved.")

if __name__ == "__main__":
    main()
