const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const source=name=>fs.readFileSync(path.join(root,name),'utf8');

function environment({news=[],search='',storageBlocked=false}={}){
 const nodes=new Map(),listeners=new Map(),media=new Map(),stored=new Map();
 let document;
 class Element{
  constructor(id='',tag='div'){this.id=id;this.tagName=tag;this.dataset={};this.attributes={};this.inert=false;this.hidden=false;this.isConnected=true;this.children=[];this.writes=0;this.values=new Map();this.style={setProperty:(k,v)=>this.values.set(k,v)};const classes=new Set();this.classList={add:k=>classes.add(k),remove:k=>classes.delete(k),contains:k=>classes.has(k),toggle:(k,on)=>on?classes.add(k):classes.delete(k)}}
  set innerHTML(value){this.html=value;this.writes++;this.children.forEach(child=>child.isConnected=false);this.children=[];
   for(const match of value.matchAll(/<(button|a|h1)\b([^>]*)>/g)){
    const el=new Element('',match[1]);
    for(const attr of match[2].matchAll(/([\w-]+)="([^"]*)"/g)){
     el.setAttribute(attr[1],attr[2]);if(attr[1]==='id'){el.id=attr[2];nodes.set(el.id,el)}
    }
    el.parent=this;this.children.push(el);
   }
  }
  get innerHTML(){return this.html||''}
  setAttribute(k,v){this.attributes[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5)]=v}
  getAttribute(k){return this.attributes[k]??null}
  querySelector(selector){return ['span','.lbl'].includes(selector)?this.label: this.querySelectorAll(selector)[0]||null}
  querySelectorAll(selector){if(selector==='.r-listen')return [];return this.children.filter(el=>selector==='button'?el.tagName==='button':selector==='button:not(:disabled),a[href]'?['button','a'].includes(el.tagName):selector==='a[href]'?el.tagName==='a':false)}
  closest(selector){return selector==='a'&&this.tagName==='a'?this:selector==='.tab'&&this.dataset.k?this:null}
  focus(){document.activeElement=this}
  click(){this.onclick?.({target:this})}
  addEventListener(k,fn){this['on'+k]=fn}
  getClientRects(){return [{}]}
  insertAdjacentHTML(_,text){this.html=(this.html||'')+text}
  appendChild(el){this.children.push(el)}
  remove(){this.isConnected=false}
 }
 for(const id of ['hero','feed','tabs','theme','date','streak','gen','reader','rBody','rBack','rSave','rSm','rLg','rShare','main','push','pushBtn','pushHint'])nodes.set(id,new Element(id,['theme','rBack','rSave','rSm','rLg','rShare','pushBtn'].includes(id)?'button':'div'));
 nodes.get('reader').hidden=true;nodes.get('pushBtn').label=new Element();
 document={activeElement:new Element(),documentElement:new Element(),body:new Element(),title:'',getElementById:id=>nodes.get(id),
  querySelector(selector){if(selector==='#tabs button')return nodes.get('tabs').children[0];if(selector.startsWith('#'))return nodes.get(selector.slice(1));const m=selector.match(/data-k="([^"]+)"/);return m?nodes.get('tabs').children.find(b=>b.dataset.k===m[1]):null},
  querySelectorAll:selector=>selector==='a[href]'?nodes.get('feed').querySelectorAll(selector):[],createElement:()=>new Element()};
 document.body.children=[nodes.get('main'),nodes.get('tabs'),nodes.get('reader')];
 const ctx={document,console,URLSearchParams,Date,Map,Set,Number,Math,Promise,encodeURIComponent,
  navigator:{userAgent:'Test desktop',platform:'Linux',maxTouchPoints:0},location:{search,hash:'',href:'http://local/',origin:'http://local',pathname:'/'},history:{back(){ctx.location.hash='';listeners.get('hashchange')?.forEach(f=>f())}},
  matchMedia(q){if(!media.has(q))media.set(q,{matches:false,addEventListener(_,fn){this.change=fn}});return media.get(q)},
  addEventListener(k,fn){if(!listeners.has(k))listeners.set(k,[]);listeners.get(k).push(fn)},
  localStorage:{getItem(k){if(storageBlocked)throw new Error('Storage disabled');return stored.get(k)??null},removeItem(k){if(storageBlocked)throw new Error('Storage disabled');stored.delete(k)},setItem(k,v){if(storageBlocked)throw new Error('Storage disabled');stored.set(k,v)}},
  fetch:async url=>({ok:true,json:async()=>url.includes('thoughts')?[]:{generated:'2026-10-14T00:00:00Z',items:news}}),
  scrollTo(){},setTimeout(){},requestAnimationFrame:f=>f()};
 ctx.window=ctx;vm.createContext(ctx);
 const run=name=>vm.runInContext(source(name),ctx,{filename:name});
 const dispatch=(type,event)=>listeners.get(type)?.forEach(f=>f(event));
 return {ctx,nodes,media,stored,run,dispatch,Element};
}
const stories=JSON.parse(source('data/news.json')).items.slice(0,10);
const flush=()=>new Promise(resolve=>setImmediate(resolve));

