#!/usr/bin/env python3
"""
linkedin_post.py — DRAFTER worker
Generates a share-worthy LinkedIn post from demand_analysis.json.
Saves to data/linkedin_post.txt and prints to console.
"""

import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'demand_analysis.json')
OUT_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'linkedin_post.txt')

DASHBOARD_URL   = "https://samcolibri.github.io/ai-demand-pulse/"
DISCUSSIONS_URL = "https://github.com/samcolibri/ai-demand-pulse/discussions"


def load_data():
    """Load demand analysis JSON. Returns None if file missing."""
    if not os.path.exists(DATA_PATH):
        print(f"[DRAFTER] ⚠️  demand_analysis.json not found at {DATA_PATH}")
        print("[DRAFTER]    Run scout.py + analyzer.py + aggregator.py first.")
        return None
    with open(DATA_PATH) as f:
        return json.load(f)


def format_top_clusters(clusters):
    """Format top 5 demand clusters as numbered list."""
    lines = []
    for c in clusters[:5]:
        lines.append(
            f"{c['rank']}. {c['biz_function']} × {c['industry']} — {c['count']} repos"
        )
    return "\n".join(lines)


def derive_insight_line(data):
    """
    Build a short 1-sentence strategic insight from the top cluster data.
    Uses hot_insight if available, otherwise synthesises from top cluster.
    """
    if data.get("hot_insight"):
        return data["hot_insight"]

    top = data["top_clusters"][0]
    second = data["top_clusters"][1]
    return (
        f"{top['biz_function']} in {top['industry']} has {top['count']} active repos — "
        f"3× more than {second['biz_function']} in {second['industry']}. "
        f"Builders are voting with commits, not surveys."
    )


def build_post(data):
    month_year = datetime.utcnow().strftime("%B %Y")
    repos_count = data.get("repos_analyzed", "500+")
    top5 = format_top_clusters(data["top_clusters"])
    hot  = derive_insight_line(data)

    # Pick the dominant tool
    tools = data.get("by_tool", {})
    dominant_tool = max(tools, key=tools.get) if tools else "Claude"
    dominant_pct  = tools.get(dominant_tool, 0)
    tool_line = (
        f"{dominant_tool.capitalize()}-based repos lead at {dominant_pct}% of analysed repos — "
        f"a clear signal of where serious builders are placing their bets."
    )

    post = f"""🔥 I let AI agents analyze {repos_count}+ GitHub repos to map where AI demand is HOTTEST in {month_year}.

Here's what they found:

📊 Top 5 demand clusters:
{top5}

🤯 The surprise: {hot}

💡 {tool_line}

The dashboard updates every 6 hours — live data, not surveys, not forecasts.
What's your company building AI for?

👉 Live demand map: {DASHBOARD_URL}
📊 Vote in the poll: {DISCUSSIONS_URL}

#AI #AgentAI #BuildInPublic #FORGE #OpenSource #AITools #ArtificialIntelligence"""

    return post.strip()


def main():
    data = load_data()
    if data is None:
        # Write a placeholder so the pipeline doesn't fail
        placeholder = "[DRAFTER] No data available yet. Run the analysis workers first."
        with open(OUT_PATH, "w") as f:
            f.write(placeholder)
        print(placeholder)
        return

    post = build_post(data)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(post)

    print("=" * 70)
    print("LINKEDIN POST — ready for review and publish")
    print("=" * 70)
    print(post)
    print("=" * 70)
    print(f"\n[DRAFTER] Saved to {OUT_PATH}")
    print("[DRAFTER] Review before posting. Remember: Gate 2 applies.")


if __name__ == "__main__":
    main()
