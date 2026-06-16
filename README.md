# AI Demand Pulse 🔥

> Which industries are hungry for AI solutions in June 2026?

**Live dashboard:** https://samcolibri.github.io/ai-demand-pulse/

FORGE agents analyze 500+ GitHub repos built with Claude, Codex, and Gemini every 6 hours.
They classify each repo by business function × industry and surface the demand clusters.

## What you're seeing

This is a live intelligence feed, not a survey. Real repos. Real builders. Real demand signals.

## How it works

```
GitHub repos (Claude/Codex/Gemini)
  → SCOUT     (discover 500+ repos via GitHub API)
  → ANALYZER  (Claude classifies each by biz function + industry)
  → AGGREGATOR (aggregate into demand clusters + heatmap)
  → Dashboard  (GitHub Pages, auto-updated every 6h)
```

Runs every 6 hours via GitHub Actions. Zero infra cost.

## Vote on what AI should solve next

→ [Open the poll in GitHub Discussions](../../discussions)

Your vote influences what FORGE agents analyze next.

## Built with

- **FORGE** — Autonomous outcome OS
- **Hephaestus** — Worker fleet orchestration
- **agmsg** — Agent messaging layer
- **Claude** (Anthropic) — Repo classification engine
- **GitHub Actions** — Zero-cost 6h cron

## Dashboard Sections

| Section | What it shows |
|---------|--------------|
| Heatmap | Business function × industry demand intensity |
| Top 10 Clusters | Ranked demand clusters with repo evidence |
| By AI Tool | Claude / Codex / Gemini breakdown |
| Hot Insight | Most surprising finding from the latest cycle |
| Live Feed | Last 10 repos classified |

## Run it yourself

```bash
git clone https://github.com/samcolibri/ai-demand-pulse
cd ai-demand-pulse
pip install anthropic requests

# Discover repos
python3 workers/scout.py

# Classify with Claude
ANTHROPIC_API_KEY=your_key python3 workers/analyzer.py

# Build dashboard data
python3 workers/aggregator.py

# Generate LinkedIn post
python3 workers/linkedin_post.py

# Open locally
open docs/index.html
```

## Repository Structure

```
ai-demand-pulse/
├── docs/
│   └── index.html          # GitHub Pages dashboard
├── workers/
│   ├── scout.py            # SCOUT: GitHub repo discovery
│   ├── analyzer.py         # ANALYZER: Claude classification
│   ├── aggregator.py       # AGGREGATOR: data aggregation
│   └── linkedin_post.py    # DRAFTER: LinkedIn post generation
├── data/
│   ├── demand_analysis.json    # Aggregated heatmap + clusters
│   ├── repos_classified.json   # Per-repo classification records
│   └── linkedin_post.txt       # Latest generated post
├── .github/
│   └── workflows/
│       └── demand_pulse.yml    # 6h GitHub Actions workflow
└── OUTCOME.md              # FORGE soul document
```

## Data Schema

`data/demand_analysis.json`
```json
{
  "repos_analyzed": 512,
  "industries_tracked": 15,
  "updated_at": "2026-06-16T00:00:00Z",
  "next_update_hours": 6,
  "heatmap": { "Healthcare": { "Document Processing": { "count": 24, "top_repo": "..." } } },
  "top_clusters": [
    { "rank": 1, "biz_function": "...", "industry": "...", "count": 24, "repos": ["..."] }
  ],
  "by_tool": { "claude": 38, "codex": 27, "gemini": 22, "other": 13 },
  "hot_insight": "..."
}
```

## Gates

Per the FORGE OUTCOME.md, two human gates apply:

- **Gate 1** — Classification taxonomy and first 25 repos reviewed before full-batch
- **Gate 2** — Top 10 clusters, dashboard layout, and LinkedIn post approved before public deploy

---

*Powered by FORGE × Hephaestus × agmsg · Open source · Updates every 6 hours*
