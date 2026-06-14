// ══════════════════════════════════════════════════════════════════
// THREE.JS — 3D LOGO (shared between loader and welcome screen)
// ══════════════════════════════════════════════════════════════════
function buildLogo3D(canvas, size, autoRotateSpeed) {
  if (!canvas || typeof THREE === 'undefined') return null;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(size, size);
  renderer.setClearColor(0x000000, 0);

  const scene  = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 50);
  camera.position.set(0, 0, 7.5);

  const group = new THREE.Group();

  // Colors
  const C_BLUE  = 0x3b82f6;
  const C_CYAN  = 0x06b6d4;
  const C_WHITE = 0xffffff;

  // Helper: line between two Vector3s
  function mkLine(a, b, color, opacity) {
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const m = new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false });
    return new THREE.Line(g, m);
  }

  // Hex vertices (flat-top hex, radius = 2.2)
  const R = 2.2;
  const hexV = [];
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 + Math.PI / 6;
    hexV.push(new THREE.Vector3(Math.cos(a) * R, Math.sin(a) * R, 0));
  }

  // Hex outline
  const hexPts = [...hexV, hexV[0]];
  const hexGeo = new THREE.BufferGeometry().setFromPoints(hexPts);
  group.add(new THREE.Line(hexGeo, new THREE.LineBasicMaterial({ color: C_BLUE, transparent: true, opacity: 0.75 })));

  // Inner ring
  const ringPts = [];
  for (let i = 0; i <= 80; i++) {
    const a = (i / 80) * Math.PI * 2;
    ringPts.push(new THREE.Vector3(Math.cos(a) * 1.4, Math.sin(a) * 1.4, 0));
  }
  const ringGeo = new THREE.BufferGeometry().setFromPoints(ringPts);
  group.add(new THREE.Line(ringGeo, new THREE.LineBasicMaterial({ color: C_BLUE, transparent: true, opacity: 0.28 })));

  // Spokes from hex vertex to center
  hexV.forEach(v => group.add(mkLine(new THREE.Vector3(0, 0, 0), v, C_BLUE, 0.22)));

  // Vertex spheres — alternating blue/cyan
  const vGeo = new THREE.SphereGeometry(0.09, 8, 8);
  hexV.forEach((v, i) => {
    const m = new THREE.MeshBasicMaterial({ color: i % 2 === 0 ? C_BLUE : C_CYAN });
    const mesh = new THREE.Mesh(vGeo, m);
    mesh.position.copy(v);
    group.add(mesh);
  });

  // Central sphere (blue)
  const cGeo = new THREE.SphereGeometry(0.42, 20, 20);
  group.add(new THREE.Mesh(cGeo, new THREE.MeshBasicMaterial({ color: C_BLUE })));

  // Center dot (white)
  const dGeo = new THREE.SphereGeometry(0.18, 12, 12);
  group.add(new THREE.Mesh(dGeo, new THREE.MeshBasicMaterial({ color: C_WHITE })));

  scene.add(group);

  const clock = new THREE.Clock();
  let raf;
  let hovered = false;
  let currentSpeed = autoRotateSpeed;

  // Hover listeners
  canvas.addEventListener('mouseenter', () => { hovered = true; });
  canvas.addEventListener('mouseleave', () => { hovered = false; });

  function loop() {
    raf = requestAnimationFrame(loop);
    const t = clock.getElapsedTime();

    // Smoothly lerp speed: hover = 1.2x, normal = 1x
    const wantSpeed = hovered ? autoRotateSpeed * 1.2 : autoRotateSpeed;
    currentSpeed += (wantSpeed - currentSpeed) * 0.05;

    group.rotation.y = t * currentSpeed;
    group.rotation.x = Math.sin(t * (currentSpeed * 0.45)) * 0.45;
    group.rotation.z = Math.cos(t * (currentSpeed * 0.3)) * 0.12;

    renderer.render(scene, camera);
  }
  loop();

  return {
    stop: () => { cancelAnimationFrame(raf); renderer.dispose(); },
    setColors: (isLight) => {
      // Colors adapt to theme (logo is always blue so no major change needed)
    }
  };
}

// Start loader 3D logo immediately
let loaderLogoInst = null;
document.addEventListener('DOMContentLoaded', () => {
  loaderLogoInst = buildLogo3D(document.getElementById('loader-canvas'), 120, 1.1);
  // Mobile block logo
  const mc = document.getElementById('mobile-canvas');
  if (mc) buildLogo3D(mc, 100, 0.8);
});

// Hide loader and show app
function hideLoader() {
  const loader = document.getElementById('loader');
  const app    = document.getElementById('app');
  loader.classList.add('hide');
  app.classList.add('ready');
  // Start the welcome 3D logo
  setTimeout(() => {
    const wlCanvas = document.getElementById('logo-canvas');
    if (wlCanvas) buildLogo3D(wlCanvas, 160, 0.72);
  }, 200);
}

// ══════════════════════════════════════════════════════════════════
// THEME TOGGLE
// ══════════════════════════════════════════════════════════════════
function toggleTheme() {
  const cur  = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('a2-theme', next);
  window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
}

// ══════════════════════════════════════════════════════════════════
// WATERMARK SVG (for terminal backdrop)
// ══════════════════════════════════════════════════════════════════
const WATERMARK_SVG = `<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <polygon points="50,8 80,24 80,57 50,73 20,57 20,24"
    stroke="white" stroke-width="1.2" fill="rgba(255,255,255,0.06)" stroke-linejoin="round"/>
  <circle cx="50" cy="8" r="3" fill="white" opacity=".6"/>
  <circle cx="80" cy="24" r="2.5" fill="white" opacity=".5"/>
  <circle cx="80" cy="57" r="2.5" fill="white" opacity=".5"/>
  <circle cx="50" cy="73" r="3" fill="white" opacity=".6"/>
  <circle cx="20" cy="57" r="2.5" fill="white" opacity=".5"/>
  <circle cx="20" cy="24" r="2.5" fill="white" opacity=".5"/>
  <line x1="50" y1="14" x2="50" y2="8" stroke="white" stroke-width=".8" opacity=".4"/>
  <line x1="50" y1="40" x2="80" y2="24" stroke="white" stroke-width=".8" opacity=".3"/>
  <line x1="50" y1="40" x2="80" y2="57" stroke="white" stroke-width=".8" opacity=".3"/>
  <line x1="50" y1="40" x2="50" y2="73" stroke="white" stroke-width=".8" opacity=".3"/>
  <line x1="50" y1="40" x2="20" y2="57" stroke="white" stroke-width=".8" opacity=".3"/>
  <line x1="50" y1="40" x2="20" y2="24" stroke="white" stroke-width=".8" opacity=".3"/>
  <circle cx="50" cy="40" r="9" fill="white" opacity=".18"/>
  <circle cx="50" cy="40" r="4" fill="white" opacity=".7"/>
  <circle cx="50" cy="40" r="1.8" fill="white" opacity=".9"/>
</svg>`;

