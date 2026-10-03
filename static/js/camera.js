(() => {
  const video=document.getElementById('camera'), canvas=document.getElementById('capture');
  const error=document.getElementById('camera-error'), placeholder=document.getElementById('placeholder');
  const start=document.getElementById('start-camera'), capture=document.getElementById('capture-face');
  const save=document.getElementById('save-face'), data=document.getElementById('face-data'), status=document.getElementById('capture-status');
  let stream;
  start.addEventListener('click',async()=>{
    try { stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false}); video.srcObject=stream; video.hidden=false; placeholder.hidden=true; capture.disabled=false; error.textContent=''; start.textContent='Camera enabled'; }
    catch(e){ error.textContent=e.name==='NotAllowedError'?'Camera permission denied. Allow camera access in your browser settings and retry.':'Camera is unavailable. Use a recent browser on localhost or HTTPS.'; }
  });
  capture.addEventListener('click',()=>{
    if(!video.videoWidth){error.textContent='Camera is still starting. Please try again.';return;}
    canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);
    data.value=canvas.toDataURL('image/jpeg',.88);save.disabled=false;status.textContent='Image captured. Review the preview, then save your face profile.';error.textContent='';
    placeholder.hidden=false;placeholder.textContent='✓';placeholder.querySelector('small').textContent='Face captured and ready to save';
  });
  document.getElementById('face-form').addEventListener('submit',()=>{if(stream)stream.getTracks().forEach(t=>t.stop());save.disabled=true;save.textContent='Saving…';});
})();
