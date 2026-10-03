(() => {
  const btn=document.getElementById('begin-check'), form=document.getElementById('attendance-form'), message=document.getElementById('verify-message');
  const rows=['lecture','time','class','location','face','duplicate'].map(x=>document.getElementById('check-'+x));
  const set=(i,state,label)=>{rows[i].className='check-row '+state;rows[i].querySelector('small').textContent=label;};
  const fail=(i,reason)=>{set(i,'failed','Failed');message.textContent=reason;message.className='hint camera-error';btn.disabled=false;btn.textContent='Try again';};
  btn.addEventListener('click',async()=>{
    btn.disabled=true;btn.textContent='Checking…';message.textContent='Checking lecture and time window…';
    // A post to the server performs authoritative checks; client-side progress is only for feedback.
    for(let i=0;i<3;i++)set(i,'passed','Passed');
    message.textContent='Requesting your campus location…';
    if(!navigator.geolocation){fail(3,'This browser does not provide location services.');return;}
    let pos;try{pos=await new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,timeout:12000,maximumAge:0}));}
    catch(e){fail(3,e.code===1?'Location permission denied. Allow location access and retry.':'GPS unavailable. Check device location settings and retry.');return;}
    form.elements.latitude.value=pos.coords.latitude;form.elements.longitude.value=pos.coords.longitude;set(3,'passed','Location received');
    message.textContent='Starting camera for face verification…';
    let stream;try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});}
    catch(e){fail(4,e.name==='NotAllowedError'?'Camera permission denied. Allow camera access and retry.':'Camera unavailable. Use localhost or HTTPS in a recent browser.');return;}
    const video=document.getElementById('verify-camera'),canvas=document.getElementById('verify-canvas');video.srcObject=stream;video.hidden=false;
    await new Promise(resolve=>video.onloadedmetadata=resolve);await new Promise(resolve=>setTimeout(resolve,350));canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);form.elements.face_data.value=canvas.toDataURL('image/jpeg',.88);stream.getTracks().forEach(t=>t.stop());video.hidden=true;set(4,'passed','Captured');set(5,'passed','Checking on server');
    message.textContent='Submitting verification securely…';form.submit();
  });
})();
