#!/usr/bin/env python3
"""Draw assets/contributions-{dark,light}.svg from the last year of GitHub activity.

    GH_TOKEN=... GH_USER=amrit-sapkota python3 scripts/update_contributions.py
    python3 scripts/update_contributions.py --sample    # made-up data, for previews

The calendar includes private contributions because the profile shares their
counts publicly, so the workflow's GITHUB_TOKEN is enough.
"""
import argparse
import datetime as dt
import json
import os
import random
import urllib.request

from svgkit import THEMES, document, measure, text, write

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      restrictedContributionsCount
      contributionCalendar { weeks { contributionDays { date contributionCount weekday } } }
    }
  }
}"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": f"{login}-profile"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise SystemExit(f"GitHub API error: {data['errors']}")
    coll = data["data"]["user"]["contributionsCollection"]
    weeks = [[(d["date"], d["contributionCount"], d["weekday"]) for d in w["contributionDays"]]
             for w in coll["contributionCalendar"]["weeks"]]
    return weeks, coll["restrictedContributionsCount"]


def sample_weeks():
    today = dt.date.today()
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    rnd, weeks, d = random.Random(7), [], start
    while d <= today:
        week = []
        for _ in range(7):
            if d <= today:
                wd = (d.weekday() + 1) % 7
                busy = rnd.random() < (0.85 if 0 < wd < 6 else 0.35)
                week.append((d.isoformat(), rnd.choice([2, 4, 6, 9, 13, 18, 26]) if busy else 0, wd))
            d += dt.timedelta(days=1)
        weeks.append(week)
    return weeks, 0


def stats(weeks):
    days = [x for w in weeks for x in w]
    counts = [c for _, c, _ in days]
    current, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1  # today may not have a contribution yet
    while i >= 0 and counts[i] > 0:
        current += 1
        i -= 1
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    best_date, best = max(((d, c) for d, c, _ in days), key=lambda x: x[1], default=("", 0))
    return {
        "total": sum(counts),
        "active": sum(1 for c in counts if c > 0),
        "current": current,
        "longest": longest,
        "best": best,
        "best_date": best_date,
    }


def thresholds(weeks):
    """Quartiles of active days, like GitHub, so one huge day doesn't flatten the rest."""
    active = sorted(c for w in weeks for _, c, _ in w if c > 0)
    if not active:
        return [1, 1, 1]
    return [active[min(len(active) - 1, int(len(active) * q))] for q in (.25, .5, .75)]


def level(c, cuts):
    if c <= 0:
        return 0
    return 1 + sum(c > cut for cut in cuts)


def build(theme, weeks, private, synced):
    t = THEMES[theme]
    s = stats(weeks)
    cuts = thresholds(weeks)
    W, H, X0, Y0, P = 880, 318, 56, 182, 15
    # 371 cells: one shared <rect>, coloured per level through CSS, keeps the daily commit small.
    out = ['<defs><rect id="cell" width="12" height="12" rx="3"/></defs>',
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>',
           text("Contributions", 28, 36, 14, t["fg"], wght=600),
           text(f"Last 12 months · synced {synced:%-d %b %Y}", W - 28, 36, 11, t["subtle"], family="mono", anchor="end"),
           f'<path d="M0 54H{W}" stroke="{t["border"]}"/>']

    best = dt.date.fromisoformat(s["best_date"]) if s["best_date"] else None
    tiles = [
        ("Contributions", f'{s["total"]:,}', ""),
        ("Active days", f'{s["active"]:,}', ""),
        ("Current streak", str(s["current"]), "days"),
        ("Longest streak", str(s["longest"]), "days"),
        ("Busiest day", str(s["best"]), f"{best:%-d %b}" if best else ""),
    ]
    tile_w = (W - 56) / len(tiles)
    for i, (label, value, unit) in enumerate(tiles):
        x = 28 + i * tile_w
        out.append(text(label, x, 84, 12, t["subtle"]))
        out.append(text(value, x, 118, 30, t["fg"], wght=700, tracking=-0.02))
        if unit:
            out.append(text(unit, x + measure(value, 30, wght=700, tracking=-0.02) + 6, 118, 12.5, t["subtle"]))
    out.append(f'<path d="M28 140H{W - 28}" stroke="{t["hairline"]}"/>')

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(text(label, 28, Y0 + row * P + 9.5, 10, t["subtle"], family="mono"))
    last_month, last_label = None, -99
    for c, week in enumerate(weeks):
        first = dt.date.fromisoformat(week[0][0])
        if first.month != last_month and c - last_label >= 3 and c > 0:
            out.append(text(f"{first:%b}", X0 + c * P, Y0 - 10, 10, t["subtle"], family="mono"))
            last_label = c
        last_month = first.month
        cells = "".join(f'<use href="#cell" x="{X0 + c * P}" y="{Y0 + wd * P}" class="l{level(n, cuts)}"/>'
                        for _, n, wd in week)
        out.append(f'<g class="col" style="animation-delay:{c * .014:.3f}s">{cells}</g>')

    foot = H - 20
    if private:
        share = private / s["total"] if s["total"] else 0
        note = (f"{private:,} of these are in private work repos" if share < .995
                else "Nearly all of this is in private work repos")
        out.append(text(note, 28, foot, 10.5, t["subtle"], family="mono"))
    lx = W - 28 - (5 * P + 66)
    out.append(text("Less", lx, foot, 10, t["subtle"], family="mono"))
    out += [f'<rect x="{lx + 32 + i * P}" y="{foot - 10}" width="12" height="12" rx="3" fill="{t["levels"][i]}"/>'
            for i in range(5)]
    out.append(text("More", lx + 32 + 5 * P + 4, foot, 10, t["subtle"], family="mono"))

    style = ("".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(t["levels"]))
             + ".col{animation:fade .6s ease-out both}@keyframes fade{from{opacity:0}}")
    desc = (f'{s["total"]:,} GitHub contributions in the last 12 months over {s["active"]} active days. '
            f'Current streak {s["current"]} days, longest {s["longest"]} days.'
            + (f" {private:,} are in private repositories." if private else ""))
    write(f"contributions-{theme}.svg", document(W, H, "GitHub contributions", desc, "".join(out), style))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="draw made-up data instead of calling the API")
    args = ap.parse_args()
    weeks, private = sample_weeks() if args.sample else fetch(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    synced = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=45)))  # Nepal time
    for theme in THEMES:
        build(theme, weeks, private, synced)
    print(f"Drew contributions-dark.svg and contributions-light.svg ({stats(weeks)['total']:,} contributions).")
