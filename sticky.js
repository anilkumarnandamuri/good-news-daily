/* Good News Daily — local-only habits: read marks, streak, saved stories, Today's 5, banners. No accounts. */
(function(){
 const LS={get(k,d){try{return JSON.parse(localStorage.getItem("gn_"+k))??d}catch(e){return d}},set(k,v){try{localStorage.setItem("gn_"+k,JSON.stringify(v))}catch(e){}}};
 for(const key of ["theme"]){try{const old=localStorage.getItem(key);if(old!==null&&localStorage.getItem("gn_"+key)===null)LS.set(key,old)}catch(e){}}
 const day=(d=new Date())=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
 const GN=window.GN={
  isRead:id=>!!LS.get("read",{})[id],
  markRead(it){const r=LS.get("read",{});if(!r[it.id]){r[it.id]=Date.now();const ks=Object.keys(r);if(ks.length>600)ks.sort((a,b)=>r[a]-r[b]).slice(0,ks.length-600).forEach(k=>delete r[k]);LS.set("read",r)}
   const ds=LS.get("days",[]);if(!ds.includes(day())){ds.push(day());LS.set("days",ds.slice(-400))}
   const t=LS.get("today",{d:"",ids:[]});if(t.d!==day()){t.d=day();t.ids=[]}if(!t.ids.includes(it.id))t.ids.push(it.id);LS.set("today",t)},
  readToday(){const t=LS.get("today",{d:"",ids:[]});return t.d===day()?t.ids:[]},
  streak(){const ds=new Set(LS.get("days",[]));let n=0,d=new Date();if(!ds.has(day(d)))d.setDate(d.getDate()-1);while(ds.has(day(d))){n++;d.setDate(d.getDate()-1)}return n},
  saved:()=>LS.get("saved",[]),
  isSaved:id=>LS.get("saved",[]).some(x=>x.id===id),
  toggleSave(it){let s=LS.get("saved",[]);const on=s.some(x=>x.id===it.id);s=on?s.filter(x=>x.id!==it.id):[{...it,savedAt:Date.now()},...s].slice(0,100);LS.set("saved",s);return !on},
  today5(data){const out=[],seen=new Set();[...data].sort((a,b)=>b.score-a.score).forEach(x=>{if(out.length<5&&!seen.has(x.category)){seen.add(x.category);out.push(x)}});return out},
  nextUpdate(){const h=new Date().getHours();return h<7?["7 AM","ఉదయం 7 గంటలకు"]:h<19?["7 PM","సాయంత్రం 7 గంటలకు"]:["7 AM tomorrow","రేపు ఉదయం 7 గంటలకు"]},
  thought(list){const d=new Date(),n=Math.floor((d-new Date(d.getFullYear(),0,0))/864e5);return list[n%list.length]},
  LS,day
 };
 // One root scale for the list and reader; migrate before app/reader render.
 const normalize=v=>{const n=Number(v);return Math.round(Math.min(1.6,Math.max(.85,Number.isFinite(n)?n:1))*100)/100};
 let scale=LS.get("textScale",null);
 if(scale===null){
  const old=LS.get("rfs",null);let legacy=old;
  if(legacy===null){try{legacy=localStorage.getItem("rfs")}catch(e){}}
  scale=legacy===null||Number(legacy)===1.15?1:normalize(legacy);
 }
 scale=normalize(scale);
 try{for(const key of ["gn_largeText","gn_rfs","rfs"])localStorage.removeItem(key)}catch(e){}
 GN.textScale={min:.85,max:1.6,step:.15,get:()=>scale,set(v){scale=normalize(v);LS.set("textScale",scale);document.documentElement.style.fontSize=Math.round(scale*100)+"%";return scale}};
 GN.textScale.set(scale);
 // ---- banners: install (Android/Chrome) + gentle notification reminder ----
 let deferred=null;
 function banner(id,html,onYes){if(document.getElementById(id))return;const b=document.createElement("div");b.className="gn-banner";b.id=id;b.innerHTML=html+'<button class="gb-x" aria-label="Dismiss">✕</button>';
  document.body.appendChild(b);requestAnimationFrame(()=>b.classList.add("show"));
  b.querySelector(".gb-yes").onclick=()=>{onYes();b.remove()};b.querySelector(".gb-x").onclick=()=>{LS.set("dismiss_"+id,Date.now());b.remove()}}
 const snoozed=id=>Date.now()-LS.get("dismiss_"+id,0)<7*864e5;
 addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferred=e;
  if(snoozed("install"))return;setTimeout(()=>banner("install",'<span class="gb-ic">📲</span><div class="gb-t"><b>Add Good News to your home screen</b><small>హోమ్ స్క్రీన్‌కు జోడించండి — ఒక్క తాకుతో తెరవండి</small></div><button class="gb-yes">Install</button>',
   async()=>{deferred.prompt();await deferred.userChoice;deferred=null}),4000)});
 GN.maybeRemind=function(){
  if(snoozed("notify")||window.GN_pushState!=="off"||GN.readToday().length<2||document.getElementById("install"))return;
  banner("notify",'<span class="gb-ic">🔔</span><div class="gb-t"><b>One happy story every morning?</b><small>రోజూ ఒక మంచి వార్త — ఉచితం</small></div><button class="gb-yes">Turn on</button>',
   ()=>{const b=document.getElementById("pushBtn");if(b){b.scrollIntoView({behavior:"smooth",block:"center"});b.click()}});
 };
})();
