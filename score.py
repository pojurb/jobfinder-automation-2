#!/usr/bin/env python3
"""
Job Scoring Engine
Matches scraped jobs against CV profile using weighted keyword analysis.
"""

import os
import re
import json
import argparse

JOBS_DIR = "jobs"
PROFILE_FILE = "profile.json"


def load_profile():
    """Load profile keywords and weights from profile.json."""
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_job(filepath):
    """Parse a job markdown file and return metadata + body."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)

    if len(parts) < 3:
        return None

    frontmatter = parts[1].strip()
    body = parts[2].strip()

    metadata = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == "match_score":
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            metadata[key] = value

    return {"metadata": metadata, "body": body}


def keyword_score(job_text, profile):
    """
    Calculate weighted keyword match score (0-100).

    Approach: Score each category independently, then compute a weighted average.
    For each category, matching just 2-3 keywords earns full credit (threshold = max(2, 20% of keywords)).
    This avoids the problem of low scores when total keyword count is large.

    Formula per category:
        category_score = min(matched_count / threshold, 1.0)
    Final:
        score = sum(category_score * weight) / sum(weight) * 100
    """
    import math

    text_lower = job_text.lower()

    total_weighted_score = 0
    total_weight = 0
    breakdown = []

    for category in profile.get("categories", []):
        weight = category.get("weight", 1)
        keywords = category.get("keywords", [])

        if not keywords:
            continue

        matched = [kw for kw in keywords if kw.lower() in text_lower]
        matches = len(matched)

        # Threshold: matching ~20% of a category's keywords gives full credit,
        # but at least 2 matches required for full credit
        threshold = max(2, math.ceil(len(keywords) * 0.20))
        category_score = min(matches / threshold, 1.0)

        total_weighted_score += category_score * weight
        total_weight += weight

        if matches > 0:
            breakdown.append(
                {
                    "category": category["name"],
                    "matched": matches,
                    "total": len(keywords),
                    "weight": weight,
                    "pct": round(category_score * 100),
                    "keywords_hit": matched[:5],
                }
            )

    if total_weight == 0:
        return 0, []

    score = round((total_weighted_score / total_weight) * 100)
    return min(score, 100), breakdown


def update_job_score(filepath, new_score):
    """Update the match_score field in a job's YAML frontmatter."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace existing match_score line
    updated = re.sub(
        r"^match_score:\s*\d+",
        f"match_score: {new_score}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)


def main():
    parser = argparse.ArgumentParser(description="Job Scoring Engine")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI scoring phase")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show score breakdowns"
    )
    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("  🧠 Job Scoring Engine")
    print("=" * 50)

    # Load profile
    try:
        profile = load_profile()
        print(f"  📄 Loaded profile: {profile.get('name', 'Unknown')}")
        print(
            f"  🏷️  {len(profile.get('categories', []))} keyword categories, "
            f"{sum(len(c.get('keywords', [])) for c in profile.get('categories', []))} total keywords"
        )
    except FileNotFoundError:
        print("  ❌ profile.json not found! Run the pipeline first.")
        return
    except json.JSONDecodeError as e:
        print(f"  ❌ profile.json parse error: {e}")
        return

    if not os.path.exists(JOBS_DIR):
        print(f"  ❌ {JOBS_DIR}/ directory not found!")
        return

    # Score each job
    scored = 0
    high_matches = 0
    results = []

    for filename in sorted(os.listdir(JOBS_DIR)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(JOBS_DIR, filename)
        job = load_job(filepath)
        if not job:
            continue

        # Combine all text fields for scoring
        full_text = " ".join(
            [
                job["metadata"].get("title", "") * 3,  # Title weighted 3x
                job["metadata"].get("company", ""),
                job["metadata"].get("location", ""),
                job["metadata"].get("work_type", ""),
                job["body"],
            ]
        )

        score, breakdown = keyword_score(full_text, profile)
        update_job_score(filepath, score)
        scored += 1

        title = job["metadata"].get("title", "Unknown")[:45]
        source = job["metadata"].get("source", "")

        if score >= 90:
            high_matches += 1
            indicator = "🟢"
        elif score >= 70:
            indicator = "🔵"
        elif score >= 50:
            indicator = "🟡"
        else:
            indicator = "⚪"

        results.append((score, indicator, title, source))

        if args.verbose and breakdown:
            print(f"\n  {indicator} {score:>3}  {title}")
            for b in breakdown:
                print(
                    f"        ├─ {b['category']}: {b['matched']}/{b['total']} "
                    f"(×{b['weight']}) → {', '.join(b['keywords_hit'])}"
                )

    # Print summary sorted by score
    if not args.verbose:
        print(f"\n  {'Score':<8} {'Title':<47} {'Source':<12}")
        print(f"  {'─' * 8} {'─' * 47} {'─' * 12}")
        for score, indicator, title, source in sorted(
            results, key=lambda x: x[0], reverse=True
        ):
            print(f"  {indicator} {score:>3}   {title:<47} {source:<12}")

    print(f"\n  {'─' * 50}")
    print(f"  📊 Scored {scored} jobs | 🟢 {high_matches} high matches (90+)")
    print(f"  {'─' * 50}\n")


if __name__ == "__main__":
    main()
