#!/usr/bin/env python3
"""Good News Daily build: fetch RSS -> dedupe -> positivity score -> data/news.json.
Free/offline scoring: VADER (English) + keyword rules; Telugu: keyword lexicon heuristics."""
import feedparser, json, re, html, hashlib, datetime as dt, pathlib, socket
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
socket.setdefaulttimeout(20)
UA = "Mozilla/5.0 (GoodNewsDaily build; +github pages)"
# (url, source, default category, lang, is_curated_positive_outlet)
FEEDS = [
 ("https://www.goodnewsnetwork.org/feed/","Good News Network","community","en",True),
 ("https://www.positive.news/feed/","Positive News","community","en",True),
 ("https://reasonstobecheerful.world/feed/","Reasons to be Cheerful","environment","en",True),
 ("https://feeds.bbci.co.uk/news/science_and_environment/rss.xml","BBC News","science","en",False),
 ("https://feeds.bbci.co.uk/news/health/rss.xml","BBC News","health","en",False),
 ("https://feeds.bbci.co.uk/news/technology/rss.xml","BBC News","tech","en",False),
 ("https://www.sciencedaily.com/rss/top/science.xml","ScienceDaily","science","en",False),
 ("https://www.sciencedaily.com/rss/top/health.xml","ScienceDaily","health","en",False),
 ("https://www.thehindu.com/sci-tech/science/feeder/default.rss","The Hindu","science","en",False),
 ("https://www.thehindu.com/news/national/andhra-pradesh/feeder/default.rss","The Hindu","india","en",False),
 ("https://www.thehindu.com/news/national/telangana/feeder/default.rss","The Hindu","india","en",False),
 ("https://www.sakshi.com/rss.xml","Sakshi","telugu","te",False),
 ("https://tv9telugu.com/feed","TV9 Telugu","telugu","te",False),
 ("https://telugu.oneindia.com/rss/feeds/telugu-news-fb.xml","Oneindia Telugu","telugu","te",False),
 ("https://www.ntnews.com/feed","Namasthe Telangana","telugu","te",False),
]
NEG_EN = r"\b(kill|killed|killing|dead|death|deaths|dies|died|dying|murder|rape|assault|attack|war|wars|bomb|shoot|shooting|gun|terror|crash|collapse|disaster|flood|earthquake|wildfire|fire|blaze|cyclone|hurricane|tornado|arrest|arrested|jail|prison|court|charged|accused|fraud|scam|crime|police|suicide|abuse|violence|riot|protest|strike|missile|militar|army|troops|hostage|victim|injur|tragedy|outbreak|epidemic|cancer risk|warns|warning|threat|fear|crisis|lawsuit|sued|ban|banned|layoff|cuts|recession|scandal|corruption|probe|ransomware|hack|breach|stabb|drown|famine|refugee|genocide|poison|toxic|row|slams|clash|accident|missing|trump|election|poll|resign|passes away|passed away|security|suspend|hc|musk|el niño|petition|conspira|urged)\w*"
POS_EN = r"\b(breakthrough|cure|record|first|rescue|saved|restor|recover|win|wins|award|celebrat|hope|kind|volunteer|donat|thriv|success|discover|innovat|clean|renewable|solar|protect|reviv|return|reunite|inspir|help|free|milestone|boost|improv|launch|honou?r|smile|joy)\w*"
CAT_RULES = [("health",r"\b(health|medic|doctor|hospital|vaccine|disease|therapy|patient|mental|drug|brain|heart|diet|sleep)"),
 ("environment",r"\b(climate|forest|ocean|wildlife|species|tree|solar|wind power|renewable|conservation|river|bird|whale|coral|plastic|rewild|animal|turtle|bee)"),
 ("tech",r"\b(ai\b|robot|software|app\b|tech|computer|chip|quantum|internet|smartphone|startup|digital)"),
 ("science",r"\b(scien|research|study|astronom|space|nasa|physic|fossil|telescope|planet|galaxy|archaeolog|chemist)")]
