#!/usr/bin/env python3
"""SCOUT v3 — 5000+ star repos only. Real signal, no noise."""
import os, json, time, urllib.request, urllib.parse
from pathlib import Path

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DATA_DIR = Path(__file__).parent.parent / "data"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ai-demand-pulse"
}

# Broad queries — star filter does the quality work
QUERIES = [
    # Core AI/LLM frameworks (catch the giants)
    ("stars:>5000 topic:llm",                           "AI Infrastructure"),
    ("stars:>5000 topic:langchain",                     "AI Infrastructure"),
    ("stars:>5000 topic:openai",                        "AI Infrastructure"),
    ("stars:>5000 topic:claude",                        "AI Infrastructure"),
    ("stars:>5000 topic:gemini",                        "AI Infrastructure"),
    ("stars:>5000 topic:ai-agent",                      "AI Infrastructure"),
    ("stars:>5000 topic:rag",                           "AI Infrastructure"),
    ("stars:>5000 topic:chatbot",                       "Customer Support"),
    ("stars:>5000 topic:llm-agent",                     "AI Infrastructure"),
    ("stars:>5000 topic:autonomous-agent",              "AI Infrastructure"),
    # Vertical: Finance
    ("stars:>5000 finance ai trading",                  "Financial Services"),
    ("stars:>5000 fintech llm",                         "Financial Services"),
    ("stars:>5000 quant trading ai",                    "Financial Services"),
    ("stars:>5000 fraud detection machine learning",    "Financial Services"),
    # Vertical: Healthcare
    ("stars:>5000 healthcare ai",                       "Healthcare"),
    ("stars:>5000 medical llm",                         "Healthcare"),
    ("stars:>5000 clinical ai nlp",                     "Healthcare"),
    ("stars:>5000 drug discovery ai",                   "Healthcare"),
    # Vertical: Legal
    ("stars:>5000 legal ai nlp",                        "Legal"),
    ("stars:>5000 contract analysis ai",                "Legal"),
    ("stars:>5000 compliance automation ai",            "Legal"),
    # Vertical: Education
    ("stars:>5000 education ai tutor",                  "Education"),
    ("stars:>5000 learning llm",                        "Education"),
    ("stars:>5000 ai teaching coding",                  "Education"),
    # Vertical: Sales & CRM
    ("stars:>5000 sales ai crm",                        "Sales"),
    ("stars:>5000 outreach email ai",                   "Sales"),
    # Vertical: Customer Support
    ("stars:>5000 customer service ai",                 "Customer Support"),
    ("stars:>5000 support chatbot llm",                 "Customer Support"),
    # Vertical: HR
    ("stars:>5000 recruiting ai resume",                "HR"),
    ("stars:>5000 hr automation ai",                    "HR"),
    # Vertical: Coding / DevTools
    ("stars:>5000 code generation ai",                  "DevTools"),
    ("stars:>5000 ai coding assistant",                 "DevTools"),
    ("stars:>5000 developer tools llm",                 "DevTools"),
    # Vertical: Data & Analytics
    ("stars:>5000 data analysis ai",                    "Data & Analytics"),
    ("stars:>5000 sql ai natural language",             "Data & Analytics"),
    # Vertical: Content / Marketing
    ("stars:>5000 content generation ai",               "Content"),
    ("stars:>5000 marketing ai copywriting",            "Content"),
    # General high-star AI
    ("stars:>5000 topic:artificial-intelligence",       "AI Infrastructure"),
    ("stars:>5000 topic:machine-learning",              "AI Infrastructure"),
    ("stars:>5000 topic:generative-ai",                 "AI Infrastructure"),
    ("stars:>5000 topic:gpt",                           "AI Infrastructure"),
    ("stars:>10000 ai agent workflow",                  "AI Infrastructure"),
    ("stars:>10000 ai automation",                      "AI Infrastructure"),
]

def search(q, per_page=30):
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q) + f"&sort=stars&order=desc&per_page={per_page}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
            # Handle rate limit message
            if "message" in data:
                print(f"    API msg: {data['message'][:80]}")
                return []
            return data.get("items", [])
    except Exception as e:
        print(f"    error: {e}")
        return []

def main():
    DATA_DIR.mkdir(exist_ok=True)
    seen = set()
    repos = []
    for i, (q, hint) in enumerate(QUERIES):
        print(f"  [{i+1}/{len(QUERIES)}] {q}")
        items = search(q, per_page=30)
        new = 0
        for item in items:
            if item["id"] in seen:
                continue
            stars = item.get("stargazers_count", 0)
            if stars < 5000:
                continue
            seen.add(item["id"])
            repos.append({
                "id": item["id"],
                "full_name": item["full_name"],
                "name": item["full_name"].split("/")[-1],
                "description": item.get("description") or "",
                "topics": item.get("topics", []),
                "language": item.get("language", ""),
                "stars": stars,
                "forks": item.get("forks_count", 0),
                "pushed_at": item.get("pushed_at", "")[:10],
                "html_url": item["html_url"],
                "hint_industry": hint,
            })
            new += 1
        print(f"     +{new} new (total: {len(repos)}, all 5k+ stars)")
        time.sleep(1.2)  # respect rate limit

    # Sort by stars descending
    repos.sort(key=lambda r: r["stars"], reverse=True)
    (DATA_DIR / "repos_raw.json").write_text(json.dumps(repos, indent=2))
    print(f"\n[SCOUT] {len(repos)} repos with 5000+ stars saved.")
    print(f"Top 5 by stars:")
    for r in repos[:5]:
        print(f"  {r['stars']:>7,} ⭐  {r['full_name']}")

if __name__ == "__main__":
    main()