// ══════════════════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════════════════
const S = {
  chatId:null, chats:[], busy:false, tokens:{},
  os:'...', shell:'...', models:{}, modes:{},
  curModel:'', curMode:'',
  activeTermId:null, terms:{},
  attachments:[],
  editingMsgId:null
};
let termCounter = 0;

// ══════════════════════════════════════════════════════════════════
// SOCKET
// ══════════════════════════════════════════════════════════════════
const socket = io();

socket.on('connect', () => {
  setStatus('ready','Ready');
  badge('ws-badge',true,'WS');
  document.getElementById('sbtn').disabled = false;
  loadChats();
  hideLoader(); // reveal app once connected
});
socket.on('disconnect', () => { setStatus('idle','Disconnected'); badge('ws-badge',false,'WS'); });
socket.on('connected', d => {
  S.os=d.os||'?'; S.shell=d.shell||'?';
  S.models=d.models||{}; S.modes=d.modes||{};
  S.curModel=d.default_model; S.curMode=d.default_mode;
  document.getElementById('shell-badge').textContent = S.shell;
  buildSelectors();
  setWelcomeChips();
});
socket.on('toast', d => toast(d.msg, d.type||'info'));
socket.on('keys_updated', () => { if(isModOpen('settings')) loadKeys(); });
socket.on('key_usage_update', d => {
  if(isModOpen('settings')) loadKeys();
  const el=document.createElement('div');
  el.style.cssText='position:fixed;bottom:18px;left:50%;transform:translateX(-50%);font-size:10px;font-family:var(--mn);color:var(--tx3);background:var(--bg3);border:1px solid var(--bd2);padding:3px 12px;border-radius:12px;z-index:150;pointer-events:none;animation:rowIn .2s ease';
  el.textContent=`Key #${d.label}: +${d.tokens.toLocaleString()} tokens`;
  document.body.appendChild(el); setTimeout(()=>el.remove(),2500);
});
socket.on('chat_titled', d => {
  const el=document.querySelector(`.ci[data-id="${d.chat_id}"]`);
  if(el) el.querySelector('.ci-ttl').textContent=d.title;
  if(d.chat_id===S.chatId) document.getElementById('tb-title').textContent=d.title;
  const c=S.chats.find(x=>x.id===d.chat_id); if(c) c.title=d.title;
});
socket.on('token_update', d => {
  S.tokens[d.chat_id]=(S.tokens[d.chat_id]||0)+d.tokens;
  if(d.chat_id===S.chatId){
    updateCtx(S.tokens[d.chat_id]);
    document.getElementById('tb-tok').textContent=S.tokens[d.chat_id].toLocaleString()+' tokens';
  }
});
socket.on('terminal_start', d => {
  termWrite(d.term_id,`\n\x1b[1;33m[${d.shell}] > ${d.command}\x1b[0m`);
  termWrite(d.term_id,'\x1b[2m'+'─'.repeat(46)+'\x1b[0m');
  badge('ag-badge',true,'Running');
});
socket.on('terminal_line', d => termWrite(d.term_id,'  '+d.data));
socket.on('terminal_done', d => {
  termWrite(d.term_id,'\x1b[2m'+'─'.repeat(46)+'\x1b[0m');
  termWrite(d.term_id,d.returncode===0?'\x1b[1;32m  [+] exit 0\x1b[0m':`\x1b[1;31m  [-] exit ${d.returncode}\x1b[0m`);
  termWrite(d.term_id,'');
  badge('ag-badge',false,'Idle');
});
socket.on('proc_started', d => {
  setTermRunning(d.term_id,true);
  document.getElementById('kill-btn').classList.add('show');
});
socket.on('proc_ended', d => {
  setTermRunning(d.term_id,false);
  document.getElementById('kill-btn').classList.remove('show');
});
socket.on('chat_tool_call', d => appendToolCall(d.description,d.command,d.shell||S.shell));
socket.on('chat_response', d => { removeTyping(); if(d.text)appendAI(d.text); if(d.done){setBusy(false);setStatus('ready','Ready');} });
socket.on('agent_stopped', () => { removeTyping(); setBusy(false); setStatus('ready','Ready'); });
socket.on('messages_truncated', async d => {
  if(d.chat_id===S.chatId){
    const res=await fetch(`/api/chats/${d.chat_id}`);
    const data=await res.json();
    renderMsgs(data.messages||[]);
    showTyping(); setBusy(true);
  }
});

// Fallback: show app after 3s even if socket hasn't connected
setTimeout(hideLoader, 3000);

// ══════════════════════════════════════════════════════════════════
// SELECTORS
// ══════════════════════════════════════════════════════════════════
function buildSelectors(){
  const msel=document.getElementById('model-sel'), mosel=document.getElementById('mode-sel');
  msel.innerHTML='';
  const groups={};
  for(const[k,m] of Object.entries(S.models)){const g=m.group||'other';if(!groups[g])groups[g]=[];groups[g].push({k,m});}
  for(const[g,items] of Object.entries(groups)){
    const og=document.createElement('optgroup'); og.label='Gemini '+g;
    for(const{k,m} of items){const o=document.createElement('option');o.value=k;o.textContent=m.label;if(k===S.curModel)o.selected=true;og.appendChild(o);}
    msel.appendChild(og);
  }
  mosel.innerHTML='';
  for(const[k,m] of Object.entries(S.modes)){const o=document.createElement('option');o.value=k;o.textContent=`${m.icon} ${m.label}`;if(k===S.curMode)o.selected=true;mosel.appendChild(o);}
}
function onModelChange(v){ S.curModel=v; }
function onModeChange(v){ S.curMode=v; }