# Telugu lexicon (translation-free). Matched as substrings because Telugu agglutinates.
NEG_TE = ["హత్య","మృతి","మరణ","చనిపో","ప్రమాద","దాడి","యుద్ధ","అరెస్ట్","అత్యాచార","ఆత్మహత్య","వరద","భూకంప","అగ్నిప్రమాద","మంటలు","పోలీస","కేసు","కోర్టు","జైలు","మోసం","దొంగ","గాయ","విషాద","ఉగ్ర","బాంబు","కాల్పు","ఆరోప","విమర్శ","ఆందోళన","నిరసన","ధర్నా","ఫైర్","రాజకీయ","చోరీ","ఎన్నిక","వివాద","హెచ్చరిక","తుపాను","కలకలం","దారుణ","షాక్","ఢీ","సస్పెండ్","బెదిరి","లంచ","ఏసీబీ","ఈడీ","సీబీఐ","killed","death","accident","police","arrest","వైసీపీ","టీడీపీ","బీఆర్ఎస్","కాంగ్రెస్","బీజేపీ","జనసేన","కేటీఆర్","జగన్","రేవంత్","చంద్రబాబు","పవన్","ఎమ్మెల్యే","మంత్రి","బిగ్ బాస్","రాశి","జాతకం","రిలీజ్","సినిమా","Movie","Event","బంగారం","ధర","విజయ్","దేవరకొండ","రష్మిక","హీరో","హీరోయిన్","ప్రచారం","ముప్పు","సీఎం","ఎఫెక్ట్"]
POS_TE = ["విజయం","విజేత","గెలుపు","గెలిచ","శుభవార్త","గుడ్ న్యూస్","గుడ్‌న్యూస్","రికార్డు","రికార్డ్","అవార్డు","పురస్కార","సాధించ","ఘనత","ఆనంద","సంతోష","సాయం","సహాయ","ఆదర్శ","స్ఫూర్తి","ప్రశంస","అభివృద్ధి","ప్రారంభ","ఉచిత","ఉద్యోగ","స్కాలర్‌షిప్","పతకం","గోల్డ్","స్వర్ణ","మెడల్","టాపర్","ర్యాంక్","ఆవిష్కర","పరిశోధన","పండుగ","ఉత్సవ","వేడుక","ఆరోగ్య","పచ్చదన","మొక్క","దానం","సేవ","అరుదైన","ప్రపంచ స్థాయి","గర్వ","మెరిసిన","అద్భుత"]
TE_CAT = [("health",["ఆరోగ్య","వైద్య","ఆస్పత్రి","ఆసుపత్రి","చికిత్స","డాక్టర్","యోగా"]),("tech",["టెక్","ఏఐ","యాప్","స్మార్ట్","సాఫ్ట్‌వేర్","ఐటీ","స్టార్టప్"]),
 ("environment",["మొక్క","అడవి","పచ్చదన","పర్యావరణ","నీరు","వన్యప్రాణ","పులి"]),("science",["ఇస్రో","శాస్త్ర","పరిశోధన","అంతరిక్ష","ఉపగ్రహ"])]
vader = SentimentIntensityAnalyzer()
def clean(s):
    s = re.sub(r"<[^>]+>"," ",html.unescape(s or "")); s = html.unescape(s)
    s = re.sub(r"\s+"," ",s).strip(); return s
def short(s,n=220):
    s = re.sub(r"(The post .*? appeared first on .*|Continue reading.*|\[…\]|\[\.\.\.\])$","",s).strip()
    return s if len(s)<=n else s[:n].rsplit(" ",1)[0]+"…"
def image(e):
    for k in ("media_content","media_thumbnail"):
        for m in e.get(k,[]) or []:
            if m.get("url"): return m["url"]
    for l in e.get("links",[]):
        if l.get("type","").startswith("image"): return l["href"]
    m = re.search(r'<img[^>]+src="([^"]+)"', (e.get("summary","")+str(e.get("content",""))))
    return m.group(1) if m else None
