#!/usr/bin/env python3
"""Send the daily Good News Daily web push via OneSignal.

Usage: python3 scripts/send_push.py [--dry-run] [--mode top|teaser]
Needs env ONESIGNAL_API_KEY (never printed).
"""
import argparse, json, os, pathlib, sys, urllib.request, urllib.error

APP_ID = "ceb85e1d-3dcc-4b8f-b7a4-c2d8a4021242"
SITE = "https://anilkumarnandamuri.github.io/good-news-daily/"
API = "https://api.onesignal.com/notifications"
NEWS = pathlib.Path(__file__).resolve().parent.parent / "data" / "news.json"
EMOJI = {"science": "🔭", "health": "🌿", "community": "🤝", "environment": "🌍",
         "india": "🇮🇳", "telugu": "🪔", "tech": "💡"}

def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"

def build(items, mode):
    items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)
    if not items:
        return None
    top = items[0]
    if mode == "teaser":
        picks, seen = [], set()
        for it in items:
            if it.get("category") not in seen:
                picks.append(it); seen.add(it.get("category"))
            if len(picks) == 3:
                break
        body = "\n".join(f"{EMOJI.get(i.get('category'), '✨')} {clip(i['title'], 60)}" for i in picks)
        title = "☀️ Today's good news"
    else:
        title = f"☀️ {clip(top['title'], 60)}"
        body = clip(top.get("summary") or "Tap to read today's uplifting stories.", 110)
    return {"app_id": APP_ID, "target_channel": "push",
            "included_segments": ["Total Subscriptions"],
            "headings": {"en": title}, "contents": {"en": body},
            "url": SITE, "chrome_web_icon": SITE + "icons/icon-192.png"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mode", choices=["top", "teaser"], default="teaser")
    a = ap.parse_args()
    payload = build(json.loads(NEWS.read_text()).get("items", []), a.mode)
    if not payload:
        print("No stories in news.json; nothing sent."); return 0
    print(json.dumps({k: payload[k] for k in ("headings", "contents", "url", "included_segments")}, ensure_ascii=False, indent=1))
    if a.dry_run:
        print("Dry run: not sent."); return 0
    key = os.environ.get("ONESIGNAL_API_KEY")
    if not key:
        print("ONESIGNAL_API_KEY is not set; aborting.", file=sys.stderr); return 2
    req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, body = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr); return 1
    body = body.replace(key, "***")
    print(f"OneSignal HTTP {status}: {body[:500]}")
    try:
        d = json.loads(body)
    except ValueError:
        d = {}
    if status == 200 and not d.get("id"):
        print("No subscribers matched yet — nothing delivered (harmless).")
    return 0 if status < 300 else 1

if __name__ == "__main__":
    sys.exit(main())
