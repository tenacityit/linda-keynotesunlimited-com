#!/usr/bin/env python3
"""Pull Linda Roszak Burton's picked podcast episodes into data/feeds.json.

Run on a schedule by .github/workflows/update-feeds.yml. Standard library only.
Each pick is [exact feed title, title to display on the page].
"""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

PODCAST_FEED = "https://media.rss.com/smiklespeaks/feed.xml"
PICKED_EPISODES = [
    [
        "Developing Grateful Hearts, Featuring Linda Roszak Burton",
        "Developing Grateful Hearts"
    ],
    [
        "Gratitude in Chaotic Times, Featuring Linda Roszak Burton",
        "Gratitude in Chaotic Times"
    ],
    [
        "Post-Traumatic Growth Featuring Linda Roszak Burton",
        "Post-Traumatic Growth"
    ]
]
# Interviews on other shows, from Linda's own list (no feed to read). Shown after the picks.
EXTRA_EPISODES = [
    {
        "display": "Healing Through the Power of Gratitude",
        "source": "An Unexpected Life, Claire Marie Foundation",
        "link": "https://podcasts.apple.com/us/podcast/healing-through-the-power-of-gratitude-guest/id1805668642?i=1000718747200",
    },
    {
        "display": "The Power of Gratitude in Healthcare",
        "source": "Sound Practice",
        "link": "https://www.soundpractice.com/e/the-power-of-gratitude-in-healthcare-with-linda-roszak-burton",
    },
]
OUT = Path(__file__).resolve().parent.parent / "data" / "feeds.json"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "keynotesunlimited-feed-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def podcast():
    ch = ET.fromstring(fetch(PODCAST_FEED)).find("channel")
    items = {it.findtext("title"): it for it in ch.findall("item")}
    missing = [t for t, _ in PICKED_EPISODES if t not in items]
    if missing:
        raise RuntimeError(f"picked episodes not in feed: {missing}")
    return {"episodes": [
        {"title": t, "display": shown, "link": items[t].findtext("link")}
        for t, shown in PICKED_EPISODES
    ] + EXTRA_EPISODES}


def main():
    try:
        data = {"podcast": podcast()}
    except Exception as exc:  # keep the previous file if the feed is down
        print("podcast feed failed:", exc, file=sys.stderr)
        sys.exit(1)
    OUT.parent.mkdir(exist_ok=True)
    if OUT.exists():
        old = json.loads(OUT.read_text())
        old.pop("updated", None)
        if old == data:
            print("no changes")
            return
    data["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}: {len(data['podcast']['episodes'])} episodes")


if __name__ == "__main__":
    main()
