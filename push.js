(function(){
 var btn=document.getElementById("pushBtn"),hint=document.getElementById("pushHint"),box=document.getElementById("push");
 var ua=navigator.userAgent,iOS=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1);
 var standalone=window.navigator.standalone===true||matchMedia("(display-mode: standalone)").matches;
 function set(state){box.dataset.state=state;btn.disabled=state==="on"||state==="busy";
  btn.querySelector(".lbl").textContent=state==="on"?"✅ You're subscribed — see you tomorrow!":state==="busy"?"⏳ One moment…":state==="blocked"?"🔕 Notifications are blocked in settings":"🔔 Get daily good news";}
 set("off");
 if(iOS&&!standalone){hint.hidden=false;btn.onclick=function(){hint.classList.remove("pulse");void hint.offsetWidth;hint.classList.add("pulse")};return;}
 window.OneSignalDeferred=window.OneSignalDeferred||[];
 OneSignalDeferred.push(async function(OneSignal){
  await OneSignal.init({appId:"ceb85e1d-3dcc-4b8f-b7a4-c2d8a4021242",
   serviceWorkerPath:"good-news-daily/OneSignalSDKWorker.js",
   serviceWorkerParam:{scope:"/good-news-daily/"},
   allowLocalhostAsSecureOrigin:true});
  function sync(){var s=OneSignal.User.PushSubscription.optedIn;
   if(s)set("on");else if(OneSignal.Notifications.permissionNative==="denied")set("blocked");else set("off");}
  sync();OneSignal.User.PushSubscription.addEventListener("change",sync);
  btn.onclick=async function(){set("busy");
   try{if(!OneSignal.Notifications.permission)await OneSignal.Notifications.requestPermission();
    await OneSignal.User.PushSubscription.optIn();}catch(e){console.warn(e)}sync();};
 });
 if(!("Notification" in window)&&!iOS){btn.disabled=true;btn.querySelector(".lbl").textContent="🔕 Not supported in this browser";}
})();