// ══════════════════════════════════════════════════════════════════
// WELCOME CHIPS
// ══════════════════════════════════════════════════════════════════
function setWelcomeChips(){
  const isWin=S.os==='Windows';
  const chips=isWin?['portscan 10.10.1.253','show network interfaces','what is HTML?','dir C:\\','check open ports on localhost','system info']:['portscan 10.10.1.253','show network interfaces','what is a SYN flood?','ls -la ~','enumerate localhost ports','check public IP'];
  const el=document.getElementById('wl-chips');
  if(el) el.innerHTML=chips.map(c=>`<div class="wl-chip" onclick="se(${JSON.stringify(c)})">${c}</div>`).join('');
}

// ══════════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════════
const msgsEl = () => document.getElementById('msgs');
const hideWel = () => { const w=document.getElementById('welcome'); if(w)w.style.display='none'; };
const scrollB = () => { const m=msgsEl(); m.scrollTop=m.scrollHeight; };
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const ts  = () => new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
const rel = d => { const diff=(Date.now()-new Date(d+'Z'))/1000; if(diff<60)return 'now'; if(diff<3600)return Math.floor(diff/60)+'m'; if(diff<86400)return Math.floor(diff/3600)+'h'; return Math.floor(diff/86400)+'d'; };

function setStatus(st,tx){ const d=document.getElementById('sdot'); d.className='sdot'; if(st==='ready')d.classList.add('ready'); else if(st==='busy')d.classList.add('busy'); document.getElementById('stxt').textContent=tx; }
function badge(id,on,label){ const b=document.getElementById(id); if(!b)return; b.className='cbadge'+(on?' on':''); b.querySelector('span').textContent=label; }
function setBusy(v){
  S.busy=v;
  document.getElementById('sbtn').style.display=v?'none':'flex';
  document.getElementById('stop-btn').style.display=v?'flex':'none';
  document.getElementById('sbtn').disabled=v;
  document.getElementById('ci').disabled=v;
  if(v){setStatus('busy','Thinking…');badge('ag-badge',true,'Running');}
  else badge('ag-badge',false,'Idle');
}
function toast(msg,type='info'){
  const el=document.createElement('div');
  el.className='toast '+({info:'ti',warning:'tw',success:'tsg',error:'te'}[type]||'ti');
  el.textContent=msg; document.body.appendChild(el); setTimeout(()=>el.remove(),4000);
}
function updateCtx(tok){
  const lim=128000,pct=Math.min(100,Math.round(tok/lim*100)),c=69.1;
  const arc=document.getElementById('ctx-arc');
  arc.style.strokeDashoffset=c-(c*pct/100);
  arc.style.stroke=pct>80?'var(--rd)':pct>50?'var(--yw)':'var(--ac)';
  document.getElementById('ctx-pct').textContent=pct+'%';
  document.getElementById('ctx-tok').textContent=(tok||0).toLocaleString();
  const rem=Math.max(0,lim-tok);
  document.getElementById('ctx-rem').textContent=rem>1000?Math.round(rem/1000)+'k':rem;
}
function isModOpen(n){ return document.getElementById('mod-'+n).classList.contains('show'); }

// ══════════════════════════════════════════════════════════════════
// FILE ATTACHMENTS
// ══════════════════════════════════════════════════════════════════
async function handleFiles(inp){
  for(const f of inp.files){
    const b64=await new Promise((res,rej)=>{ const r=new FileReader(); r.onload=()=>res(r.result.split(',')[1]); r.onerror=rej; r.readAsDataURL(f); });
    S.attachments.push({name:f.name,mime_type:f.type||'text/plain',data:b64});
  }
  renderAttPrev(); inp.value='';
}
function renderAttPrev(){
  const el=document.getElementById('att-preview');
  if(!S.attachments.length){el.innerHTML='';return;}
  el.innerHTML=S.attachments.map((a,i)=>`<div class="att-prev-item"><svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10"><path d="M4.5 3a2.5 2.5 0 015 0v9a1.5 1.5 0 01-3 0V5a.5.5 0 011 0v7a.5.5 0 001 0V3a1.5 1.5 0 00-3 0v9a2.5 2.5 0 005 0V5a.5.5 0 011 0v7a3.5 3.5 0 01-7 0z"/></svg>${esc(a.name)}<span class="remove" onclick="removeAtt(${i})">×</span></div>`).join('');
}
function removeAtt(i){ S.attachments.splice(i,1); renderAttPrev(); }

