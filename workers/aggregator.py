#!/usr/bin/env python3.11
"""
Aggregator worker: computes demand matrix and insights from classified repos.
Reads data/repos_classified.json, saves to data/demand_analysis.json
"""

import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    classified_path = DATA_DIR / "repos_classified.json"
    if not classified_path.exists():
        print("ERROR: %s not found -- run analyzer.py first" % classified_path)
        return

    with open(classified_path) as f:
        repos = json.load(f)

    print("AGGREGATOR: processing %d classified repos..." % len(repos))

    # 1. demand_matrix: {business_function: {industry: count}}
    demand_matrix = defaultdict(lambda: defaultdict(int))
    # 2. cluster counts and repo lists
    cluster_map = defaultdict(list)  # (bf, ind) -> list of {name, url}
    # 3. ai_tool counts
    by_ai_tool = defaultdict(int)
    # 4. function / industry counts
    bf_counts = defaultdict(int)
    ind_counts = defaultdict(int)

    for repo in repos:
        bf = repo.get("business_function", "Other")
        ind = repo.get("industry", "Other")
        tool = repo.get("ai_tool", "other")

        demand_matrix[bf][ind] += 1
        cluster_map[(bf, ind)].append(
            {"name": repo["full_name"], "url": repo["html_url"]}
        )
        by_ai_tool[tool] += 1
        bf_counts[bf] += 1
        ind_counts[ind] += 1

    # Convert demand_matrix to plain dict
    dm = {bf: dict(ind_dict) for bf, ind_dict in demand_matrix.items()}

    # top_clusters: top 15 by count
    clusters_sorted = sorted(cluster_map.items(), key=lambda x: len(x[1]), reverse=True)
    top_clusters = []
    for (bf, ind), repo_list in clusters_sorted[:15]:
        top_clusters.append(
            {
                "business_function": bf,
                "industry": ind,
                "count": len(repo_list),
                "repos": repo_list[:5],
            }
        )

    # trending_functions: top 10
    trending_functions = [
        {"business_function": bf, "count": cnt}
        for bf, cnt in sorted(bf_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # trending_industries: top 10
    trending_industries = [
        {"industry": ind, "count": cnt}
        for ind, cnt in sorted(ind_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # hot_insight: find the most surprising (non-SaaS, non-Other) high-concentration cluster
    surprise_candidates = [
        (bf, ind, cnt)
        for (bf, ind), repo_list in cluster_map.items()
        if bf != "Other"
        and ind not in ("Other", "SaaS & Developer Tools")
        for cnt in [len(repo_list)]
    ]
    surprise_candidates.sort(key=lambda x: x[2], reverse=True)
    if surprise_candidates:
        top_bf, top_ind, top_cnt = surprise_candidates[0]
        hot_insight = (
            "Highest unexpected concentration: %d repos targeting '%s' in '%s' -- "
            "real-world AI adoption is happening outside pure developer tooling."
            % (top_cnt, top_bf, top_ind)
        )
    else:
        # Fall back to the top cluster
        if top_clusters:
            tc = top_clusters[0]
            hot_insight = (
                "Top cluster: %d repos in '%s' x '%s'."
                % (tc["count"], tc["business_function"], tc["industry"])
            )
        else:
            hot_insight = "Insufficient data for insight."

    result = {
        "demand_matrix": dm,
        "top_clusters": top_clusters,
        "by_ai_tool": dict(by_ai_tool),
        "trending_functions": trending_functions,
        "trending_industries": trending_industries,
        "total_repos_analyzed": len(repos),
        "analysis_date": "2026-06-16",
        "hot_insight": hot_insight,
    }

    out_path = DATA_DIR / "demand_analysis.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print("AGGREGATOR: top 3 clusters:")
    for cluster in top_clusters[:3]:
        print(
            "  [%d repos] %s x %s"
            % (cluster["count"], cluster["business_function"], cluster["industry"])
        )

    print("AGGREGATOR: by_ai_tool: %s" % dict(by_ai_tool))
    print("AGGREGATOR: hot_insight: %s" % hot_insight)
    print("AGGREGATOR: saved -> %s" % out_path)


if __name__ == "__main__":
    main()
