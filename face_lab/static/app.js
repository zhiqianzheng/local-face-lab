'use strict';
const $=id=>document.getElementById(id);
const commonLabels=['愤怒样表情','厌恶样表情','恐惧样表情','开心样表情','中性表情','悲伤样表情','惊讶样表情','轻蔑样表情'];
const auNames={1:'内眉上提',2:'外眉上提',4:'眉毛下压',5:'上眼睑上提',6:'脸颊上提',7:'眼睑收紧',9:'皱鼻',10:'上唇上提',12:'嘴角上提',14:'嘴角收紧',15:'嘴角下拉',17:'下巴上提',20:'嘴唇横向拉伸',23:'嘴唇收紧',24:'嘴唇压紧',25:'双唇分开',26:'下颌下落'};
const intensityIDs=[1,2,4,5,6,9,12,15,17,20,25,26],presenceIDs=[1,2,4,6,7,10,12,14,15,17,23,24];
$('expressionBars').innerHTML=commonLabels.map((s,i)=>`<div class="expression-row"><div class="row"><span>${s}</span><span class="scores"><span class="mint" id="bv${i}">—</span><span class="blue" id="ev${i}">—</span></span></div><div class="bar"><div class="fill" id="bb${i}"></div></div><div class="bar"><div class="fill new" id="eb${i}"></div></div></div>`).join('');
$('auBars').innerHTML=intensityIDs.map(id=>`<div><div class="row"><span>AU${id} ${auNames[id]}</span><span id="av${id}">—</span></div><div class="bar"><div class="fill" id="ab${id}"></div></div></div>`).join('');
$('presence').innerHTML=presenceIDs.map(id=>`<span class="chip" id="ap${id}">AU${id} ${auNames[id]} · —</span>`).join('');
$('trendAU').innerHTML=intensityIDs.map(id=>`<option value="${id}" ${id===12?'selected':''}>AU${id} ${auNames[id]}</option>`).join('');
let stream=null,active=false,recorder=null,rows=[],began=0,timer=null,recordTimer=null,saving=false,generation=0,history=[];
const input=document.createElement('canvas');input.width=640;
function clearPredictions(text='等待画面'){
 $('baseLabel').textContent=text;$('emotiLabel').textContent=$('mode').value==='baseline'?'未启用':text;$('baseTime').textContent='';$('emotiTime').textContent='';
 commonLabels.forEach((_,i)=>{for(const p of ['b','e']){$(p+'v'+i).textContent='—';$(p+'b'+i).style.width='0%'}});
 intensityIDs.forEach(id=>{$('av'+id).textContent='—';$('ab'+id).style.width='0%'});
 presenceIDs.forEach(id=>{$('ap'+id).className='chip';$('ap'+id).textContent=`AU${id} ${auNames[id]} · —`});
 const c=$('overlay');c.getContext('2d').clearRect(0,0,c.width,c.height);
 $('auStatus').textContent=$('mode').value==='detail'?'等待有效的面部关键点':'当前模式未启用 AU 分析';
}
function updateModels(d){
 for(const [key,prefix,labelID,timeID] of [['baseline','b','baseLabel','baseTime'],['emotieff','e','emotiLabel','emotiTime']]){
  const m=d.models[key];if(!m)continue;$(labelID).textContent=m.label;$(timeID).textContent=`处理 ${m.ms.toFixed(1)} ms`;
  commonLabels.forEach((label,i)=>{const idx=m.labels.indexOf(label);if(idx>=0){const s=m.scores[idx];$(prefix+'v'+i).textContent=(s*100).toFixed(1)+'%';$(prefix+'b'+i).style.width=s*100+'%'}});
 }
 if(d.au){$('auStatus').textContent=`强度为模型估计，0 表示弱、5 表示强 · 关键点与 AU 处理 ${d.au.ms.toFixed(1)} ms`;
  intensityIDs.forEach(id=>{const v=d.au.intensity[id];$('av'+id).textContent=v.toFixed(2);$('ab'+id).style.width=v/5*100+'%'});
  presenceIDs.forEach(id=>{const v=d.au.presence[id];$('ap'+id).className='chip'+(v?' on':'');$('ap'+id).textContent=`AU${id} ${auNames[id]} · ${v?'出现':'未出现'}`});
 }else if(d.au_error){$('auStatus').textContent=d.au_error;}
}
function drawTrend(){
 const c=$('trend'),ctx=c.getContext('2d'),w=c.width,h=c.height,l=42,r=w-18,top=20,b=h-35;ctx.clearRect(0,0,w,h);ctx.font='16px system-ui';
 for(let v=0;v<=5;v++){const y=b-v/5*(b-top);ctx.strokeStyle='#2c3b50';ctx.beginPath();ctx.moveTo(l,y);ctx.lineTo(r,y);ctx.stroke();ctx.fillStyle='#9babbd';ctx.fillText(String(v),15,y+5)}
 ctx.fillStyle='#9babbd';ctx.fillText('−30 秒',l,h-10);ctx.fillText('现在',r-35,h-10);
 if(!history.length)return;const end=history[history.length-1].t,begin=end-30000,id=$('trendAU').value;ctx.strokeStyle='#69dbc2';ctx.lineWidth=3;ctx.beginPath();let pen=false;
 for(const point of history){if(point.t<begin)continue;const v=point.values?.[id];if(v==null){pen=false;continue}const x=l+(point.t-begin)/30000*(r-l),y=b-v/5*(b-top);if(pen)ctx.lineTo(x,y);else ctx.moveTo(x,y);pen=true}ctx.stroke();
}
async function loop(gen){
 if(!active||gen!==generation)return;const started=performance.now(),mode=$('mode').value;
 try{
  const v=$('video');if(v.readyState<2)return;input.height=Math.round(640*v.videoHeight/v.videoWidth);input.getContext('2d').drawImage(v,0,0,input.width,input.height);
  const blob=await new Promise(r=>input.toBlob(r,'image/jpeg',.85));const f=new FormData();f.append('frame',blob,'frame.jpg');f.append('mode',mode);
  const res=await fetch('/analyze',{method:'POST',body:f});const d=await res.json();if(!res.ok)throw Error(d.error||'服务器处理失败');if(!active||gen!==generation||mode!==$('mode').value)return;
  clearPredictions(d.face?'等待预测':'未检测到人脸');if(d.face){updateModels(d);const c=$('overlay');c.width=d.width;c.height=d.height;const ctx=c.getContext('2d');ctx.strokeStyle='#69dbc2';ctx.lineWidth=3;const [x,y,w,h]=d.box;ctx.strokeRect(d.width-x-w,y,w,h)}
  $('timing').textContent=`本机处理 ${d.total_ms.toFixed(1)} ms · 往返 ${Math.round(performance.now()-started)} ms · ${d.count} 张人脸`;
  const now=performance.now();history.push({t:now,values:d.au?.intensity||null});history=history.filter(p=>p.t>=now-31000);drawTrend();
  if(recorder?.state==='recording'&&started>=began){rows.push({seconds:+((started-began)/1000).toFixed(3),...d});$('status').textContent=`正在录制 ${((now-began)/1000).toFixed(1)} / 60 秒 · ${rows.length} 条采样`;}
 }catch(e){if(gen===generation)$('status').textContent='分析失败：'+e.message;}
 finally{if(active&&gen===generation)timer=setTimeout(()=>loop(gen),150)}
}
$('start').onclick=async()=>{
 $('start').disabled=true;try{stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480}},audio:false});$('video').srcObject=stream;await $('video').play();active=true;generation++;history=[];drawTrend();$('record').disabled=saving;$('stop').disabled=false;$('status').textContent='实时分析中，尚未录制。';loop(generation)}
 catch(e){stream?.getTracks().forEach(t=>t.stop());$('start').disabled=false;$('status').textContent='摄像头开启失败：'+e.message+'。请检查浏览器权限或设备占用。'}
};
function finish(){clearTimeout(recordTimer);if(recorder?.state==='recording'){recorder.stop();$('stopRecord').disabled=true;}}
$('record').onclick=()=>{
 if(!stream||saving)return;try{
  const type=['video/webm;codecs=vp8','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));const current=new MediaRecorder(stream,type?{mimeType:type}:{});recorder=current;const chunks=[];rows=[];
  current.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
  current.onstop=async()=>{
   saving=true;$('record').disabled=true;$('mode').disabled=true;$('status').textContent='正在保存视频和分析时间线…';const captured=rows.slice(),blob=new Blob(chunks,{type:current.mimeType});
   try{const f=new FormData();f.append('video',blob,'video.webm');f.append('metrics',JSON.stringify(captured));const res=await fetch('/save',{method:'POST',body:f});const d=await res.json();if(!res.ok)throw Error(d.error||'保存失败');$('saved').textContent=`已保存 ${d.samples} 条采样：\n${d.path}`;const links=document.createElement('p');for(const [file,text] of [['video.webm','回看录像'],['predictions.csv','CSV 时间线'],['analysis.json','完整 JSON']]){const a=document.createElement('a');a.href='/recordings/'+d.session+'/'+file;a.textContent=text;a.target='_blank';links.append(a)}$('saved').append(links);$('status').textContent=active?'保存完成，实时分析继续。':'摄像头已关闭，录像已保存。'}
   catch(e){$('status').textContent='保存失败：'+e.message+'，请下载录像备份。';$('saved').replaceChildren();for(const [data,name,text] of [[blob,'video.webm','录像备份'],[new Blob([JSON.stringify(captured)],{type:'application/json'}),'analysis-backup.json','数据备份']]){const a=document.createElement('a');a.href=URL.createObjectURL(data);a.download=name;a.textContent=text;$('saved').append(a)}}
   finally{saving=false;$('record').disabled=!active;$('mode').disabled=false;}
  };
  began=performance.now();current.start(1000);$('record').disabled=true;$('stopRecord').disabled=false;$('mode').disabled=true;$('status').textContent='正在录制…';recordTimer=setTimeout(()=>{if(recorder===current)finish()},60000);
 }catch(e){$('status').textContent='录制失败：'+e.message;}
};
$('stopRecord').onclick=finish;
$('stop').onclick=()=>{finish();active=false;generation++;clearTimeout(timer);stream?.getTracks().forEach(t=>t.stop());$('video').srcObject=null;clearPredictions('摄像头已关闭');history=[];drawTrend();$('start').disabled=false;$('record').disabled=true;$('stop').disabled=true;$('status').textContent='摄像头已关闭。';};
$('mode').onchange=()=>{clearPredictions();history=[];drawTrend()};$('trendAU').onchange=drawTrend;
window.addEventListener('beforeunload',()=>stream?.getTracks().forEach(t=>t.stop()));
clearPredictions();drawTrend();
