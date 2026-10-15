(function(){
 const R=document.getElementById("reader"),B=document.getElementById("rBody");
 const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
 const CAT={science:["Science","🔭"],health:["Health","🌿"],community:["Kindness","🤝"],environment:["Environment","🌍"],india:["India · AP/TS","🇮🇳"],telugu:["తెలుగు","🪔"],tech:["Tech","💡"],sports:["Sports","🏏"]};
 const COL={science:"#5b6cff",health:"#13a37f",community:"#f26b3a",environment:"#3f9d3a",india:"#e2452b",telugu:"#c2185b",tech:"#7c4dff",sports:"#0277bd"};
 let DATA=[],NAV={},cur=null,fromList=false,speaking=null,returnFocus=null,returnHref=null;
 const background=new Map();
 const ago=iso=>{const m=(Date.now()-new Date(iso))/6e4;if(m<60)return Math.max(1,m|0)+" min ago";if(m<1440)return (m/60|0)+" hours ago";return (m/1440|0)+" days ago"};
 // font size
 let fs=Number(GN.LS.get("rfs",1.15));const setFs=v=>{fs=Math.min(1.8,Math.max(1,Number.isFinite(v)?v:1.15));GN.LS.set("rfs",fs);R.style.setProperty("--rfs",fs)};setFs(fs);
 document.getElementById("rSm").onclick=()=>setFs(fs-.15);document.getElementById("rLg").onclick=()=>setFs(fs+.15);
 document.getElementById("rBack").onclick=()=>{fromList?history.back():(location.hash="")};
 document.getElementById("rShare").onclick=async()=>{const u=location.href;try{if(navigator.share)await navigator.share({title:cur&&cur.title,url:u});else{await navigator.clipboard.writeText(u);toast("Link copied ✓")}}catch(e){}};
 function toast(t){const d=document.createElement("div");d.className="r-toast";d.textContent=t;d.setAttribute("role","status");R.appendChild(d);setTimeout(()=>d.remove(),2600)}
 // speech
 function voiceFor(lang){const vs=speechSynthesis.getVoices();const want=lang==="te"?["te-IN","te"]:["en-IN","en-GB","en-US","en"];
  for(const w of want){const v=vs.find(v=>v.lang.replace("_","-").toLowerCase().startsWith(w.toLowerCase()));if(v)return v}return null}
 function isVoiceEnabled(){try{const p=new URLSearchParams(window.location.search);if(p.get("voice")==="1")return true}catch(e){}try{if(window.localStorage&&window.localStorage.getItem("gn-voice")==="1")return true}catch(e){}return false}
 let summariesData=null,summariesPromise=null,manifestData=null,manifestURL=null,manifestPromise=null,sampleNews=null,samplePromise=null,voiceModule=null,voicePromise=null;
 function getSummaries(){if(!summariesPromise){summariesPromise=fetch("data/summaries.json").then(r=>r.ok?r.json():{}).then(d=>{summariesData=d;return d}).catch(()=>({}))}return summariesPromise}
 function getManifest(){if(!manifestPromise){const u=new URL("voice/demo/audio/manifest.json",document.baseURI).href;manifestPromise=fetch(u).then(r=>r.ok?r.json():{}).then(m=>{manifestData=m;manifestURL=u;return{manifest:m,manifestURL:u}}).catch(()=>({manifest:{},manifestURL:document.baseURI}))}return manifestPromise}
 function getSampleNews(){if(!samplePromise){samplePromise=fetch("voice/sample/news.json").then(r=>r.ok?r.json():{items:[]}).then(d=>{sampleNews=d.items||[];return sampleNews}).catch(()=>[])}return samplePromise}
 function getVoiceModule(){if(!voicePromise){voicePromise=import("./voice/src/gn-voice.js").then(m=>{voiceModule=m;return m})}return voicePromise}
 if(isVoiceEnabled()){getSummaries();getManifest();getVoiceModule();getSampleNews()}

 let activePlayer=null,activeBtn=null,activeSentenceEls=[];
 function clearHighlight(){if(activeSentenceEls&&activeSentenceEls.length){activeSentenceEls.forEach(el=>{el.classList.remove("is-active","active","highlight");el.removeAttribute("aria-current")})}}
 function highlightSentence(idx){if(!activeSentenceEls||!activeSentenceEls.length)return;activeSentenceEls.forEach((el,i)=>{const on=(i===idx);el.classList.toggle("is-active",on);el.classList.toggle("active",on);el.classList.toggle("highlight",on);if(on){el.setAttribute("aria-current","true");try{el.scrollIntoView({block:"nearest",behavior:"smooth"})}catch(e){}}else{el.removeAttribute("aria-current")}})}
 function stopVoice(){if(activePlayer){try{activePlayer.destroy()}catch(e){}activePlayer=null}if(activeBtn){activeBtn.classList.remove("on");const sp=activeBtn.querySelector("span");if(sp)sp.textContent="🔊 Listen";activeBtn=null}clearHighlight();activeSentenceEls=[];window.__readerPlayer=null}
 function stop(){stopVoice();if("speechSynthesis" in window)speechSynthesis.cancel();if(speaking){speaking.classList.remove("on");speaking.querySelector("span").textContent="🔊 Listen"}speaking=null}
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

 async function playVoice(btn,lang,story){
  if(activeBtn===btn&&activePlayer&&activePlayer.isPlaying){stopVoice();return}stop();
  const container=btn.closest(".r-sum");activeSentenceEls=container?[...container.querySelectorAll(".r-sentence")]:[];
  let sentences=[];
  if(story&&story.pairs&&story.pairs.length){sentences=story.pairs.map(p=>p[lang]||"").filter(Boolean)}
  if(!sentences.length){const txt=(story&&story["sum_"+lang])||(story&&story.lang===lang?story.summary:"")||"";sentences=(txt.match(/[^.!?।॥…]+[.!?।॥…]*|[.!?।॥…]+/gu)||[]).map(s=>s.trim()).filter(Boolean)}
  const {VoicePlayer}=await getVoiceModule();const {manifest,manifestURL}=await getManifest();
  class ReaderVoicePlayer extends VoicePlayer{_makeQueue(){const ok=super._makeQueue();if(ok&&sentences.length){for(const it of this.queue){if(!it.intro){it.chunks=sentences.slice()}}}return ok}}
  const player=new ReaderVoicePlayer({language:lang,preferAudio:true,radio:false});
  player.setStories([story],{manifest,manifestURL,limit:1});
  player.audio.addEventListener("timeupdate",()=>{if(player.mode==="audio"&&player.audio.duration>0&&sentences.length){const curT=player.audio.currentTime,dur=player.audio.duration;const totalChars=sentences.reduce((acc,s)=>acc+s.length,0)||1;let accum=0,activeIdx=0;for(let i=0;i<sentences.length;i++){accum+=sentences[i].length;if(curT<=(accum/totalChars)*dur||i===sentences.length-1){activeIdx=i;break}}highlightSentence(activeIdx)}});
  player.addEventListener("statechange",()=>{if(player.state==="playing"){btn.classList.add("on");const sp=btn.querySelector("span");if(sp)sp.textContent="⏹ Stop";if(player.mode==="speech"){highlightSentence(player.chunkIndex)}else if(player.mode==="audio"){highlightSentence(0)}}else if(player.state==="ended"||player.state==="idle"){stopVoice()}else if(player.state==="error"){toast(player.message||(lang==="te"?"తెలుగు వాయిస్ లేదు":"Speech unavailable"));stopVoice()}});
  player.addEventListener("progress",()=>{if(player.mode==="speech"){highlightSentence(player.chunkIndex)}});
  player.addEventListener("ended",()=>stopVoice());
  activePlayer=player;activeBtn=btn;window.__readerPlayer=player;btn.classList.add("on");const sp=btn.querySelector("span");if(sp)sp.textContent="⏹ Stop";
  highlightSentence(0);player.play();
 }

 function block(lang,text,pairs){if(!text)return"";const te=lang==="te";
  let contentHtml=`<p>${esc(text)}</p>`;
  if(isVoiceEnabled()){let sents=[];if(pairs&&pairs.length){sents=pairs.map(p=>p[lang]||"").filter(Boolean)}if(!sents.length){sents=(text.match(/[^.!?।॥…]+[.!?।॥…]*|[.!?।॥…]+/gu)||[]).map(s=>s.trim()).filter(Boolean)}if(sents.length){contentHtml=`<p class="r-sentences" data-lang="${lang}">`+sents.map((s,idx)=>`<span class="r-sentence" data-idx="${idx}">${esc(s)}</span>`).join(" ")+`</p>`}}
  return `<section class="r-sum ${te?"te":""}" lang="${te?"te":"en"}"><div class="r-sh"><h2>${te?"తెలుగులో సారాంశం":"In short"}</h2>
  <button class="r-listen" data-lang="${lang}"><span>🔊 Listen</span></button></div>${contentHtml}</section>`}

 function renderBody(it){
  const c=CAT[it.category]||CAT.community,col=COL[it.category]||"#f26b3a";
  const first=it.lang==="te"?[["te",it.sum_te],["en",it.sum_en]]:[["en",it.sum_en],["te",it.sum_te]];
  const excerpt=it.summary_status!=="paired"||!it.sum_en||!it.sum_te;
  const fallback=excerpt?`<section class="r-sum ${it.lang==="te"?"te":""}" lang="${it.lang==="te"?"te":"en"}"><h2 lang="en">Publisher excerpt</h2><p>${esc(it.summary)}</p><p class="r-note" lang="en">A complete bilingual summary is not available yet.</p></section>`:"";
  B.innerHTML=`${thumb(it,"r-img",true)}
  <div class="r-card"><div class="r-meta"><span class="pill" style="--c:${col}">${c[1]} ${c[0]}</span><span>${esc(it.source)}</span><span class="dot">•</span><time>${ago(it.published)}</time></div>
  <h1 id="rTitle" tabindex="-1" lang="${it.lang==="te"?"te":"en"}" class="${/[\u0C00-\u0C7F]/.test(it.title)?"te":""}">${esc(it.title)}</h1>
  ${excerpt?fallback:first.map(([l,t])=>block(l,t,it.pairs)).join("")}

  <div class="r-acts"><a class="r-wa" id="rWa" href="#" target="_blank" rel="noopener"><svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M16 3C8.8 3 3 8.7 3 15.8c0 2.5.7 4.9 2 7L3 29l6.4-2c2 1.1 4.300 1.700 6.600 1.700 7.200 0 13-5.700 13-12.800S23.200 3 16 3zm0 23.300c-2.100 0-4.100-.6-5.900-1.700l-.4-.2-3.800 1.200 1.200-3.700-.3-.4c-1.200-1.800-1.800-3.900-1.800-6 0-6 4.900-10.800 11-10.800s11 4.800 11 10.800S22.100 26.300 16 26.300zm6-8.100c-.3-.2-1.900-1-2.200-1.100-.3-.1-.5-.2-.7.200-.2.300-.8 1-1 1.200-.2.200-.4.200-.7.100-.3-.2-1.400-.5-2.600-1.600-1-.9-1.600-1.900-1.800-2.200-.2-.3 0-.5.100-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6l-1-2.400c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.400-.3.300-1.100 1.100-1.100 2.700s1.200 3.100 1.300 3.300c.2.200 2.300 3.500 5.500 4.900 2.700 1.100 3.300.9 3.900.8.600-.1 1.900-.8 2.200-1.500.3-.7.3-1.400.2-1.500-.1-.2-.3-.3-.6-.4z"/></svg>Share on WhatsApp</a>
  <button class="r-save2" id="rSave2"></button></div>
  <a class="r-cta" href="${esc(it.link)}" target="_blank" rel="noopener">Read full story at ${esc(it.source)} <b>↗</b></a>
  <p class="r-note">${excerpt?"Excerpt supplied by the publisher":"Bilingual summary by Good News Daily. Translations may contain errors"}. The full article belongs to ${esc(it.source)}.</p>
  <a class="r-next" href="#/s/${NAV.nx.id}"><small>Next story →</small><span class="${/[\u0C00-\u0C7F]/.test(NAV.nx.title)?"te":""}">${esc(NAV.nx.title)}</span></a>
  <p class="r-swipe">👆 Swipe left or right for more stories</p></div>
  <nav class="r-nav"><a href="#/s/${NAV.pv.id}" class="r-pv">← Previous</a><a href="#/s/${NAV.nx.id}" class="r-nx">Next story →</a></nav>`;
  const teHead=excerpt||/[\u0C00-\u0C7F]/.test(it.title)?it.title:((it.sum_te||"").split(/(?<=[.!?])\s/)[0]||it.title);
  const snip=(excerpt?it.summary:(it.lang==="te"?it.sum_te:it.sum_en))||it.summary||"";const cut=snip.length>160?snip.slice(0,160).replace(/\s\S*$/,"")+"…":snip;
  document.getElementById("rWa").href="https://wa.me/?text="+encodeURIComponent(`🌼 ${teHead}\n\n${cut}\n\n👉 ${location.origin+location.pathname}#/s/${it.id}\n— Good News Daily`);
  const paintSave=()=>{const on=GN.isSaved(it.id);const b=document.getElementById("rSave");b.setAttribute("aria-pressed",on);b.classList.toggle("on",on);document.getElementById("rSave2").innerHTML=on?"✓ Saved":"🔖 Save for later";document.getElementById("rSave2").classList.toggle("on",on)};
  document.getElementById("rSave").onclick=document.getElementById("rSave2").onclick=()=>{const on=GN.toggleSave(it);paintSave();toast(on?"Saved 🔖 — find it in the Saved tab":"Removed from Saved")};paintSave();
  GN.markRead(it);
  B.querySelectorAll(".r-listen").forEach(b=>b.onclick=()=>{if(isVoiceEnabled())playVoice(b,b.dataset.lang,cur);else speak(b,b.closest(".r-sum").querySelector("p").textContent,b.dataset.lang)});
 }

 function open(id,customIt){
  let it=customIt||DATA.find(x=>x.id===id)||GN.saved().find(x=>x.id===id);
  if(!it&&isVoiceEnabled()){getSampleNews().then(items=>{const found=items.find(x=>x.id===id);if(found&&(!cur||cur.id!==id))open(id,found)});return}
  if(!it)return;
  if(isVoiceEnabled()){
   const attach=s=>{if(s&&s[it.id]?.pairs){it.pairs=s[it.id].pairs;it.sum_en=it.sum_en||s[it.id].en;it.sum_te=it.sum_te||s[it.id].te;it.summary_status="paired"}};
   if(summariesData)attach(summariesData);
   else getSummaries().then(s=>{attach(s);if(cur&&cur.id===it.id&&it.pairs)renderBody(it)});
  }
  if(R.hidden){returnFocus=document.activeElement;returnHref=returnFocus?.closest("a")?.getAttribute("href");
   [...document.body.children].filter(node=>node!==R).forEach(node=>{background.set(node,node.inert);node.inert=true})}
  cur=it;stop();
  const ord=(window.GN_order&&window.GN_order.some(x=>x.id===id))?window.GN_order:DATA;
  let i=ord.findIndex(x=>x.id===id);
  const nx=i>=0?ord[(i+1)%ord.length]:it,pv=i>=0?ord[(i-1+ord.length)%ord.length]:it;
  NAV={nx,pv};
  renderBody(it);
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
