const CATS={all:["All","✨"],saved:["Saved","🔖"],telugu:["తెలుగు","🪔"],india:["India · AP/TS","🇮🇳"],science:["Science","🔭"],health:["Health","🌿"],community:["Kindness","🤝"],environment:["Environment","🌍"],tech:["Tech","💡"],sports:["Sports","🏏"]};
const GRAD={science:["#5b6cff","#9fb4ff"],health:["#13a37f","#8be3c4"],community:["#f26b3a","#ffc46b"],environment:["#3f9d3a","#b6e388"],india:["#ff9933","#e2452b"],telugu:["#c2185b","#ffb36b"],tech:["#7c4dff","#4fc3f7"],sports:["#0277bd","#4dd0e1"]};
const $=s=>document.querySelector(s);const isTe=s=>/[\u0C00-\u0C7F]/.test(s);
const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ago=iso=>{const m=(Date.now()-new Date(iso))/6e4;if(m<60)return Math.max(1,m|0)+"m ago";if(m<1440)return (m/60|0)+"h ago";return (m/1440|0)+"d ago"};
const thumb=(it,cls="thumb",priority=false)=>{const g=GRAD[it.category]||GRAD.community;
 const image=it.image&&/^https?:\/\//i.test(it.image)?`<img src="${esc(it.image)}" alt="" width="640" height="420" loading="${priority?"eager":"lazy"}" decoding="async"${priority?' fetchpriority="high"':""}>`:CATS[it.category][1];
 return `<div class="${cls}${it.image?"":" ph"}" aria-hidden="true" style="background:linear-gradient(135deg,${g[0]},${g[1]})">${image}</div>`};
const meta=it=>`<div class="meta"><span class="pill" style="--c:${(GRAD[it.category]||GRAD.community)[0]}">${CATS[it.category][0]}</span><span>${esc(it.source)}</span><span class="dot">•</span><time datetime="${it.published}">${ago(it.published)}</time></div>`;
const card=(it,i)=>`<a class="card${GN.isRead(it.id)?" read":""}" href="#/s/${it.id}" style="animation-delay:${Math.min(i,12)*45}ms">${thumb(it)}<div class="txt">${meta(it)}<h3 lang="${isTe(it.title)?"te":"en"}" class="${isTe(it.title)?"te":""}">${esc(it.title)}</h3><p lang="${isTe(it.summary)?"te":"en"}" class="${isTe(it.summary)?"te":""}">${esc(it.summary)}</p></div></a>`;
const wide=matchMedia("(min-width:1080px)");
let DATA=[],cur="all";
function mix(a){const g={};a.forEach(x=>(g[x.category]=g[x.category]||[]).push(x));const ks=Object.keys(g),o=[];
 for(let i=0;o.length<a.length;i++)ks.forEach(k=>{if(g[k][i])o.push(g[k][i])});return o}
const thoughtCard=()=>{const t=window.THOUGHTS&&GN.thought(THOUGHTS);if(!t)return"";
 return `<section class="thought"><div class="th-k">🌅 Good thought of the day · ఈ రోజు మంచి మాట</div><p class="th-te te" lang="te">“${esc(t.te)}”</p><p class="th-en">“${esc(t.en)}”</p><div class="th-by">— ${esc(t.by_te)} · ${esc(t.by)}</div></section>`};
function today5Html(){const t5=GN.today5(DATA);window.GN_today5=t5;const rd=GN.readToday(),n=t5.filter(x=>rd.includes(x.id)).length;
 return `<div class="t5-h"><h2>Today's 5 <span class="te" lang="te">· ఈ రోజు 5</span></h2><div class="t5-p" aria-label="${n} of 5 read today"><b>${n}</b> of 5 read<span class="t5-dots">${t5.map(x=>`<i class="${rd.includes(x.id)?"on":""}"></i>`).join("")}</span></div></div>
 <div class="t5" id="t5">${t5.map((it,i)=>{return `<a class="t5-c${rd.includes(it.id)?" read":""}" href="#/s/${it.id}">${thumb(it,"img",i===0)}<span class="t5-n">${i+1}</span>${rd.includes(it.id)?'<span class="t5-ok">✓ Read</span>':""}<div class="body">${meta(it)}<h3 lang="${isTe(it.title)?"te":"en"}" class="${isTe(it.title)?"te":""}">${esc(it.title)}</h3></div></a>`}).join("")}</div>`}
