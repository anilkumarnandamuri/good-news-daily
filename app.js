const CATS={all:["All","✨"],telugu:["తెలుగు","🪔"],india:["India · AP/TS","🇮🇳"],science:["Science","🔭"],health:["Health","🌿"],community:["Community","🤝"],environment:["Environment","🌍"],tech:["Tech","💡"]};
const GRAD={science:["#5b6cff","#9fb4ff"],health:["#13a37f","#8be3c4"],community:["#f26b3a","#ffc46b"],environment:["#3f9d3a","#b6e388"],india:["#ff9933","#e2452b"],telugu:["#c2185b","#ffb36b"],tech:["#7c4dff","#4fc3f7"]};
const $=s=>document.querySelector(s);const isTe=s=>/[\u0C00-\u0C7F]/.test(s);
const esc=s=>(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ago=iso=>{const m=(Date.now()-new Date(iso))/6e4;if(m<60)return Math.max(1,m|0)+"m ago";if(m<1440)return (m/60|0)+"h ago";return (m/1440|0)+"d ago"};
const thumb=(it,cls="thumb")=>{const g=GRAD[it.category]||GRAD.community;const bg=`linear-gradient(135deg,${g[0]},${g[1]})`;
 return it.image?`<div class="${cls}" style="background-image:url('${esc(it.image)}'),${bg}"></div>`:`<div class="${cls} ph" style="background:${bg}">${CATS[it.category][1]}</div>`};
const meta=it=>`<div class="meta"><span class="pill" style="--c:${(GRAD[it.category]||GRAD.community)[0]}">${CATS[it.category][0]}</span><span>${esc(it.source)}</span><span class="dot">•</span><time datetime="${it.published}">${ago(it.published)}</time></div>`;
const card=(it,i)=>`<a class="card" href="${esc(it.link)}" target="_blank" rel="noopener" style="animation-delay:${Math.min(i,12)*45}ms">${thumb(it)}<div class="txt">${meta(it)}<h3 class="${isTe(it.title)?"te":""}">${esc(it.title)}</h3><p class="${isTe(it.summary)?"te":""}">${esc(it.summary)}</p></div></a>`;
let DATA=[],cur="all";
function render(){const list=cur==="all"?DATA:DATA.filter(x=>x.category===cur);
 const lead=list.find(x=>x.image)||list[0];const rest=list.filter(x=>x!==lead);
 if(!lead){$("#hero").innerHTML="";$("#feed").innerHTML='<p class="empty">No uplifting stories here yet today — check back tomorrow 🌱</p>';return}
 const g=GRAD[lead.category];
 $("#hero").innerHTML=`<a class="hero" href="${esc(lead.link)}" target="_blank" rel="noopener"><div class="img" style="background-image:${lead.image?`url('${esc(lead.image)}'),`:""}linear-gradient(135deg,${g[0]},${g[1]})"></div><div class="body">${meta(lead)}<h2 class="${isTe(lead.title)?"te":""}">${esc(lead.title)}</h2><p>${esc(lead.summary)}</p></div></a>`
  +(innerWidth>=1080?`<div class="side">${rest.slice(0,4).map(card).join("")}</div>`:"");
 const feed=innerWidth>=1080?rest.slice(4):rest;$("#feed").innerHTML=feed.map(card).join("");}
function tabs(){const c={all:DATA.length};DATA.forEach(x=>c[x.category]=(c[x.category]||0)+1);
 $("#tabs").innerHTML=Object.keys(CATS).filter(k=>c[k]).map(k=>`<button class="tab" role="tab" aria-selected="${k===cur}" data-k="${k}">${CATS[k][1]} ${CATS[k][0]}<span class="n">${c[k]}</span></button>`).join("");}
$("#tabs").onclick=e=>{const b=e.target.closest(".tab");if(!b)return;cur=b.dataset.k;tabs();render();scrollTo({top:0,behavior:"smooth"})};
const th=localStorage.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");document.documentElement.dataset.theme=th;
$("#theme").onclick=()=>{const t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=localStorage.theme=t};
$("#date").textContent=new Date().toLocaleDateString(undefined,{weekday:"long",month:"long",day:"numeric"});
const p=new URLSearchParams(location.search);if(p.get("theme"))document.documentElement.dataset.theme=p.get("theme");if(p.get("cat"))cur=p.get("cat");
fetch("data/news.json",{cache:"no-cache"}).then(r=>r.json()).then(d=>{DATA=d.items;$("#gen").textContent="Updated "+new Date(d.generated).toLocaleString()+".";tabs();render()});
let rt;addEventListener("resize",()=>{clearTimeout(rt);rt=setTimeout(render,200)});