// ══════════════════════════════════════════════════════════════════
// CHAT MANAGEMENT
// ══════════════════════════════════════════════════════════════════
async function loadChats(){
  const res=await fetch('/api/chats'); S.chats=await res.json();
  renderList(S.chats);
  if(!S.chats.length) await newChat();
  else if(!S.chatId) await switchChat(S.chats[0].id);
  if(Object.keys(S.terms).length===0) addTerm();
}
function renderList(chats){
  const el=document.getElementById('clist');
  if(!chats.length){el.innerHTML='<div class="empty-sb">No chats.<br>Click <strong>+ New</strong> to start.</div>';return;}
  const today=new Date(); today.setHours(0,0,0,0);
  const yest=new Date(today); yest.setDate(yest.getDate()-1);
  const g={Today:[],Yesterday:[],Older:[]};
  for(const c of chats){const d=new Date(c.updated_at+'Z');d.setHours(0,0,0,0);if(d>=today)g.Today.push(c);else if(d>=yest)g.Yesterday.push(c);else g.Older.push(c);}
  let h='';
  for(const[lbl,items] of Object.entries(g)){
    if(!items.length)continue;
    h+=`<div class="cg">${lbl}</div>`;
    for(const c of items){
      const a=c.id===S.chatId?' active':'';
      const ml=S.models[c.model]?.label||c.model||'';
      h+=`<div class="ci${a}" data-id="${c.id}" onclick="switchChat('${c.id}')"><span class="ci-ico">💬</span><div class="ci-b"><div class="ci-ttl">${esc(c.title)}</div><div class="ci-meta"><span class="ci-time">${rel(c.updated_at)}</span>${ml?`<span class="ci-model">${esc(ml)}</span>`:''}</div></div><button class="ci-del" onclick="delChat(event,'${c.id}')">×</button></div>`;
    }
  }
  el.innerHTML=h;
}
function filterChats(q){ renderList(S.chats.filter(c=>c.title.toLowerCase().includes(q.toLowerCase()))); }
async function newChat(){
  // Clear immediately — a new chat is always empty
  msgsEl().innerHTML='';
  document.getElementById('tb-title').textContent='New Chat';
  const res=await fetch('/api/chats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:S.curModel,mode:S.curMode})});
  const chat=await res.json();
  S.chats.unshift(chat); renderList(S.chats); await switchChat(chat.id);
}
async function switchChat(id){
  S.chatId=id; S.busy=false;
  document.getElementById('sbtn').disabled=false;
  document.getElementById('ci').disabled=false;
  setStatus('ready','Ready');
  renderList(S.chats);
  const chat=S.chats.find(c=>c.id===id);
  document.getElementById('tb-title').textContent=chat?chat.title:'Chat';
  if(chat?.model&&S.models[chat.model]){S.curModel=chat.model;document.getElementById('model-sel').value=chat.model;}
  if(chat?.mode&&S.modes[chat.mode]){S.curMode=chat.mode;document.getElementById('mode-sel').value=chat.mode;}
  const tok=S.tokens[id]||0; updateCtx(tok);
  document.getElementById('tb-tok').textContent=tok.toLocaleString()+' tokens';
  const res=await fetch(`/api/chats/${id}`);
  const data=await res.json();
  // Stale-ID guard: if user clicked another chat while this was loading, discard
  if(S.chatId!==id) return;
  renderMsgs(data.messages||[]);
}
async function delChat(e,id){
  e.stopPropagation();
  await fetch(`/api/chats/${id}`,{method:'DELETE'});
  S.chats=S.chats.filter(c=>c.id!==id); renderList(S.chats);
  if(S.chatId===id){S.chatId=null;S.chats.length?await switchChat(S.chats[0].id):await newChat();}
}
function startRename(){
  const el=document.getElementById('tb-title'),cur=el.textContent;
  el.innerHTML=`<input class="ri" value="${esc(cur)}" onblur="finishRename(this)" onkeydown="if(event.key==='Enter')this.blur()">`;
  el.querySelector('input').focus();
}
async function finishRename(inp){
  const title=inp.value.trim()||'New Chat';
  document.getElementById('tb-title').textContent=title;
  if(S.chatId){
    await fetch(`/api/chats/${S.chatId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title})});
    const item=document.querySelector(`.ci[data-id="${S.chatId}"]`);if(item)item.querySelector('.ci-ttl').textContent=title;
    const c=S.chats.find(x=>x.id===S.chatId);if(c)c.title=title;
  }
}

// ══════════════════════════════════════════════════════════════════
// MESSAGES
// ══════════════════════════════════════════════════════════════════
function renderMsgs(msgs){
  const el=msgsEl(); el.innerHTML='';
  if(!msgs.length){showWelcome();return;}
  for(const m of msgs){
    if(m.role==='user') _user(m.content,JSON.parse(m.meta||'{}'),m.id);
    else if(m.role==='assistant') _ai(m.content);
    else if(m.role==='tool_call'){const meta=JSON.parse(m.meta||'{}');_tool(m.content,meta.cmd||'',S.shell);}
  }
  scrollB();
}
function showWelcome(){
  msgsEl().innerHTML=`<div id="welcome" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:10px;text-align:center;padding:30px 20px">
    <canvas id="logo-canvas" width="160" height="160" style="display:block;width:160px;height:160px;filter:drop-shadow(0 0 16px rgba(59,130,246,.22))"></canvas>
    <div class="wl-title">Agent 2</div>
    <div class="wl-sub">Commands run in <strong style="color:var(--yw)">${S.shell}</strong> on <strong style="color:var(--cy)">${S.os}</strong>.</div>
    <div class="wl-chips" id="wl-chips"></div>
  </div>`;
  setWelcomeChips();
  setTimeout(()=>{ buildLogo3D(document.getElementById('logo-canvas'), 160, 0.72); },80);
}

let _ti=0;
function _user(text,meta,msgId){
  hideWel();
  const atts=(meta?.attachments||[]);
  const attHtml=atts.length?`<div class="att-chips">${atts.map(n=>`<span class="att-chip"><svg viewBox="0 0 16 16" fill="currentColor" width="10" height="10"><path d="M4.5 3a2.5 2.5 0 015 0v9a1.5 1.5 0 01-3 0V5a.5.5 0 011 0v7a.5.5 0 001 0V3a1.5 1.5 0 00-3 0v9a2.5 2.5 0 005 0V5a.5.5 0 011 0v7a3.5 3.5 0 01-7 0z"/></svg>${esc(n)}</span>`).join('')}</div>`:'';
  const editBtn=msgId?`<button class="msg-edit-btn" onclick="editMsg('${msgId}',${JSON.stringify(text)})" title="Edit"><svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor"><path d="M12.854.146a.5.5 0 00-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 000-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 016 13.5V13h-.5a.5.5 0 01-.5-.5V12h-.5a.5.5 0 01-.5-.5V11h-.5a.5.5 0 01-.5-.5V10h-.5a.499.499 0 01-.175-.032l-.179.178a.5.5 0 00-.11.168l-2 5a.5.5 0 00.65.65l5-2a.5.5 0 00.168-.11l.178-.178z"/></svg></button>`:'';
  const el=document.createElement('div');el.className='mrow mu';if(msgId)el.dataset.msgId=msgId;
  el.innerHTML=`<div class="mrow-head"><span class="mbadge mbu">USER</span><span class="mtime">${ts()}</span>${editBtn}</div><div class="utxt">${esc(text).replace(/\n/g,'<br>')}</div>${attHtml}`;
  msgsEl().appendChild(el); scrollB();
}
function _ai(md) {
  hideWel();
  const el = document.createElement('div');
  el.className = 'mrow ma';
  const ml = S.models[S.curModel]?.label || S.curModel;
  const mi = S.modes[S.curMode]?.icon || '';

  // Render Markdown
  const htmlContent = marked.parse(md);

  el.innerHTML = `
    <div class="mrow-head">
      <span class="mbadge mba">AGENT 2</span>
      <span class="mmodel">${mi} ${esc(ml)}</span>
      <span class="mtime">${ts()}</span>
    </div>
    <div class="mc">${htmlContent}</div>
    <div class="m-actions">
      <button class="m-btn" onclick="copyResponse(this)" title="Copy Response">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
      </button>
      <button class="m-btn" onclick="retryLast()" title="Regenerate">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
      </button>
    </div>`;

  msgsEl().appendChild(el);

  // 1. Handle Syntax Highlighting & Code Copy Buttons
  el.querySelectorAll('pre').forEach(pre => {
    // Add Copy Button
    const code = pre.querySelector('code');
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = 'Copy';
    // Inside _ai(md) function, for the code blocks:
    btn.onclick = async () => {
        await copyToClipboard(code.innerText);
        toast('Code copied', 'success');
        btn.style.color = 'var(--gr)';
        setTimeout(() => btn.style.color = '', 2000);
    };
    pre.appendChild(btn);
    
    // Highlight
    if (code) hljs.highlightElement(code);
  });

  scrollB();
}

// Universal Copy Helper (Works on IP/Insecure Contexts)
async function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
  } else {
    // Fallback for IP addresses/non-HTTPS
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    textArea.style.top = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
    } catch (err) {
      console.error('Fallback copy failed', err);
    }
    document.body.removeChild(textArea);
  }
}