test('scripts defer in dependency order and OneSignal paths stay unchanged',()=>{
 const html=source('index.html');
 const scripts=[...html.matchAll(/<script src="([^"]+)"([^>]*)>/g)];
 assert.deepEqual(scripts.filter(m=>!m[1].startsWith('https:')).map(m=>m[1]),['sticky.js','app.js','push.js','reader.js']);
 assert.ok(scripts.every(m=>/\bdefer\b/.test(m[2])));
 assert.ok(scripts.at(-1)[1].includes('OneSignalSDK.page.js'));
 assert.match(source('push.js'),/serviceWorkerPath:"good-news-daily\/OneSignalSDKWorker.js"/);
 assert.match(source('push.js'),/scope:"\/good-news-daily\/"/);
 assert.equal(source('OneSignalSDKWorker.js').trim(),"importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js');");
});

test('OneSignal initialization and subscription lifecycle work against an in-memory SDK',async()=>{
 const e=environment();e.ctx.Notification={};e.run('push.js');
 assert.equal(e.ctx.GN_pushState,'off');
 let init,callback,requests=0,optIns=0;
 const sdk={init:async value=>{init=value},User:{PushSubscription:{optedIn:false,addEventListener:(_,fn)=>callback=fn,optIn:async()=>{optIns++;sdk.User.PushSubscription.optedIn=true}}},Notifications:{permission:false,permissionNative:'default',requestPermission:async()=>requests++}};
 await e.ctx.OneSignalDeferred[0](sdk);
 assert.equal(init.appId,'ceb85e1d-3dcc-4b8f-b7a4-c2d8a4021242');
 await e.nodes.get('pushBtn').onclick();
 assert.equal(requests,1);assert.equal(optIns,1);assert.equal(e.ctx.GN_pushState,'on');
 assert.equal(e.nodes.get('pushBtn').disabled,true);
 sdk.User.PushSubscription.optedIn=false;sdk.Notifications.permissionNative='denied';callback();
 assert.equal(e.ctx.GN_pushState,'blocked');
});

test('iPhone installation hint remains available without calling the SDK',()=>{
 const e=environment();e.ctx.navigator.userAgent='iPhone';e.run('push.js');
 assert.equal(e.nodes.get('pushHint').hidden,false);assert.equal(e.ctx.OneSignalDeferred,undefined);
});

test('feed uses lazy dimensioned images and changing category retains the category button',async()=>{
 const e=environment({news:stories});e.run('sticky.js');e.run('app.js');await flush();
 assert.match(e.nodes.get('feed').innerHTML,/loading="lazy" decoding="async"/);
 assert.match(e.nodes.get('feed').innerHTML,/width="640" height="420"/);
 assert.equal((e.nodes.get('hero').innerHTML.match(/fetchpriority="high"/g)||[]).length,1);
 const tabs=e.nodes.get('tabs'),button=tabs.children.find(b=>b.dataset.k==='telugu');
 const writes=tabs.writes;button.focus();tabs.onclick({target:button});
 assert.equal(tabs.writes,writes);assert.equal(e.ctx.document.activeElement,button);
 assert.equal(button.getAttribute('aria-pressed'),'true');
 assert.ok(!e.nodes.get('feed').innerHTML.includes('background-image:url'));
});

