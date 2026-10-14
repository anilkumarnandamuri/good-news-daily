#!/usr/bin/env python3
"""English + Telugu summaries for Good News Daily stories (strictly one-to-one).

Method (no LLM available on the box):
 * ONE canonical summary in the story's own language: up to 6 sentences / ~120 words,
   extractive from the full feed description plus the article's og:/meta/twitter
   descriptions (never the article body). De-duplicated, no headline repeats, no
   "Topic:" prefixes, no "read more" line (that lives on the button).
 * The other language is a sentence-by-sentence machine translation of exactly that
   text (free Google translate web endpoint, MyMemory fallback). If any sentence
   fails to translate, the other language is left empty and retried next run.
 * Cached by story id in data/summaries.json, so reruns only touch new stories.
 * Every network call has a short timeout; failures are skipped and retried next run.
Run standalone: python3 scripts/summarize.py  (updates data/news.json in place)
"""
import concurrent.futures as cf, html, json, pathlib, re, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "summaries.json"
UA = {"User-Agent": "Mozilla/5.0 (GoodNewsDaily summary bot)"}
BUDGET_S = 240  # whole summary step stays under ~2.5 min even on a cold cache

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
    ds = []
    for n in ("og:description", "description", "twitter:description"):
        v = m(n)
        if v and v not in ds: ds.append(v)
    return " ".join(ds), m("og:image", "twitter:image")

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
PREFIX = re.compile(r"^[^:：.!?]{2,45}[:：]\s+")  # "Indiramma Housing: ..." style lead-ins

def _tok(s):
    return set(re.findall(r"[\w\u0C00-\u0C7F]{3,}", s.lower()))

def sentences(text, lang="en"):
    text = re.split(r"\[\s*(?:…|\.\.\.)\s*\]|\[\s*&hellip;\s*\]", text or "")
    if len(text) > 1:  # drop the half sentence that runs into a "[…]" cut
        head = text[0]; cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
        text = head[: cut + 1] if cut > 0 else ""
    else:
        text = text[0]
    text = text.strip()
    if re.search(r"(\.\.|…)$", text):  # feed truncated mid-sentence: drop that tail
        m = list(re.finditer(r"(?<!\.)[.!?।](?!\.)\s", text))
        text = text[: m[-1].end()] if m else ""
    text = re.sub(r"\([^)]{0,80}\)", "", text or "")
    text = re.sub(r"https?://\S+|Read more.*$|Click here.*$|Also Read.*$|The post .*? appeared first on .*$", "", text, flags=re.I)
    out = []
    for s in SPLIT.split(text):
        s = PREFIX.sub("", s.strip()).strip(" .…-–—:").strip()
        te_share = len(re.findall(r"[\u0C00-\u0C7F]", s)) / max(1, len(re.findall(r"\w", s)))
        if (lang == "te") != (te_share > 0.3): continue  # keep the summary in one language
        if 25 <= len(s) <= 260 and not s.endswith("…") and "…" not in s[-4:]:
            out.append(s + ("" if s[-1] in ".!?" else "."))
    return out

def canonical(title, *texts, n=6, max_words=120, lang="en"):
    """Up to 5-6 clean, de-duplicated sentences in the source language; never just the headline."""
    tt = _tok(PREFIX.sub("", title)); picked, toks = [], []
    for t in texts:
        for s in sentences(t, lang):
            k = _tok(s)
            if not k: continue
            if tt and len(k & tt) / len(k) > 0.7: continue          # headline repeat
            if any(len(k & o) / max(1, min(len(k), len(o))) > 0.6 for o in toks): continue  # duplicate
            if picked and len(" ".join(picked + [s]).split()) > max_words: return picked
            picked.append(s); toks.append(k)
            if len(picked) == n: return picked
    if len(picked) < 2:  # thin source: lead with the headline (minus any "Topic:" prefix)
        h = re.sub(r"\s*\.{2,}\s*", ", ", PREFIX.sub("", title)).strip(" ,.!?") + "."
        if not picked or not (_tok(h) and len(_tok(h) & toks[0]) / len(_tok(h)) > 0.6):
            picked = [h] + picked
    return picked

def summarize_item(it):
    desc = it.get("desc") or it.get("summary") or ""
    md, img = meta(it["link"])
    src_lang = "te" if it["lang"] == "te" else "en"
    other = "en" if src_lang == "te" else "te"
    sents = canonical(it["title"], desc, md, lang=src_lang)
    trans = [translate(x, src_lang, other) for x in sents]  # one call per sentence: strict 1:1
    if not all(trans):
        trans = []
    res = {src_lang: " ".join(sents), other: " ".join(trans), "n": len(sents)}
    return {"en": res["en"], "te": res["te"], "n": res["n"], "og_image": img, "t": int(time.time()), "v": 5}

def run(items):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [i for i in items if not (cache.get(i["id"], {}).get("v") == 5 and cache[i["id"]].get("en") and cache[i["id"]].get("te"))]
    t0 = time.time(); done = fail = 0
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(summarize_item, i): i for i in todo}
        try:
            for f in cf.as_completed(futs, timeout=BUDGET_S):
                i = futs[f]
                try:
                    r = f.result(); old = cache.get(i["id"], {})
                    cache[i["id"]] = r; done += 1
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
        ok = c.get("v") == 5; i["sum_en"] = c.get("en", "") if ok else ""; i["sum_te"] = c.get("te", "") if ok else ""
        if not i.get("image") and c.get("og_image", "") and c["og_image"].startswith("http"): i["image"] = c["og_image"]
        i.pop("desc", None)
        both += bool(i["sum_en"] and i["sum_te"])
    print(f"summaries: {done} new, {fail} failed, {len(items)-len(todo)} cached, both={both}/{len(items)} in {time.time()-t0:.0f}s")
    return items

if __name__ == "__main__":
    p = ROOT / "data" / "news.json"; d = json.loads(p.read_text())
    d["items"] = run(d["items"]); p.write_text(json.dumps(d, ensure_ascii=False, indent=1))