// Updated copyResponse
async function copyResponse(btn) {
  const mc = btn.closest('.ma').querySelector('.mc');
  const text = mc.innerText;
  
  await copyToClipboard(text);
  
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `<span style="font-size:9px; color:var(--gr)">✓</span>`;
  setTimeout(() => btn.innerHTML = originalHtml, 2000);
  toast('Response copied', 'success');
}

// Regenerate the last AI response
async function retryLast() {
  if (S.busy || !S.chatId) return;

  // Find the last user message to resend
  const rows = document.querySelectorAll('.mrow.mu');
  if (!rows.length) return;
  
  const lastUserMsg = rows[rows.length - 1];
  const text = lastUserMsg.querySelector('.utxt').innerText;
  
  // Optional: Remove the last AI response from UI for a cleaner "retry" feel
  const aiRows = document.querySelectorAll('.mrow.ma');
  if (aiRows.length) aiRows[aiRows.length - 1].remove();

  showTyping();
  setBusy(true);
  
  // Re-emit the last message
  socket.emit('chat_message', {
    chat_id: S.chatId,
    message: text,
    term_id: S.activeTermId || 't1',
    model: S.curModel,
    mode: S.curMode,
    attachments: [] // You might want to track if the last msg had attachments
  });
  
  toast('Regenerating response...', 'info');
}

function _tool(desc,cmd,shell){
  hideWel();
  const id='tc'+_ti++;
  const el=document.createElement('div');el.className='mrow mt';
  el.innerHTML=`<div class="mrow-head"><span class="mbadge mbt">TOOL</span><span class="mshell">${shell}</span><span class="mtime">${ts()}</span></div>
    <div class="tblk"><div class="tblk-hd" onclick="togTool('${id}')">
      <div class="tblk-l"><span class="tarr" id="arr-${id}">&#9654;</span><span class="tfn">run_command</span><span class="tdesc">${esc(desc)}</span></div>
      <div style="display:flex;align-items:center;gap:5px"><span class="tshbg">${shell}</span><button class="tcopy" onclick="event.stopPropagation();cpCmd('${id}')">copy</button><button class="trun-btn" onclick="event.stopPropagation();runToolCmd('${id}')">▶ run</button></div>
    </div><div class="tbody" id="${id}"><div class="tlbl">Command</div><div class="tcmd" id="cmd-${id}">$ ${esc(cmd)}</div></div></div>`;
  msgsEl().appendChild(el); scrollB(); togTool(id);
}
function togTool(id){ const b=document.getElementById(id),a=document.getElementById('arr-'+id); if(!b)return; const o=b.classList.toggle('open'); if(a){a.innerHTML=o?'&#9660;':'&#9654;';a.classList.toggle('open',o);} }
function cpCmd(id){ const el=document.getElementById('cmd-'+id); if(el)navigator.clipboard.writeText(el.textContent.replace(/^\$ /,'')); toast('Copied','success'); }
function runToolCmd(id){
  const el=document.getElementById('cmd-'+id);
  if(!el) return;
  const cmd=el.textContent.replace(/^\$ /,'').trim();
  if(!cmd) return;
  const termId=S.activeTermId||Object.keys(S.terms)[0];
  if(!termId){ toast('No terminal open','warning'); return; }
  // Push to history
  const t=S.terms[termId];
  if(t){
    if(!t.history.length||t.history[0]!==cmd) t.history.unshift(cmd);
    if(t.history.length>100) t.history.pop();
    t.setHistIdx(-1);
  }
  socket.emit('run_raw_command',{command:cmd,term_id:termId});
  toast('Running in terminal…','success');
}
function showTyping(){ hideWel(); const el=document.createElement('div');el.id='typing';el.className='mrow ma';el.innerHTML=`<div class="mrow-head"><span class="mbadge mbr">REASONING</span></div><div class="typing"><span></span><span></span><span></span></div>`;msgsEl().appendChild(el);scrollB(); }
function removeTyping(){ const t=document.getElementById('typing'); if(t)t.remove(); }
function appendAI(t){ _ai(t); }
function appendToolCall(desc,cmd,shell){ _tool(desc,cmd,shell||S.shell); }