test('single text scale defaults to normal, clamps, persists, and tolerates blocked storage',()=>{
 assert.ok(!source('index.html').includes('id="textSize"'));
 for(const storageBlocked of [false,true]){
  const e=environment({storageBlocked});e.run('sticky.js');e.run('reader.js');
  const scale=e.ctx.GN.textScale,html=e.ctx.document.documentElement;
  assert.equal(scale.get(),1);assert.equal(html.style.fontSize,'100%');
  e.nodes.get('rLg').click();assert.equal(scale.get(),1.15);assert.equal(html.style.fontSize,'115%');
  const toast=e.nodes.get('reader').children.at(-1);assert.equal(toast.textContent,'Text size 115%');assert.equal(toast.getAttribute('role'),'status');
  e.nodes.get('rSm').click();e.nodes.get('rSm').click();assert.equal(scale.get(),.85);
  assert.equal(e.nodes.get('rSm').disabled,true);assert.equal(e.nodes.get('rSm').getAttribute('aria-disabled'),'true');
  for(let i=0;i<10;i++)e.nodes.get('rLg').click();
  assert.equal(scale.get(),1.6);assert.equal(e.nodes.get('rLg').disabled,true);assert.equal(e.nodes.get('rLg').getAttribute('aria-disabled'),'true');
  assert.equal(e.nodes.get('rSm').disabled,false);
  if(!storageBlocked){assert.equal(e.stored.get('gn_textScale'),'1.6');e.run('sticky.js');assert.equal(e.ctx.GN.textScale.get(),1.6)}
  for(let i=0;i<10;i++)e.nodes.get('rSm').click();assert.equal(e.ctx.GN.textScale.get(),.85);
 }
});

test('text scale migrates merge defaults and legacy choices, preserving newer settings',()=>{
 for(const key of ['gn_rfs','rfs'])for(const [old,want] of [[1.15,1],[1.3,1.3],[.2,.85],[9,1.6],['invalid',1]]){
  const e=environment();e.stored.set(key,JSON.stringify(old));e.stored.set('gn_largeText','true');e.run('sticky.js');
  assert.equal(e.ctx.GN.textScale.get(),want);assert.equal(e.stored.get('gn_textScale'),String(want));
  for(const removed of ['gn_largeText','gn_rfs','rfs'])assert.equal(e.stored.has(removed),false);
 }
 const e=environment();e.stored.set('gn_textScale','1.45');e.stored.set('gn_rfs','1.15');e.run('sticky.js');assert.equal(e.ctx.GN.textScale.get(),1.45);
});

test('layout rerenders only at its media-query breakpoint',async()=>{
 const e=environment({news:stories,search:'?cat=telugu'});e.run('sticky.js');e.run('app.js');await flush();
 const before=e.nodes.get('feed').writes;e.dispatch('resize',{});assert.equal(e.nodes.get('feed').writes,before);
 const mq=e.media.get('(min-width:1080px)');mq.matches=true;mq.change();assert.equal(e.nodes.get('feed').writes,before+1);
});

test('reader enters dialog focus, makes background inert, labels excerpts, and restores focus',async()=>{
 const e=environment({news:stories});e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 const origin=e.nodes.get('feed').children[0];assert.ok(origin);origin.focus();
 e.ctx.location.hash=origin.getAttribute('href');e.dispatch('hashchange');
 assert.equal(e.nodes.get('reader').hidden,false);assert.equal(e.nodes.get('main').inert,true);
 assert.equal(e.ctx.document.activeElement.id,'rTitle');
 assert.match(e.nodes.get('rBody').innerHTML,/Publisher excerpt|Bilingual summary/);
 e.nodes.get('rBack').click();
 assert.equal(e.nodes.get('reader').hidden,true);assert.equal(e.nodes.get('main').inert,false);
 assert.equal(origin.isConnected,false);assert.notEqual(e.ctx.document.activeElement,origin);
 assert.equal(e.ctx.document.activeElement.getAttribute('href'),origin.getAttribute('href'));
});

