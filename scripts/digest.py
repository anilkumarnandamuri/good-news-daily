#!/usr/bin/env python3
"""Write a short email digest (HTML + text) of the top 5 stories from 5 different categories.
Does not send anything. Usage: python3 scripts/digest.py [--out digest-sample.html]
Writes <out> (HTML) and <out minus .html>.txt (plain text)."""
import argparse, datetime as dt, html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://anilkumarnandamuri.github.io/good-news-daily/"
CATS = {"science": ("Science", "🔭", "#5b6cff"), "health": ("Health", "🌿", "#13a37f"),
        "community": ("Kindness", "🤝", "#f26b3a"), "environment": ("Environment", "🌍", "#3f9d3a"),
        "india": ("India · AP/TS", "🇮🇳", "#e2452b"), "telugu": ("తెలుగు", "🪔", "#c2185b"),
        "tech": ("Tech", "💡", "#7c4dff"), "sports": ("Sports", "🏏", "#0277bd")}

def clip(s, n=180):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"

def pick(items, n=5):
    out, seen = [], set()
    for it in sorted(items, key=lambda x: x.get("score", 0), reverse=True):
        if it["category"] not in seen:
            out.append(it); seen.add(it["category"])
        if len(out) == n:
            break
    return out

def render(stories, day):
    e = html.escape
    rows = "".join(f"""
<tr><td style="padding:0 0 22px">
 <div style="font:600 11px/1 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:{CATS[s['category']][2]}">{CATS[s['category']][1]} {e(CATS[s['category']][0])} · {e(s['source'])}</div>
 <a href="{e(s['link'])}" style="display:block;margin:6px 0 4px;font:700 20px/1.3 Georgia,serif;color:#1d1a17;text-decoration:none">{e(s['title'])}</a>
 <div style="font:16px/1.5 Arial,'Noto Sans Telugu',sans-serif;color:#5a524b">{e(clip(s['summary']))}</div>
 <a href="{e(s['link'])}" style="font:600 15px Arial,sans-serif;color:#f26b3a">Read the story →</a>
</td></tr>""" for s in stories)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Good News Daily — {day}</title></head>
<body style="margin:0;background:#fff8f0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" style="max-width:560px;background:#fff;border-radius:20px;padding:28px 24px" cellpadding="0" cellspacing="0">
<tr><td style="padding:0 0 18px">
 <div style="font:700 28px/1.1 Georgia,serif;color:#1d1a17">☀️ Good News <i style="color:#f26b3a">Daily</i></div>
 <div style="font:13px Arial,sans-serif;color:#8a8077;margin-top:6px;text-transform:uppercase;letter-spacing:.06em">{day} · 5 stories to brighten your day</div>
</td></tr>{rows}
<tr><td align="center" style="padding:6px 0 4px">
 <a href="{SITE}" style="display:inline-block;background:linear-gradient(135deg,#f26b3a,#f7b733);background-color:#f26b3a;color:#fff;font:700 17px Arial,sans-serif;padding:14px 28px;border-radius:999px;text-decoration:none">See all of today's good news</a>
</td></tr>
<tr><td style="padding-top:18px;font:12px/1.5 Arial,sans-serif;color:#9a9087;text-align:center">Headlines and excerpts link to the original publishers. Positivity is scored automatically and can be wrong.</td></tr>
</table></td></tr></table></body></html>"""

def text(stories, day):
    lines = [f"☀️ Good News Daily — {day}", "5 stories to brighten your day", ""]
    for i, s in enumerate(stories, 1):
        c = CATS[s["category"]]
        lines += [f"{i}. {c[1]} {c[0]}: {s['title']}", f"   {clip(s['summary'])}", f"   {s['link']}", ""]
    return "\n".join(lines + [f"See all of today's good news: {SITE}"])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(ROOT / "digest-sample.html")); a = ap.parse_args()
    d = json.loads((ROOT / "data" / "news.json").read_text())
    stories = pick(d["items"])
    day = dt.datetime.fromisoformat(d["generated"]).astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%A, %d %B %Y")
    out = pathlib.Path(a.out); out.write_text(render(stories, day)); out.with_suffix(".txt").write_text(text(stories, day))
    print(f"Wrote {out} and {out.with_suffix('.txt')} with {len(stories)} stories:", ", ".join(s["category"] for s in stories))

if __name__ == "__main__":
    main()