// ══════════════════════════════════════════════════════════════════
// SEND
// ══════════════════════════════════════════════════════════════════
function se(t){ document.getElementById('ci').value=t; sendMsg(); }
function stopAgent(){ socket.emit('stop_agent',{}); setBusy(false); removeTyping(); toast('Stopping…','warning'); }
function editMsg(msgId,currentText){
  const inp=document.getElementById('ci');
  inp.value=currentText; inp.focus();
  inp.style.height='auto'; inp.style.height=Math.min(inp.scrollHeight,120)+'px';
  S.editingMsgId=msgId; document.getElementById('sbtn').title='Send edited message';
  toast('Edit your message and press Enter','info');
}
const _origSendMsg = sendMsg;
function sendMsg(){
  const inp=document.getElementById('ci'), text=inp.value.trim();
  if((!text&&!S.attachments.length)||S.busy||!S.chatId)return;
  if(S.editingMsgId){
    const msgId=S.editingMsgId; S.editingMsgId=null;
    document.getElementById('sbtn').title='';
    showTyping(); setBusy(true);
    socket.emit('edit_message',{message_id:msgId,new_text:text,chat_id:S.chatId,term_id:S.activeTermId||'t1',model:S.curModel,mode:S.curMode});
    inp.value=''; inp.style.height='auto';
    S.attachments=[]; renderAttPrev(); return;
  }
  _user(text,{attachments:S.attachments.map(a=>a.name)});
  showTyping(); setBusy(true);
  socket.emit('chat_message',{chat_id:S.chatId,message:text,term_id:S.activeTermId||'t1',model:S.curModel,mode:S.curMode,attachments:S.attachments});
  fetch(`/api/chats/${S.chatId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:S.curModel,mode:S.curMode})});
  inp.value=''; inp.style.height='auto';
  S.attachments=[]; renderAttPrev();
}
document.getElementById('ci').addEventListener('keydown',e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg();} });
document.getElementById('ci').addEventListener('input',function(){ this.style.height='auto'; this.style.height=Math.min(this.scrollHeight,120)+'px'; });

// ══════════════════════════════════════════════════════════════════
// TERMINALS — with per-terminal command history (↑/↓ arrows)
// ══════════════════════════════════════════════════════════════════
function termWrite(term_id,line){
  const obj=S.terms[term_id]||S.terms[S.activeTermId];
  if(obj) obj.term.writeln(line);
}
function setTermRunning(term_id,running){
  const tab=document.getElementById('tab-'+term_id);
  if(tab) tab.classList.toggle('running',running);
  const t=S.terms[term_id]; if(!t)return;
  const si=document.getElementById('stdin-'+term_id);
  const tir=document.getElementById('tir-'+term_id);
  if(si) si.classList.toggle('active',running);
  if(tir) tir.style.display=running?'none':'flex';
}

function createTerm(){
  termCounter++;
  const id='t'+termCounter;
  const COLS=['#22c55e','#3b82f6','#d4a020','#06b6d4','#ef4444','#a78bfa'];
  const col=COLS[(termCounter-1)%COLS.length];
  const [rr,gg,bb]=[parseInt(col.slice(1,3),16),parseInt(col.slice(3,5),16),parseInt(col.slice(5,7),16)];

  // Per-terminal command history
  const history=[];
  let histIdx=-1;

  const xterm=new Terminal({
    fontFamily:"'JetBrains Mono',Fira Code,Consolas,monospace",
    fontSize:12.5, lineHeight:1.42,
    theme:{
      background:'#1a1a1a',foreground:'#d0d0d0',cursor:col,
      green:'#22c55e',yellow:'#d4a020',red:'#ef4444',
      cyan:'#06b6d4',blue:'#3b82f6',magenta:'#a78bfa',
      white:'#d0d0d0',brightGreen:'#4ade80',brightWhite:'#f0f0f0'
    },
    cursorBlink:true, scrollback:10000, convertEol:true
  });
  const fit=new FitAddon.FitAddon();
  xterm.loadAddon(fit);

  const pane=document.createElement('div');
  pane.className='tpane'; pane.id='pane-'+id;
  pane.innerHTML=`
    <div class="txterm" id="xt-${id}">
      <div class="term-wm">${WATERMARK_SVG}</div>
    </div>
    <div class="stdin-row" id="stdin-${id}">
      <span class="stdin-label">stdin ›</span>
      <input class="stdin-inp" id="si-${id}" placeholder="type input for running process…" spellcheck="false" autocomplete="off">
      <button class="stdin-send" onclick="sendStdin('${id}')">send</button>
    </div>
    <div class="tir" id="tir-${id}">
      <span class="tps" id="tps-${id}" style="color:${col}">${S.shell||'sh'}&nbsp;$&nbsp;</span>
      <input class="tinp" id="ti-${id}" type="text"
        placeholder="run command (${S.os||'linux'})…"
        spellcheck="false" autocomplete="off">
      <button class="trun" onclick="runRaw('${id}')">run</button>
    </div>`;

  document.getElementById('tpanes').appendChild(pane);

  xterm.open(document.getElementById('xt-'+id));
  new ResizeObserver(()=>{ try{fit.fit()}catch(e){} }).observe(pane);

  xterm.writeln(`\x1b[1m\x1b[38;2;${rr};${gg};${bb}m  Agent 2 Terminal #${termCounter}  [${S.os||'linux'} / ${S.shell||'sh'}]\x1b[0m`);
  xterm.writeln('\x1b[2m  '+'─'.repeat(40)+'\x1b[0m\n');

  // Command input with ↑/↓ history
  const tiEl=document.getElementById('ti-'+id);
  tiEl.addEventListener('keydown', e=>{
    if(e.key==='Enter'){ runRaw(id); return; }
    if(e.key==='ArrowUp'){
      e.preventDefault();
      if(!history.length) return;
      histIdx=Math.min(histIdx+1, history.length-1);
      tiEl.value=history[histIdx];
      setTimeout(()=>tiEl.setSelectionRange(tiEl.value.length,tiEl.value.length),0);
    }
    if(e.key==='ArrowDown'){
      e.preventDefault();
      if(histIdx<=0){histIdx=-1;tiEl.value='';return;}
      histIdx--;
      tiEl.value=history[histIdx];
      setTimeout(()=>tiEl.setSelectionRange(tiEl.value.length,tiEl.value.length),0);
    }
  });

  document.getElementById('si-'+id).addEventListener('keydown',e=>{ if(e.key==='Enter')sendStdin(id); });

  // Tab
  const tabs=document.getElementById('ttabs');
  const tab=document.createElement('div');
  tab.className='ttab'; tab.id='tab-'+id; tab.dataset.id=id;
  tab.innerHTML=`<div class="ttab-dot" style="background:${col}"></div><span>${S.shell||'sh'} #${termCounter}</span><span class="ttab-close" onclick="closeTerm(event,'${id}')">×</span>`;
  tab.onclick=e=>{ if(!e.target.classList.contains('ttab-close'))switchTerm(id); };
  // Insert before the + button
  tabs.insertBefore(tab, tabs.querySelector('.ttab-add'));

  S.terms[id]={term:xterm,fit,col,pane,history,getHistIdx:()=>histIdx,setHistIdx:v=>{histIdx=v;}};
  return id;
}

function runRaw(id){
  const tiEl=document.getElementById('ti-'+id);
  const cmd=tiEl.value.trim();
  if(!cmd)return;
  const t=S.terms[id];
  if(t){
    if(!t.history.length||t.history[0]!==cmd) t.history.unshift(cmd);
    if(t.history.length>100) t.history.pop();
    t.setHistIdx(-1);
  }
  socket.emit('run_raw_command',{command:cmd,term_id:id});
  tiEl.value='';
}

function addTerm(){
  const id=createTerm(); switchTerm(id);
  setTimeout(()=>{ try{S.terms[id].fit.fit()}catch(e){} },80);
}
function switchTerm(id){
  Object.keys(S.terms).forEach(tid=>{
    document.getElementById('pane-'+tid)?.classList.remove('active');
    document.getElementById('tab-'+tid)?.classList.remove('active');
  });
  S.activeTermId=id;
  document.getElementById('pane-'+id)?.classList.add('active');
  document.getElementById('tab-'+id)?.classList.add('active');
  setTimeout(()=>{ try{S.terms[id].fit.fit()}catch(e){} },50);
}
function closeTerm(e,id){
  e.stopPropagation();
  if(Object.keys(S.terms).length<=1){toast('At least one terminal required','warning');return;}
  document.getElementById('pane-'+id)?.remove();
  document.getElementById('tab-'+id)?.remove();
  try{S.terms[id]?.term.dispose();}catch(e){}
  delete S.terms[id];
  if(S.activeTermId===id){
    const rem=Object.keys(S.terms);
    if(rem.length)switchTerm(rem[rem.length-1]);
  }
}
function clearActiveTerm(){ const t=S.terms[S.activeTermId]; if(t){t.term.clear();t.term.writeln('\x1b[2m  [cleared]\x1b[0m\n');} }
function killActive(){ socket.emit('terminal_kill',{term_id:S.activeTermId}); }
function sendStdin(id){ const inp=document.getElementById('si-'+id); const text=inp.value; socket.emit('terminal_input',{term_id:id,text}); inp.value=''; }

// Fallback terminal init
document.addEventListener('DOMContentLoaded',()=>{ setTimeout(()=>{ if(!Object.keys(S.terms).length) addTerm(); },1200); });

// ══════════════════════════════════════════════════════════════════
// MODALS
// ══════════════════════════════════════════════════════════════════
function openMod(n){ document.getElementById('mod-'+n).classList.add('show'); if(n==='mem')loadMems(); if(n==='rules')loadRules(); if(n==='settings')loadKeys(); }
function closeMod(n){ document.getElementById('mod-'+n).classList.remove('show'); }
function ovClick(e,n){ if(e.target===document.getElementById('mod-'+n))closeMod(n); }
document.addEventListener('keydown',e=>{ if(e.key==='Escape')document.querySelectorAll('.mov.show').forEach(m=>m.classList.remove('show')); });
function switchMTab(el,panelId){
  const modal=el.closest('.modal');
  modal.querySelectorAll('.mtab').forEach(t=>t.classList.remove('active'));
  modal.querySelectorAll('.mpanel').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(panelId).classList.add('active');
}

// ══════════════════════════════════════════════════════════════════
// MEMORIES
// ══════════════════════════════════════════════════════════════════
async function loadMems(){ const mems=await(await fetch('/api/memories')).json(); const el=document.getElementById('mem-list'); if(!mems.length){el.innerHTML='<div class="empty-hint">No memories yet.<br>Add facts the agent should always know.</div>';return;} el.innerHTML=mems.map(m=>`<div class="mitem"><span class="mitem-txt">${esc(m.content)}</span><button class="m-del" onclick="delMem('${m.id}')">×</button></div>`).join(''); }
async function addMem(){ const inp=document.getElementById('mem-inp'),c=inp.value.trim(); if(!c)return; await fetch('/api/memories',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:c})}); inp.value=''; loadMems(); toast('Memory saved','success'); }
async function delMem(id){ await fetch(`/api/memories/${id}`,{method:'DELETE'}); loadMems(); }