test('reader traps forward and reverse keyboard focus and preserves save action',async()=>{
 const e=environment({news:stories});e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 const origin=e.nodes.get('feed').children[0];origin.focus();e.ctx.location.hash=origin.getAttribute('href');e.dispatch('hashchange');
 const first=e.nodes.get('rBack'),last=e.nodes.get('rShare');e.nodes.get('reader').children=[first,last];
 let prevented=0;first.focus();e.dispatch('keydown',{key:'Tab',shiftKey:true,preventDefault:()=>prevented++});assert.equal(e.ctx.document.activeElement,last);
 e.dispatch('keydown',{key:'Tab',shiftKey:false,preventDefault:()=>prevented++});assert.equal(e.ctx.document.activeElement,first);assert.equal(prevented,2);
 e.nodes.get('rSave').click();assert.equal(e.nodes.get('rSave').getAttribute('aria-pressed'),'true');
 assert.equal(e.ctx.GN.saved().length,1);
 e.dispatch('keydown',{key:'Escape',preventDefault(){}});assert.equal(e.nodes.get('reader').hidden,true);
});

test('old theme and reader size preferences migrate without overwriting newer choices',async()=>{
 const e=environment({news:stories});e.stored.set('theme','dark');e.stored.set('rfs','1.3');
 e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 assert.equal(e.ctx.document.documentElement.dataset.theme,'dark');assert.equal(e.ctx.document.documentElement.style.fontSize,'130%');
 const second=environment({news:stories});second.stored.set('theme','dark');second.stored.set('gn_theme','"light"');
 second.run('sticky.js');second.run('app.js');await flush();assert.equal(second.ctx.document.documentElement.dataset.theme,'light');
});

test('reader initializes when news resolves before the deferred reader script',async()=>{
 const e=environment({news:stories});e.run('sticky.js');e.run('app.js');await flush();
 e.ctx.location.hash='#/s/'+stories[0].id;e.run('reader.js');assert.equal(e.nodes.get('reader').hidden,false);
});

test('legacy saved summaries use the explicit excerpt fallback',async()=>{
 const legacy={...stories[0],id:'old-saved',sum_en:'A short old summary.',sum_te:'పాత సారాంశం.'};delete legacy.summary_status;
 const e=environment({news:stories});e.stored.set('gn_saved',JSON.stringify([legacy]));
 e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 e.ctx.location.hash='#/s/old-saved';e.dispatch('hashchange');
 assert.match(e.nodes.get('rBody').innerHTML,/Publisher excerpt/);assert.ok(!e.nodes.get('rBody').innerHTML.includes('A short old summary.'));
 const shared=decodeURIComponent(e.nodes.get('rWa').href);assert.ok(!shared.includes(legacy.sum_en));assert.ok(!shared.includes(legacy.sum_te));assert.ok(shared.includes(legacy.title));
});

test('feed item without summary_status but with both summaries renders the summaries',async()=>{
 const legacyItem={...stories[0],id:'legacy-feed-item',sum_en:'A complete English summary.',sum_te:'పూర్తి తెలుగు సారాంశం.'};delete legacyItem.summary_status;
 const e=environment({news:[legacyItem]});
 e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 e.ctx.location.hash='#/s/legacy-feed-item';e.dispatch('hashchange');
 assert.equal(e.nodes.get('reader').hidden,false);
 assert.ok(!e.nodes.get('rBody').innerHTML.includes('Publisher excerpt'));
 assert.ok(e.nodes.get('rBody').innerHTML.includes('A complete English summary.'));
 assert.ok(e.nodes.get('rBody').innerHTML.includes('పూర్తి తెలుగు సారాంశం.'));
 assert.match(e.nodes.get('rBody').innerHTML,/In short/);
});

test('reader renders summary status like paired with both summaries and listen controls',async()=>{
 const summaryItem={...stories[0],id:'summary-status-item',summary_status:'summary',sum_en:'A complete English summary.',sum_te:'పూర్తి తెలుగు సారాంశం.'};
 const e=environment({news:[summaryItem]});
 e.run('sticky.js');e.run('app.js');e.run('reader.js');await flush();
 e.ctx.location.hash='#/s/summary-status-item';e.dispatch('hashchange');
 assert.equal(e.nodes.get('reader').hidden,false);
 assert.ok(!e.nodes.get('rBody').innerHTML.includes('Publisher excerpt'));
 assert.ok(e.nodes.get('rBody').innerHTML.includes('A complete English summary.'));
 assert.ok(e.nodes.get('rBody').innerHTML.includes('పూర్తి తెలుగు సారాంశం.'));
 assert.match(e.nodes.get('rBody').innerHTML,/In short/);
 assert.match(e.nodes.get('rBody').innerHTML,/తెలుగులో సారాంశం/);
 assert.match(e.nodes.get('rBody').innerHTML,/r-listen/);
});

