#!/usr/bin/env python3
"""Short, elder-friendly English + Telugu summaries for Good News Daily stories.

Method (no LLM available on the box):
 * English: extractive. Sentences come only from the feed description and the
   article's <meta description>/og:description (never the article body), cleaned and
   trimmed to 3-4 short sentences, ending with a pointer to the source.
 * Telugu: Telugu-language stories use their own Telugu description extractively;
   other stories are machine-translated (free Google translate web endpoint, with the
   MyMemory API as fallback). English for Telugu stories is translated the same way.
 * Cached by story id in data/summaries.json, so reruns only touch new stories.
 * Every network call has a short timeout; failures are skipped and retried next run.
Run standalone: python3 scripts/summarize.py  (updates data/news.json in place)
"""
import concurrent.futures as cf, html, json, pathlib, re, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "summaries.json"
UA = {"User-Agent": "Mozilla/5.0 (GoodNewsDaily summary bot)"}
BUDGET_S = 150  # whole summary step stays under ~2.5 min even on a cold cache

def _get(url, timeout=8, limit=400_000):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read(limit).decode("utf-8", "ignore")

def meta(url):
    """og:description/meta description and og:image only — no article body."""
    try:
        h = _get(url)
    except Exception:
        return "", None
    def m(*names):
        for n in names:
            for pat in (rf'<meta[^>]+(?:property|name)=["\']{n}["\'][^>]*content=["\']([^"\']+)',
                        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{n}["\']'):
                x = re.search(pat, h, re.I)
                if x: return html.unescape(x.group(1)).strip()
        return None
    return m("og:description", "description", "twitter:description") or "", m("og:image", "twitter:image")

def translate(text, sl, tl):
    if not text: return ""
    q = urllib.parse.quote(text[:1500])
    for url, pick in (
        (f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={sl}&tl={tl}&q={q}",
         lambda d: d[0] if isinstance(d[0], str) else d[0][0]),
        (f"https://api.mymemory.translated.net/get?langpair={sl}|{tl}&q={q}",
         lambda d: d["responseData"]["translatedText"]),
    ):
        try:
            out = pick(json.loads(_get(url, timeout=10)))
            if out and "MYMEMORY WARNING" not in out and out.strip() != text.strip():
                return html.unescape(out).strip()
        except Exception:
            continue
    return ""

SPLIT = re.compile(r"(?<=[.!?।])\s+|(?<=\.\.)\s*|\s*\|\s*")
def sentences(text):
    text = re.sub(r"\([^)]{0,80}\)", "", text or "")
    text = re.sub(r"https?://\S+|Read more.*$|Click here.*$|Also Read.*$", "", text, flags=re.I)
    out = []
    for s in SPLIT.split(text):
        s = s.strip(" .…-–—:").strip()
        if 25 <= len(s) <= 260 and not s.endswith("…"): out.append(s + ("" if s[-1] in ".!?" else "."))
    return out

def extractive(title, *texts, n=3, source=""):
    seen, picked = set(), []
    tkey = re.sub(r"\W", "", title.lower())[:40]
    for t in texts:
        for s in sentences(t):
            k = re.sub(r"\W", "", s.lower())[:40]
            if k in seen or k == tkey: continue
            seen.add(k); picked.append(s)
            if len(picked) == n: break
        if len(picked) == n: break
    if not picked:
        picked = [title.rstrip(".!?") + "."]
    return picked

def summarize_item(it):
    desc = it.get("desc") or it.get("summary") or ""
    md, img = meta(it["link"])
    if it["lang"] == "te":
        te = extractive(it["title"], desc, md, n=3)
        if len(te) < 2: te = [it["title"].rstrip(".!?") + "."] + te
        te.append(f"పూర్తి వార్త {it['source']}లో చదవండి.")
        en_src = " ".join([it["title"].rstrip(".!?") + "."] + te[:-1])
        en = translate(en_src, "te", "en")
        en = (en + f" Read the full story at {it['source']}.") if en else ""
        te = " ".join(te)
    else:
        en = extractive(it["title"], desc, md, n=3)
        if len(en) < 2 and not en[0].startswith(it["title"][:30]): en = [it["title"].rstrip(".!?") + "."] + en
        en = " ".join(en)
        te = translate(en, "en", "te")
        te = (te + f" పూర్తి వార్త {it['source']}లో చదవండి.") if te else ""
        en += f" Read the full story at {it['source']}."
    return {"en": en, "te": te, "og_image": img, "t": int(time.time())}

def run(items):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [i for i in items if not (cache.get(i["id"], {}).get("en") and cache[i["id"]].get("te"))]
    t0 = time.time(); done = fail = 0
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(summarize_item, i): i for i in todo}
        try:
            for f in cf.as_completed(futs, timeout=BUDGET_S):
                i = futs[f]
                try:
                    r = f.result(); old = cache.get(i["id"], {})
                    cache[i["id"]] = {k: r[k] or old.get(k) for k in r}; done += 1
                except Exception:
                    fail += 1
        except cf.TimeoutError:
            print("summaries: time budget hit; remaining stories retry next run")
            for f in futs: f.cancel()
    live = {i["id"] for i in items}
    cache = {k: v for k, v in cache.items() if k in live or time.time() - v.get("t", 0) < 7 * 86400}
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    both = 0
    for i in items:
        c = cache.get(i["id"], {})
        i["sum_en"] = c.get("en") or ""; i["sum_te"] = c.get("te") or ""
        if not i.get("image") and c.get("og_image", "") and c["og_image"].startswith("http"): i["image"] = c["og_image"]
        i.pop("desc", None)
        both += bool(i["sum_en"] and i["sum_te"])
    print(f"summaries: {done} new, {fail} failed, {len(items)-len(todo)} cached, both={both}/{len(items)} in {time.time()-t0:.0f}s")
    return items

if __name__ == "__main__":
    p = ROOT / "data" / "news.json"; d = json.loads(p.read_text())
    d["items"] = run(d["items"]); p.write_text(json.dumps(d, ensure_ascii=False, indent=1))