def hires(u):
    return re.sub(r"/ace/standard/\d+/","/ace/standard/976/",u) if u else u
def score_en(t,s,curated):
    txt=f"{t}. {s}"; low=txt.lower()
    neg=len(re.findall(NEG_EN,low)); negt=len(re.findall(NEG_EN,t.lower())); pos=len(re.findall(POS_EN,low))
    v=vader.polarity_scores(txt)["compound"]; vt=vader.polarity_scores(t)["compound"]
    sc=0.5*v+0.5*vt+0.12*pos-0.35*neg-0.6*negt+(0.35 if curated else 0)
    return sc, (negt==0 and neg<=(1 if curated else 0) and vt>-0.1 and sc>(0.15 if curated else 0.35))
def score_te(t,s):
    neg=sum(w in t for w in NEG_TE)+0.5*sum(w in s for w in NEG_TE)
    pos=sum(w in t for w in POS_TE)+0.3*sum(w in s for w in POS_TE)
    sc=0.4*pos-0.8*neg; return sc, (neg==0 and pos>=1)
def cat_en(text,default):
    if default in ("india","telugu"): return default
    for c,rx in CAT_RULES:
        if re.search(rx,text.lower()): return c
    return default
def main():
    now=dt.datetime.now(dt.timezone.utc); items=[]; seen=set(); report=[]
    for url,src,dcat,lang,cur in FEEDS:
        try:
            f=feedparser.parse(url,agent=UA); n=0
            for e in f.entries[:80]:
                t=clean(e.get("title")); link=e.get("link")
                if not t or not link or t.startswith('Good News in History'): continue
                key=re.sub(r"\W","",t.lower())[:60]
                if key in seen or link in seen: continue
                seen|={key,link}
                tm=e.get("published_parsed") or e.get("updated_parsed")
                when=dt.datetime(*tm[:6],tzinfo=dt.timezone.utc) if tm else now
                if (now-when).days>4: continue
                s=short(clean(e.get("summary","")))
                if lang=="te" and s.startswith(t[:20]): s=short(re.sub(r"^[\u0C3E-\u0C4D\u0C55\u0C56\u0C02\u0C03]+","",s[len(t):].strip()).strip())
                sc,ok=(score_te(t,s) if lang=="te" else score_en(t,s,cur))
                if not ok: continue
                cat=cat_en(t+" "+s,dcat)
                if lang=="te":
                    cat="telugu"; sub=next((c for c,ws in TE_CAT if any(w in t for w in ws)),None)
                else: sub=None
                items.append(dict(id=hashlib.md5(link.encode()).hexdigest()[:10],title=t,source=src,summary=s,link=link,
                    published=when.isoformat(),category=cat,subcategory=sub,lang=lang,image=hires(image(e)),score=round(sc,3))); n+=1
            report.append(dict(feed=url,source=src,entries=len(f.entries),kept=n,status=f.get("status")))
        except Exception as ex: report.append(dict(feed=url,source=src,error=str(ex)))
    items.sort(key=lambda x:(-x["score"])); out=[]; per={}
    for it in items:  # cap per category and per source for diversity
        k=it["category"]; per[k]=per.get(k,0)+1
        if per[k]<=(30 if k=="telugu" else 20): out.append(it)
    out.sort(key=lambda x:x["published"],reverse=True)
    p=pathlib.Path(__file__).resolve().parent.parent/"data"; p.mkdir(exist_ok=True)
    (p/"news.json").write_text(json.dumps(dict(generated=now.isoformat(),count=len(out),feeds=report,items=out),ensure_ascii=False,indent=1))
    for r in report: print(r)
    print("kept",len(out),{c:sum(i["category"]==c for i in out) for c in per})
if __name__=="__main__": main()
