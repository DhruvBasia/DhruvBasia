#!/usr/bin/env python3
"""Scrape the public GitHub contribution calendar. No token, no GraphQL.

GitHub serves the same HTML fragment the profile page uses at
https://github.com/users/<username>/contributions -- it's public, so all we
need is requests + BeautifulSoup.

Writes data/contributions.json with the raw days plus derived stats.
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "DhruvBasia")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art bot; +https://github.com/%s)" % USERNAME,
    "Accept": "text/html",
    "X-Requested-With": "XMLHttpRequest",
}

COUNT_RE = re.compile(r"^(No|[\d,]+)\s+contribution")


def fetch_html() -> str:
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Tooltips carry the counts; day cells carry date + level. Join on cell id.
    counts = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        m = COUNT_RE.match(tip.get_text(" ", strip=True))
        if m:
            raw = m.group(1)
            counts[target] = 0 if raw == "No" else int(raw.replace(",", ""))

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        days.append(
            {
                "date": d,
                "count": counts.get(cell.get("id"), 0),
                "level": int(cell.get("data-level") or 0),
            }
        )

    if not days:
        raise SystemExit("No day cells found -- GitHub may have changed its markup.")

    days.sort(key=lambda x: x["date"])
    return {"days": days, "total": sum(d["count"] for d in days)}


def streaks(days):
    """Current and longest run of consecutive active days.

    Today is excluded from breaking the current streak -- a day that hasn't
    happened yet shouldn't zero out yesterday's work.
    """
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    today = date.today().isoformat()
    current = 0
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            current += 1
        elif d["date"] == today:
            continue  # today is still young
        else:
            break
    return current, longest


def derive(parsed: dict) -> dict:
    days = parsed["days"]
    active = [d for d in days if d["count"] > 0]
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    return {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "total": parsed["total"],
        "active_days": len(active),
        "max_count": best["count"],
        "best_day": {"date": best["date"], "count": best["count"]},
        "current_streak": current,
        "longest_streak": longest,
        "monthly": dict(sorted(monthly.items())),
        "days": days,
    }


def main():
    data = derive(parse(fetch_html()))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(
        f"{OUT.relative_to(ROOT)}: {data['total']} contributions, "
        f"{data['active_days']} active days, streak {data['current_streak']}"
    )


if __name__ == "__main__":
    sys.exit(main())
