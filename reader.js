(function(){
 const R=document.getElementById("reader"),B=document.getElementById("rBody");
 const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
 const CAT={science:["Science","🔭"],health:["Health","🌿"],community:["Kindness","🤝"],environment:["Environment","🌍"],india:["India · AP/TS","🇮🇳"],telugu:["తెలుగు","🪔"],tech:["Tech","💡"],sports:["Sports","🏏"]};
 const COL={science:"#5b6cff",health:"#13a37f",community:"#f26b3a",environment:"#3f9d3a",india:"#e2452b",telugu:"#c2185b",tech:"#7c4dff",sports:"#0277bd"};
 let DATA=[],cur=null,fromList=false,speaking=null;
 const ago=iso=>{const m=(Date.now()-new Date(iso))/6e4;if(m<60)return Math.max(1,m|0)+" min ago";if(m<1440)return (m/60|0)+" hours ago";return (m/1440|0)+" days ago"};
 // font size
 let fs=+localStorage.rfs||1;const setFs=v=>{fs=Math.min(1.6,Math.max(.85,v));localStorage.rfs=fs;R.style.setProperty("--rfs",fs)};setFs(fs);
 document.getElementById("rSm").onclick=()=>setFs(fs-.15);document.getElementById("rLg").onclick=()=>setFs(fs+.15);
 document.getElementById("rBack").onclick=()=>{fromList?history.back():(location.hash="")};
 document.getElementById("rShare").onclick=async()=>{const u=location.href;try{if(navigator.share)await navigator.share({title:cur&&cur.title,url:u});else{await navigator.clipboard.writeText(u);toast("Link copied ✓")}}catch(e){}};
 function toast(t){const d=document.createElement("div");d.className="r-toast";d.textContent=t;R.appendChild(d);setTimeout(()=>d.remove(),2600)}
 // speech
 function voiceFor(lang){const vs=speechSynthesis.getVoices();const want=lang==="te"?["te-IN","te"]:["en-IN","en-GB","en-US","en"];
  for(const w of want){const v=vs.find(v=>v.lang.replace("_","-").toLowerCase().startsWith(w.toLowerCase()));if(v)return v}return null}
 function stop(){if("speechSynthesis" in window)speechSynthesis.cancel();if(speaking){speaking.classList.remove("on");speaking.querySelector("span").textContent="🔊 Listen"}speaking=null}
 function speak(btn,text,lang){
  if(speaking===btn){stop();return}stop();
  if(!("speechSynthesis" in window)){toast(lang==="te"?"ఈ ఫోన్‌లో వినిపించే సౌకర్యం లేదు":"Reading aloud isn't supported on this browser");return}
  const v=voiceFor(lang);
  if(!v&&lang==="te"){toast("తెలుగు వాయిస్ లేదు. Telugu voice not available on this phone — try Chrome, or add Telugu in text-to-speech settings.");return}
  const u=new SpeechSynthesisUtterance(text);if(v)u.voice=v;u.lang=v?v.lang:(lang==="te"?"te-IN":"en-IN");u.rate=.92;
  u.onend=u.onerror=()=>{if(speaking===btn)stop()};
  speaking=btn;btn.classList.add("on");btn.querySelector("span").textContent="⏹ Stop";speechSynthesis.speak(u);
 }
 if("speechSynthesis" in window)speechSynthesis.onvoiceschanged=()=>{};
 function block(lang,text){if(!text)return"";const te=lang==="te";
  return `<section class="r-sum ${te?"te":""}" lang="${te?"te":"en"}"><div class="r-sh"><h2>${te?"తెలుగులో సారాంశం":"In short"}</h2>
  <button class="r-listen" data-lang="${lang}"><span>🔊 Listen</span></button></div><p>${esc(text)}</p></section>`}
 function open(id){const it=DATA.find(x=>x.id===id);if(!it)return;cur=it;stop();
  const i=DATA.indexOf(it),nx=DATA[(i+1)%DATA.length],c=CAT[it.category]||CAT.community,col=COL[it.category]||"#f26b3a";
  const first=it.lang==="te"?[["te",it.sum_te],["en",it.sum_en]]:[["en",it.sum_en],["te",it.sum_te]];
  const fallback=!it.sum_en&&!it.sum_te?`<section class="r-sum"><p>${esc(it.summary)}</p></section>`:"";
  B.innerHTML=`<div class="r-img" style="${it.image?`background-image:url('${esc(it.image)}'),`:"background-image:"}linear-gradient(135deg,${col},#ffc46b)">${it.image?"":`<span>${c[1]}</span>`}</div>
  <div class="r-card"><div class="r-meta"><span class="pill" style="--c:${col}">${c[1]} ${c[0]}</span><span>${esc(it.source)}</span><span class="dot">•</span><time>${ago(it.published)}</time></div>
  <h1 class="${/[\u0C00-\u0C7F]/.test(it.title)?"te":""}">${esc(it.title)}</h1>
  ${first.map(([l,t])=>block(l,t)).join("")}${fallback}
  <a class="r-cta" href="${esc(it.link)}" target="_blank" rel="noopener">Read full story at ${esc(it.source)} <b>↗</b></a>
  <p class="r-note">Short summary by Good News Daily${it.lang==="te"?"; English is machine-translated":"; Telugu is machine-translated"}. The full article belongs to ${esc(it.source)}.</p>
  <a class="r-next" href="#/s/${nx.id}"><small>Next story →</small><span class="${/[\u0C00-\u0C7F]/.test(nx.title)?"te":""}">${esc(nx.title)}</span></a></div>`;
  B.querySelectorAll(".r-listen").forEach(b=>b.onclick=()=>speak(b,b.closest(".r-sum").querySelector("p").textContent,b.dataset.lang));
  R.hidden=false;document.documentElement.classList.add("r-open");R.scrollTop=0;
  requestAnimationFrame(()=>R.classList.add("show"));document.title=it.title+" · Good News Daily";
 }
 function close(){stop();R.classList.remove("show");document.documentElement.classList.remove("r-open");document.title="Good News Daily — the day's uplifting stories";setTimeout(()=>{if(!R.classList.contains("show"))R.hidden=true},300)}
 function route(){const m=location.hash.match(/^#\/s\/([\w-]+)/);if(m&&DATA.length)open(m[1]);else if(!m)close()}
 addEventListener("hashchange",()=>{fromList=/#\/s\//.test(location.hash);route()});
 addEventListener("keydown",e=>{if(e.key==="Escape"&&!R.hidden)document.getElementById("rBack").click()});
 window.onData=d=>{DATA=d;route()};
})();