// ══════════════════════════════════════════════════════════════════
// RULES
// ══════════════════════════════════════════════════════════════════
async function loadRules(){ const rules=await(await fetch('/api/rules')).json(); const el=document.getElementById('rule-list'); if(!rules.length){el.innerHTML='<div class="empty-hint">No rules yet.<br>Add custom instructions for the agent.</div>';return;} el.innerHTML=rules.map(r=>`<div class="mitem"><span class="mitem-txt${r.active?'':' off'}">${esc(r.content)}</span><button class="m-toggle${r.active?' on':''}" onclick="togRule('${r.id}')">${r.active?'on':'off'}</button><button class="m-del" onclick="delRule('${r.id}')">×</button></div>`).join(''); }
async function addRule(){ const inp=document.getElementById('rule-inp'),c=inp.value.trim(); if(!c)return; await fetch('/api/rules',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:c})}); inp.value=''; loadRules(); toast('Rule added','success'); }
async function togRule(id){ await fetch(`/api/rules/${id}`,{method:'PUT'}); loadRules(); }
async function delRule(id){ await fetch(`/api/rules/${id}`,{method:'DELETE'}); loadRules(); }

// ══════════════════════════════════════════════════════════════════
// API KEYS
// ══════════════════════════════════════════════════════════════════
async function loadKeys(){
  const keys=await(await fetch('/api/keys')).json();
  const el=document.getElementById('key-list');
  if(!keys.length){el.innerHTML='<div class="empty-hint">No keys configured.<br>Paste a key above to add.</div>';return;}
  el.innerHTML=keys.map(k=>{
    const pct=Math.min(100,Math.round((k.tokens/(128000*10))*100));
    const fc=pct>80?'high':pct>50?'mid':'';
    return `<div class="key-card"><div class="key-row1"><div class="key-num">#${k.label}</div><input class="key-name-inp" value="${esc(k.name)}" placeholder="Label…" onblur="renameKey('${k.label}',this.value)" onkeydown="if(event.key==='Enter')this.blur()"><span class="key-st ${k.active?'a':'x'}">${k.active?'active':'exhausted'}</span><button class="key-pin${k.pinned?' pinned':''}" onclick="pinKey('${k.label}',${!k.pinned})">${k.pinned?'📌 pinned':'pin'}</button>${!k.active?`<button class="key-rst" onclick="rstKey('${k.label}')">reset</button>`:''}<button class="key-del" onclick="delKey('${k.label}')">×</button></div><div class="key-row2"><span class="key-prev">${k.preview}</span><div class="key-usage"><span><strong>${(k.tokens||0).toLocaleString()}</strong> tokens</span><span><strong>${k.requests||0}</strong> req</span>${k.last_used?`<span>${k.last_used.slice(11,16)}</span>`:''}</div></div><div class="usage-bar"><div class="usage-fill ${fc}" style="width:${pct}%"></div></div></div>`;
  }).join('');
}
async function addKey(){
  const inp=document.getElementById('key-inp'),nameInp=document.getElementById('key-name-inp');
  const key=inp.value.trim().replace(/\s/g,''),name=nameInp.value.trim();
  if(!key){toast('Paste your API key first','warning');inp.focus();return;}
  if(key.length<15){toast('Key too short','error');inp.focus();return;}
  const d=await(await fetch('/api/keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,name})})).json();
  if(d.ok){inp.value='';nameInp.value='';loadKeys();toast('Key added','success');}
  else toast(d.error==='already_exists'?'Key already added':d.error||'Failed','error');
}
async function renameKey(label,name){ await fetch(`/api/keys/${label}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})}); }
async function delKey(l){ await fetch(`/api/keys/${l}`,{method:'DELETE'}); loadKeys(); }
async function rstKey(l){ await fetch(`/api/keys/${l}/reset`,{method:'POST'}); loadKeys(); toast('Key reset','success'); }
async function pinKey(label,pin){
  await fetch(`/api/keys/${label}/pin`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin})});
  loadKeys(); toast(pin?`Pinned to Key #${label}`:'Auto-rotate enabled','success');
}
async function loadUsage(){
  const keys=await(await fetch('/api/keys')).json();
  const el=document.getElementById('usage-list');
  if(!keys.length){el.innerHTML='<div class="empty-hint">No usage data yet.</div>';return;}
  const total=keys.reduce((s,k)=>s+(k.tokens||0),0);
  el.innerHTML=`<div style="margin-bottom:10px;font-size:11px;font-family:var(--mn);color:var(--tx2)">Total: <strong style="color:var(--wh)">${total.toLocaleString()}</strong> tokens</div>`+
    keys.map(k=>{const pct=total?Math.round(k.tokens/total*100):0;return `<div class="key-card"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px"><span style="font-size:12px;font-family:var(--mn);color:var(--wh);font-weight:500">${esc(k.name)}</span><span class="key-st ${k.active?'a':'x'}">${k.active?'active':'exhausted'}</span></div><div class="key-usage" style="margin-bottom:5px"><span>Tokens:<strong>${(k.tokens||0).toLocaleString()}</strong></span><span>Req:<strong>${k.requests||0}</strong></span><span>Share:<strong>${pct}%</strong></span></div><div class="usage-bar"><div class="usage-fill ${pct>80?'high':pct>50?'mid':''}" style="width:${pct}%"></div></div></div>`;}).join('');
}

// ══════════════════════════════════════════════════════════════════
// RESIZER
// ══════════════════════════════════════════════════════════════════
const rz=document.getElementById('rz'),cpEl=document.getElementById('cp'),taEl=document.getElementById('ta'),wsEl=document.getElementById('ws');
let drag=false;
rz.addEventListener('mousedown',e=>{drag=true;rz.classList.add('drag');document.body.style.cssText+='cursor:col-resize;user-select:none';e.preventDefault();});
document.addEventListener('mousemove',e=>{
  if(!drag)return;
  const rect=wsEl.getBoundingClientRect();
  const w=Math.max(280,Math.min(rect.width-220,e.clientX-rect.left));
  cpEl.style.cssText=`flex:none;width:${w}px`;
  taEl.style.cssText=`flex:none;width:${rect.width-w-3}px`;
  Object.values(S.terms).forEach(t=>{try{t.fit.fit()}catch(e){}});
});
document.addEventListener('mouseup',()=>{
  if(!drag)return; drag=false; rz.classList.remove('drag');
  document.body.style.cursor=document.body.style.userSelect='';
  Object.values(S.terms).forEach(t=>{try{t.fit.fit()}catch(e){}});
});
window.addEventListener('resize',()=>{ Object.values(S.terms).forEach(t=>{try{t.fit.fit()}catch(e){}});});

document.getElementById('msgs').addEventListener('scroll', function() {
  const btn = document.getElementById('scroll-bottom-btn');
  if (!btn) return;

  const isFarUp = (this.scrollHeight - this.scrollTop - this.clientHeight) > 400;
  
  if (isFarUp) {
    btn.style.display = 'flex';
    // Optional: add a class for a fade-in animation
    btn.style.opacity = '1';
  } else {
    btn.style.opacity = '0';
    setTimeout(() => { if(btn.style.opacity === '0') btn.style.display = 'none'; }, 200);
  }
});