#!/usr/bin/env python3.11
"""
Analyzer worker: classifies repos using Claude Haiku.
Reads data/repos_raw.json, saves to data/repos_classified.json
"""

import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

BUSINESS_FUNCTIONS = [
    "Sales & Outreach",
    "Customer Support",
    "Finance & Accounting",
    "HR & Recruiting",
    "Legal & Compliance",
    "Operations & Logistics",
    "Product Development",
    "Data & Analytics",
    "IT & Security",
    "Content & Marketing",
    "Healthcare & Clinical",
    "Education & Training",
    "Research & Science",
    "DevOps & Infrastructure",
    "Other",
]

INDUSTRIES = [
    "Financial Services",
    "Healthcare",
    "Education",
    "Real Estate",
    "Retail & E-commerce",
    "Manufacturing & Industrial",
    "Legal & Professional Services",
    "Media & Entertainment",
    "Government & Public Sector",
    "SaaS & Developer Tools",
    "Consulting & Agency",
    "Energy & Utilities",
    "Transportation & Logistics",
    "HR & Workforce",
    "Other",
]

SYSTEM_PROMPT = (
    "You are a B2B software analyst. Classify GitHub AI/LLM repos by business function and industry.\n\n"
    "Valid business_function values (pick exactly one):\n"
    + ", ".join(BUSINESS_FUNCTIONS)
    + "\n\nValid industry values (pick exactly one):\n"
    + ", ".join(INDUSTRIES)
    + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
)


def call_claude(messages, retries=4):
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    body = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data["content"][0]["text"]
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            if e.code == 429:
                wait = 13 * (attempt + 1)
                print("  [rate-limit] waiting %ds before retry %d..." % (wait, attempt + 1))
                time.sleep(wait)
                continue
            print("  [claude http %d] %s" % (e.code, body_text[:200]))
            return None
        except Exception as e:
            print("  [claude error] %s" % e)
            return None
    print("  [claude] exhausted retries")
    return None


def build_batch_prompt(repos):
    lines = []
    for i, repo in enumerate(repos):
        lines.append("--- Repo %d ---" % (i + 1))
        lines.append("Name: %s" % repo["full_name"])
        lines.append("Description: %s" % repo["description"][:200])
        lines.append("Topics: %s" % ", ".join(repo["topics"][:10]))
        lines.append("Language: %s" % repo["language"])
        lines.append("README: %s" % repo["readme_snippet"][:250])
        lines.append("")
    prompt = "\n".join(lines)
    prompt += (
        "\nReturn a JSON array of %d objects, one per repo, in order. "
        "Each object: business_function, industry, confidence (0.0-1.0), "
        "ai_tool (claude|codex|gemini|other), use_case_summary." % len(repos)
    )
    return prompt


def parse_classifications(text, count):
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            arr = json.loads(text[start : end + 1])
            if isinstance(arr, list):
                return arr
        except Exception:
            pass
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return [obj]
    except Exception:
        pass
    return []


def validate_classification(cls):
    bf = cls.get("business_function", "Other")
    if bf not in BUSINESS_FUNCTIONS:
        bf = "Other"
    ind = cls.get("industry", "Other")
    if ind not in INDUSTRIES:
        ind = "Other"
    return {
        "business_function": bf,
        "industry": ind,
        "confidence": float(cls.get("confidence", 0.5)),
        "ai_tool": cls.get("ai_tool", "other"),
        "use_case_summary": cls.get("use_case_summary", ""),
    }


def classify_batch(repos):
    prompt = build_batch_prompt(repos)
    messages = [{"role": "user", "content": prompt}]
    response = call_claude(messages)
    if not response:
        return [None] * len(repos)

    parsed = parse_classifications(response, len(repos))
    if len(parsed) != len(repos):
        print("  [warn] expected %d results, got %d" % (len(repos), len(parsed)))
        while len(parsed) < len(repos):
            parsed.append({})

    results = []
    for cls in parsed[: len(repos)]:
        try:
            results.append(validate_classification(cls))
        except Exception:
            results.append(None)
    return results


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    raw_path = DATA_DIR / "repos_raw.json"
    if not raw_path.exists():
        print("ERROR: %s not found -- run scout.py first" % raw_path)
        return

    with open(raw_path) as f:
        repos = json.load(f)

    out_path = DATA_DIR / "repos_classified.json"

    # Resume: load existing classified output if present
    existing_by_id = {}
    if out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)
        for r in existing:
            if not r.get("classification_error"):
                existing_by_id[r["id"]] = r
        print("ANALYZER: resuming -- %d already classified, %d remaining" % (
            len(existing_by_id), len(repos) - len(existing_by_id)
        ))

    # Only classify repos that failed or are missing
    todo = [r for r in repos if r["id"] not in existing_by_id]
    total = len(repos)

    if todo:
        print("ANALYZER: classifying %d remaining repos with %s..." % (len(todo), CLAUDE_MODEL))

    newly_classified = {}
    processed = 0
    batch_size = 5

    for i in range(0, len(todo), batch_size):
        batch = todo[i : i + batch_size]
        results = classify_batch(batch)

        for repo, cls in zip(batch, results):
            if cls:
                entry = dict(repo)
                entry.update(cls)
                newly_classified[repo["id"]] = entry
            processed += 1

        print("ANALYZER: classified %d/%d remaining repos" % (processed, len(todo)))
        if i + batch_size < len(todo):
            time.sleep(13)  # 5 req/min rate limit => ~12s between batches

    # Merge: preserve order from raw
    classified = []
    for repo in repos:
        rid = repo["id"]
        if rid in newly_classified:
            classified.append(newly_classified[rid])
        elif rid in existing_by_id:
            classified.append(existing_by_id[rid])
        else:
            entry = dict(repo)
            entry.update({
                "business_function": "Other",
                "industry": "Other",
                "confidence": 0.0,
                "ai_tool": "other",
                "use_case_summary": "",
                "classification_error": True,
            })
            classified.append(entry)

    with open(out_path, "w") as f:
        json.dump(classified, f, indent=2)

    success = sum(1 for r in classified if not r.get("classification_error"))
    print("ANALYZER: done. %d/%d classified successfully -> %s" % (success, total, out_path))


if __name__ == "__main__":
    main()
