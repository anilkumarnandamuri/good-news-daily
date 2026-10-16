(function(){
 const R=document.getElementById("reader"),B=document.getElementById("rBody");
 const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
 const CAT={science:["Science","🔭"],health:["Health","🌿"],community:["Kindness","🤝"],environment:["Environment","🌍"],india:["India · AP/TS","🇮🇳"],telugu:["తెలుగు","🪔"],tech:["Tech","💡"],sports:["Sports","🏏"]};
 const COL={science:"#5b6cff",health:"#13a37f",community:"#f26b3a",environment:"#3f9d3a",india:"#e2452b",telugu:"#c2185b",tech:"#7c4dff",sports:"#0277bd"};
 let DATA=[],NAV={},cur=null,fromList=false,speaking=null,returnFocus=null,returnHref=null;
 const background=new Map();
 const ago=iso=>{const m=(Date.now()-new Date(iso))/6e4;if(m<60)return Math.max(1,m|0)+" min ago";if(m<1440)return (m/60|0)+" hours ago";return (m/1440|0)+" days ago"};
 // The root scale also adjusts list text when the reader closes.
 const smaller=document.getElementById("rSm"),larger=document.getElementById("rLg");
 function paintSize(){const s=GN.textScale.get();for(const [b,disabled] of [[smaller,s<=GN.textScale.min],[larger,s>=GN.textScale.max]]){b.disabled=disabled;b.setAttribute("aria-disabled",String(disabled))}}
 function resize(delta){const s=GN.textScale.set(GN.textScale.get()+delta);paintSize();toast("Text size "+Math.round(s*100)+"%")}
 smaller.onclick=()=>resize(-GN.textScale.step);larger.onclick=()=>resize(GN.textScale.step);paintSize();
 document.getElementById("rBack").onclick=()=>{fromList?history.back():(location.hash="")};
 document.getElementById("rShare").onclick=async()=>{const u=location.href;try{if(navigator.share)await navigator.share({title:cur&&cur.title,url:u});else{await navigator.clipboard.writeText(u);toast("Link copied ✓")}}catch(e){}};
 function toast(t){const d=document.createElement("div");d.className="r-toast";d.textContent=t;d.setAttribute("role","status");R.appendChild(d);setTimeout(()=>d.remove(),2600)}
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
 function open(id){const it=DATA.find(x=>x.id===id)||GN.saved().find(x=>x.id===id);if(!it)return;
  if(R.hidden){returnFocus=document.activeElement;returnHref=returnFocus?.closest("a")?.getAttribute("href");
   [...document.body.children].filter(node=>node!==R).forEach(node=>{background.set(node,node.inert);node.inert=true})}
  cur=it;stop();
  const ord=(window.GN_order&&window.GN_order.some(x=>x.id===id))?window.GN_order:DATA,i=ord.findIndex(x=>x.id===id),nx=ord[(i+1)%ord.length],pv=ord[(i-1+ord.length)%ord.length];NAV={nx,pv};const c=CAT[it.category]||CAT.community,col=COL[it.category]||"#f26b3a";
  const first=it.lang==="te"?[["te",it.sum_te],["en",it.sum_en]]:[["en",it.sum_en],["te",it.sum_te]];
  const excerpt=(it.summary_status!=="paired"&&it.summary_status!=="summary")||!it.sum_en||!it.sum_te;
  const fallback=excerpt?`<section class="r-sum ${it.lang==="te"?"te":""}" lang="${it.lang==="te"?"te":"en"}"><h2 lang="en">Publisher excerpt</h2><p>${esc(it.summary)}</p><p class="r-note" lang="en">A complete bilingual summary is not available yet.</p></section>`:"";
  B.innerHTML=`${thumb(it,"r-img",true)}
  <div class="r-card"><div class="r-meta"><span class="pill" style="--c:${col}">${c[1]} ${c[0]}</span><span>${esc(it.source)}</span><span class="dot">•</span><time>${ago(it.published)}</time></div>
  <h1 id="rTitle" tabindex="-1" lang="${it.lang==="te"?"te":"en"}" class="${/[\u0C00-\u0C7F]/.test(it.title)?"te":""}">${esc(it.title)}</h1>
  ${excerpt?fallback:first.map(([l,t])=>block(l,t)).join("")}

  <div class="r-acts"><a class="r-wa" id="rWa" href="#" target="_blank" rel="noopener"><svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M16 3C8.8 3 3 8.7 3 15.8c0 2.5.7 4.9 2 7L3 29l6.4-2c2 1.1 4.300 1.700 6.600 1.700 7.200 0 13-5.700 13-12.800S23.200 3 16 3zm0 23.300c-2.100 0-4.100-.6-5.900-1.700l-.4-.2-3.800 1.200 1.200-3.700-.3-.4c-1.200-1.800-1.800-3.900-1.800-6 0-6 4.900-10.800 11-10.800s11 4.800 11 10.800S22.100 26.300 16 26.300zm6-8.100c-.3-.2-1.900-1-2.200-1.100-.3-.1-.5-.2-.7.200-.2.300-.8 1-1 1.200-.2.200-.4.200-.7.100-.3-.2-1.400-.5-2.600-1.600-1-.9-1.600-1.900-1.800-2.200-.2-.3 0-.5.100-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6l-1-2.400c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.400-.3.300-1.100 1.100-1.100 2.700s1.200 3.100 1.300 3.300c.2.200 2.300 3.500 5.500 4.900 2.700 1.100 3.300.9 3.900.8.600-.1 1.900-.8 2.200-1.500.3-.7.3-1.400.2-1.500-.1-.2-.3-.3-.6-.4z"/></svg>Share on WhatsApp</a>
  <button class="r-save2" id="rSave2"></button></div>
  <a class="r-cta" href="${esc(it.link)}" target="_blank" rel="noopener">Read full story at ${esc(it.source)} <b>↗</b></a>
  <p class="r-note">${excerpt?"Excerpt supplied by the publisher":"Bilingual summary by Good News Daily. Translations may contain errors"}. The full article belongs to ${esc(it.source)}.</p>
  <a class="r-next" href="#/s/${nx.id}"><small>Next story →</small><span class="${/[\u0C00-\u0C7F]/.test(nx.title)?"te":""}">${esc(nx.title)}</span></a>
  <p class="r-swipe">👆 Swipe left or right for more stories</p></div>
  <nav class="r-nav"><a href="#/s/${pv.id}" class="r-pv">← Previous</a><a href="#/s/${nx.id}" class="r-nx">Next story →</a></nav>`;
  const teHead=excerpt||/[\u0C00-\u0C7F]/.test(it.title)?it.title:((it.sum_te||"").split(/(?<=[.!?])\s/)[0]||it.title);
  const snip=(excerpt?it.summary:(it.lang==="te"?it.sum_te:it.sum_en))||it.summary||"";const cut=snip.length>160?snip.slice(0,160).replace(/\s\S*$/,"")+"…":snip;
  document.getElementById("rWa").href="https://wa.me/?text="+encodeURIComponent(`🌼 ${teHead}\n\n${cut}\n\n👉 ${location.origin+location.pathname}#/s/${it.id}\n— Good News Daily`);
  const paintSave=()=>{const on=GN.isSaved(it.id);const b=document.getElementById("rSave");b.setAttribute("aria-pressed",on);b.classList.toggle("on",on);document.getElementById("rSave2").innerHTML=on?"✓ Saved":"🔖 Save for later";document.getElementById("rSave2").classList.toggle("on",on)};
  document.getElementById("rSave").onclick=document.getElementById("rSave2").onclick=()=>{const on=GN.toggleSave(it);paintSave();toast(on?"Saved 🔖 — find it in the Saved tab":"Removed from Saved")};paintSave();
  GN.markRead(it);
  B.querySelectorAll(".r-listen").forEach(b=>b.onclick=()=>speak(b,b.closest(".r-sum").querySelector("p").textContent,b.dataset.lang));
  R.hidden=false;document.documentElement.classList.add("r-open");R.scrollTop=0;
  requestAnimationFrame(()=>{if(!R.hidden)R.classList.add("show")});document.getElementById("rTitle").focus({preventScroll:true});document.title=it.title+" · Good News Daily";
 }
 function close(){if(R.hidden)return;stop();R.classList.remove("show");R.hidden=true;
  document.documentElement.classList.remove("r-open");background.forEach((inert,node)=>node.inert=inert);background.clear();
  document.title="Good News Daily — the day's uplifting stories";
  if(cur&&window.GN_render){GN_render();setTimeout(()=>GN.maybeRemind(),900)}
  const target=returnFocus?.isConnected?returnFocus:returnHref?[...document.querySelectorAll("a[href]")].find(a=>a.getAttribute("href")===returnHref):null;
  (target||document.querySelector("#tabs button")||document.getElementById("main")).focus({preventScroll:true});cur=null;
 }
 function route(){const m=location.hash.match(/^#\/s\/([\w-]+)/);if(m&&DATA.length)open(m[1]);else if(!m)close()}
 addEventListener("hashchange",()=>{fromList=/#\/s\//.test(location.hash);route()});
 addEventListener("keydown",e=>{if(R.hidden)return;
  if(e.key==="Escape"){e.preventDefault();document.getElementById("rBack").click()}
  if(e.key==="Tab"){const targets=[...R.querySelectorAll('button:not(:disabled),a[href]')].filter(node=>node.getClientRects().length);
   const first=targets[0],last=targets[targets.length-1];
   if(e.shiftKey&&(document.activeElement===first||!targets.includes(document.activeElement))){e.preventDefault();last?.focus()}
   else if(!e.shiftKey&&(document.activeElement===last||!targets.includes(document.activeElement))){e.preventDefault();first?.focus()}}
 });
 let sx=0,sy=0,st=0;
 R.addEventListener("touchstart",e=>{const t=e.touches[0];sx=t.clientX;sy=t.clientY;st=Date.now()},{passive:true});
 R.addEventListener("touchend",e=>{const t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;
  if(Math.abs(dx)>70&&Math.abs(dy)<60&&Date.now()-st<700&&NAV.nx){B.classList.add(dx<0?"sw-l":"sw-r");setTimeout(()=>{B.classList.remove("sw-l","sw-r");location.hash="#/s/"+(dx<0?NAV.nx:NAV.pv).id},160)}},{passive:true});
 window.onData=d=>{DATA=d;route()};
 if(window.GN_data)onData(window.GN_data);
})();
