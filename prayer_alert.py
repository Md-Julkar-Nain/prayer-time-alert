"""Posts an @everyone prayer alert to a Discord webhook at Dhaka prayer times.

Runs every 5 minutes from GitHub Actions. It fetches today's Dhaka timings and
posts only if a prayer time fell inside the last 5 minutes, so each prayer is
announced once.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

WINDOW_MINUTES = 5
DHAKA = timezone(timedelta(hours=6))

PRAYERS = [
    ("Fajr", "Fajr"),
    ("Dhuhr", "Zuhr"),
    ("Asr", "Asr"),
    ("Maghrib", "Maghrib"),
    ("Isha", "Isha"),
]

API = (
    "https://api.aladhan.com/v1/timingsByCity"
    "?city=Dhaka&country=Bangladesh&method=1&school=1"
)


def fetch_timings():
    with urllib.request.urlopen(API, timeout=20) as r:
        return json.load(r)["data"]["timings"]


def post(webhook, text):
    body = json.dumps(
        {"content": text, "allowed_mentions": {"parse": ["everyone"]}}
    ).encode()
    req = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "prayer-alert/1.0"},
    )
    urllib.request.urlopen(req, timeout=20).read()


def main():
    now = datetime.now(DHAKA)
    timings = fetch_timings()
    dry = os.environ.get("DRY_RUN") == "1"
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook and not dry:
        sys.exit("DISCORD_WEBHOOK_URL is not set")

    for key, label in PRAYERS:
        hh, mm = timings[key].split(" ")[0].split(":")
        t = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        if t <= now < t + timedelta(minutes=WINDOW_MINUTES):
            msg = f"@everyone Hey everyone, it's {label} time. ({t.strftime('%I:%M %p')} Dhaka time)"
            print("POST:", msg)
            if not dry:
                post(webhook, msg)
        elif dry:
            print(f"{label}: {t.strftime('%I:%M %p')}")


if __name__ == "__main__":
    main()