function endCard(){const [en,te]=GN.nextUpdate();return `<div class="endcard"><div class="ec-i">🌼</div><h3>You're all caught up</h3><p class="te" lang="te">అన్నీ చదివేశారు! కొత్త వార్తలు ${te}.</p><p>New stories at ${en}.</p></div>`}
function render(){let list=cur==="all"?mix(DATA):cur==="saved"?GN.saved():DATA.filter(x=>x.category===cur);
 const st=GN.streak(),se=$("#streak");if(st>0){se.hidden=false;se.innerHTML=`🌼 ${st} day${st>1?"s":""}`;se.title=`You've read good news ${st} day(s) in a row`}
 if(cur==="saved"){$("#hero").innerHTML=`<div class="saved-h"><h2>🔖 Saved stories</h2><p>${list.length?"Kept on this phone only.":"Tap 🔖 on any story to keep it here for later."}</p></div>`;window.GN_order=list;$("#feed").innerHTML=list.map(card).join("");return}
 if(cur==="all"){const t5=GN.today5(DATA);$("#hero").innerHTML=today5Html()+thoughtCard();const ids=new Set(t5.map(x=>x.id));const rest=list.filter(x=>!ids.has(x.id));window.GN_order=[...t5,...rest];
  $("#feed").innerHTML=rest.map(card).join("")+endCard();return}
 const lead=list.find(x=>x.image)||list[0];const rest=list.filter(x=>x!==lead);window.GN_order=lead?[lead,...rest]:[];
 if(!lead){$("#hero").innerHTML="";$("#feed").innerHTML='<p class="empty">No uplifting stories here yet today — check back tomorrow 🌱</p>';return}
 $("#hero").innerHTML=`<a class="hero${GN.isRead(lead.id)?" read":""}" href="#/s/${lead.id}">${thumb(lead,"img",true)}<div class="body">${meta(lead)}<h2 lang="${isTe(lead.title)?"te":"en"}" class="${isTe(lead.title)?"te":""}">${esc(lead.title)}</h2><p>${esc(lead.summary)}</p></div></a>`
  +(wide.matches?`<div class="side">${rest.slice(0,4).map(card).join("")}</div>`:"");
 const feed=wide.matches?rest.slice(4):rest;$("#feed").innerHTML=feed.map(card).join("")+endCard();}
window.GN_render=()=>{tabs();render()};
function tabs(){const focused=document.activeElement?.dataset.k;const c={all:DATA.length,saved:GN.saved().length};DATA.forEach(x=>c[x.category]=(c[x.category]||0)+1);
 $("#tabs").innerHTML=Object.keys(CATS).filter(k=>c[k]).map(k=>`<button class="tab" aria-pressed="${k===cur}" data-k="${k}">${CATS[k][1]} ${CATS[k][0]}<span class="n">${c[k]}</span></button>`).join("");
 if(focused)document.querySelector(`[data-k="${focused}"]`)?.focus({preventScroll:true});}
$("#tabs").onclick=e=>{const b=e.target.closest(".tab");if(!b)return;cur=b.dataset.k;$("#tabs").querySelectorAll("button").forEach(tab=>tab.setAttribute("aria-pressed",tab===b));render();scrollTo({top:0,behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth"})};
const th=GN.LS.get("theme",null)||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");document.documentElement.dataset.theme=th;
$("#theme").onclick=()=>{const t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=t;GN.LS.set("theme",t)};
$("#date").textContent=new Date().toLocaleDateString(undefined,{weekday:"long",month:"long",day:"numeric"});
const p=new URLSearchParams(location.search);if(["dark","light"].includes(p.get("theme")))document.documentElement.dataset.theme=p.get("theme");if(Object.hasOwn(CATS,p.get("cat")))cur=p.get("cat");
fetch("data/thoughts.json").then(r=>r.json()).then(t=>{window.THOUGHTS=t;if(DATA.length&&cur==="all")$("#hero").insertAdjacentHTML("beforeend",thoughtCard())}).catch(()=>{});
fetch("data/news.json",{cache:"default"}).then(r=>{if(!r.ok)throw new Error("News unavailable");return r.json()}).then(d=>{
 // Transitional legacy feed adapter until routine runs summarize v6
 d.items.forEach(it=>{if(!("summary_status" in it)){const p=typeof it.sum_en==="string"&&it.sum_en!==""&&typeof it.sum_te==="string"&&it.sum_te!=="";it.summary_status=p?"paired":"excerpt";if(!p){it.sum_en="";it.sum_te=""}}else if(it.summary_status==="summary"&&(!it.sum_en||!it.sum_te)){it.summary_status="excerpt"}});
 DATA=d.items;window.GN_data=DATA;$("#gen").textContent="Updated "+new Date(d.generated).toLocaleString()+".";tabs();render();window.onData&&onData(DATA)}).catch(()=>{$("#feed").innerHTML='<p class="empty" role="alert">News could not load. Please refresh to try again.</p>'});
wide.addEventListener("change",()=>{if(DATA.length)render()});
