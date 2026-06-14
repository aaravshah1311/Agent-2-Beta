"""
agent2/ui.py
────────────
Single-file HTML/CSS/JS frontend served at GET /.
Edit this file to change the look and behaviour of the web UI.
"""

HTML: str = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent 2</title>

<!-- Theme detection — runs BEFORE styles to prevent flash -->
<script>
(function(){
  const saved = localStorage.getItem('a2-theme');
  const sys   = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', saved || sys);
})();
</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.8.1/socket.io.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<link rel="stylesheet" href="/style.css">
</head>
<body>

<!-- ═══ MOBILE BLOCK — shown only on phones ═══════════════════ -->
<div id="mobile-block">
  <canvas id="mobile-canvas" width="100" height="100"></canvas>
  <div class="mb-title">Agent 2</div>
  <div class="mb-msg">
    <strong>📵 Not designed for mobile</strong>
    Agent 2 is a professional terminal agent built for laptops and desktops.<br>Please open it on a larger screen.
  </div>
</div>

<!-- ═══ LOADER ════════════════════════════════════════════════ -->
<div id="loader">
  <canvas id="loader-canvas" width="120" height="120"></canvas>
  <div class="loader-title">Agent 2</div>
  <div class="loader-dots"><span></span><span></span><span></span></div>
</div>

<!-- ═══ APP ══════════════════════════════════════════════════ -->
<div id="app">

<!-- Sidebar -->
<div id="sb">
  <div class="sb-head">
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 20 20" fill="none">
          <polygon points="10,1.5 17.1,5.5 17.1,13.5 10,17.5 2.9,13.5 2.9,5.5"
            stroke="#3b82f6" stroke-width="1.1" fill="rgba(59,130,246,0.15)" stroke-linejoin="round"/>
          <circle cx="10" cy="1.5" r="1" fill="#3b82f6" opacity=".8"/>
          <circle cx="17.1" cy="5.5" r=".85" fill="#06b6d4" opacity=".7"/>
          <circle cx="17.1" cy="13.5" r=".85" fill="#3b82f6" opacity=".7"/>
          <circle cx="10" cy="17.5" r="1" fill="#06b6d4" opacity=".8"/>
          <circle cx="2.9" cy="13.5" r=".85" fill="#3b82f6" opacity=".7"/>
          <circle cx="2.9" cy="5.5" r=".85" fill="#06b6d4" opacity=".7"/>
          <circle cx="10" cy="9.5" r="2.6" fill="#3b82f6" opacity=".9"/>
          <circle cx="10" cy="9.5" r="1.1" fill="white"/>
        </svg>
      </div>
      <div class="logo-txt">Agent 2</div>
    </div>
    <button class="new-btn" onclick="newChat()">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="5" y1="1" x2="5" y2="9"/><line x1="1" y1="5" x2="9" y2="5"/></svg>
      New
    </button>
  </div>
  <div class="sb-search"><input id="srch" placeholder="Search chats…" oninput="filterChats(this.value)"></div>
  <div class="clist" id="clist"></div>
  <div class="sb-ctx">
    <div class="ctx-row">
      <div class="ctx-ring">
        <svg viewBox="0 0 28 28"><circle class="ctx-track" cx="14" cy="14" r="11"/><circle class="ctx-fill" id="ctx-arc" cx="14" cy="14" r="11"/></svg>
        <div class="ctx-pct" id="ctx-pct">0%</div>
      </div>
      <div class="ctx-info"><div><strong id="ctx-tok">0</strong> tokens</div><div><strong id="ctx-rem">128k</strong> left</div></div>
    </div>
  </div>
  <div class="sb-foot">
    <button class="sfb" onclick="openMod('mem')" title="Memories">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M2 3a1 1 0 00-1 1v8a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H9.5a1 1 0 01-.8-.4l-.9-1.2A1 1 0 006.99 2H3a1 1 0 00-1 1zm1 1h4l.9 1.2a1 1 0 00.8.4H14v7H3V4z"/></svg>
      Mem
    </button>
    <button class="sfb" onclick="openMod('rules')" title="Rules">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M2.5 3a.5.5 0 000 1h11a.5.5 0 000-1zm0 3a.5.5 0 000 1h11a.5.5 0 000-1zm0 3a.5.5 0 000 1h6a.5.5 0 000-1zm0 3a.5.5 0 000 1h6a.5.5 0 000-1zm8-6a.5.5 0 01.5-.5h2a.5.5 0 010 1h-2a.5.5 0 01-.5-.5zm0 3a.5.5 0 01.5-.5h2a.5.5 0 010 1h-2a.5.5 0 01-.5-.5zm0 3a.5.5 0 01.5-.5h2a.5.5 0 010 1h-2a.5.5 0 01-.5-.5z"/></svg>
      Rules
    </button>
    <button class="sfb" onclick="openMod('settings')" title="API Keys">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 8a4 4 0 007.465 2H14v2h2v-2h1v-2h-1V6h-2V4h-2v2H7.465A4 4 0 000 8zm4 0a2 2 0 100-4 2 2 0 000 4z"/></svg>
      Keys
    </button>
  </div>
</div>

<!-- Main -->
<div id="main">
  <div id="topbar">
    <div class="tb-title" id="tb-title" onclick="startRename()">New Chat</div>
    <div class="model-area">
      <select id="model-sel" class="model-sel" onchange="onModelChange(this.value)"></select>
      <select id="mode-sel"  class="mode-sel"  onchange="onModeChange(this.value)"></select>
    </div>
    <div class="tb-right">
      <span class="shell-badge" id="shell-badge">—</span>
      <span class="tb-tokens" id="tb-tok">0 tokens</span>
      <button class="theme-btn" onclick="toggleTheme()" title="Toggle theme">
        <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
        <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      </button>
    </div>
  </div>

  <div id="ws">
    <div id="cp">
      <div id="msgs">
        <div id="welcome">
          <!-- Three.js 3D logo lives here -->
          <canvas id="logo-canvas" width="160" height="160"></canvas>
          <div class="wl-title">Agent 2</div>
          <div class="wl-sub">Autonomous agent with terminal access.</div>
          <div class="wl-chips" id="wl-chips"></div>
        </div>
      </div>
      
      <button id="scroll-bottom-btn" onclick="scrollB()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 13l5 5 5-5M7 6l5 5 5-5"/></svg>
      </button>
    

      <div id="ia">
        <div id="att-preview"></div>
        <div id="iw">
          <textarea id="ci" rows="1" placeholder="Describe target or type a command…"></textarea>
          <button class="ia-btn" id="att-btn" onclick="document.getElementById('file-input').click()" title="Attach file">
            <svg viewBox="0 0 16 16" fill="currentColor"><path d="M4.5 3a2.5 2.5 0 015 0v9a1.5 1.5 0 01-3 0V5a.5.5 0 011 0v7a.5.5 0 001 0V3a1.5 1.5 0 00-3 0v9a2.5 2.5 0 005 0V5a.5.5 0 011 0v7a3.5 3.5 0 01-7 0z"/></svg>
          </button>
          <input type="file" id="file-input" multiple accept=".txt,.py,.js,.ts,.html,.css,.json,.yaml,.yml,.md,.csv,.xml,.sh,.bat,.c,.cpp,.h,.java,.go,.rs,.pdf,.png,.jpg,.jpeg,.gif,.webp" onchange="handleFiles(this)">
          <button class="ia-btn" id="stop-btn" onclick="stopAgent()" style="display:none;background:var(--rd)" title="Stop">
            <svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1"/></svg>
          </button>
          <button class="ia-btn" id="sbtn" onclick="sendMsg()" disabled>
            <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
          </button>
        </div>
        <div class="ia-foot">
          <span class="ia-hint">Enter send · Shift+Enter newline · 📎 attach files</span>
          <div id="srow"><div class="sdot" id="sdot"></div><span id="stxt">Connecting…</span></div>
        </div>
      </div>
      
    </div>

    <div id="rz"></div>

    <div id="ta">
      <div id="ttop">
        <div style="display:flex;gap:5px">
          <div class="cbadge" id="ws-badge"><div class="cbdot"></div><span>WS</span></div>
          <div class="cbadge" id="ag-badge"><div class="cbdot"></div><span>Idle</span></div>
        </div>
        <div class="ttop-r">
          <button class="tbtn kill" id="kill-btn" onclick="killActive()">■ kill</button>
          <button class="tbtn add" onclick="addTerm()">+ Term</button>
          <button class="tbtn" onclick="clearActiveTerm()">clear</button>
        </div>
      </div>
      <div id="ttabs">
        <!-- + New Terminal tab button -->
        <!--
            <div class="ttab-add" onclick="addTerm()" title="New terminal">
              <svg viewBox="0 0 10 10" fill="currentColor"><path d="M5 1v8M1 5h8"/></svg>
              Terminal
            </div>
        -->
      </div>
      <div id="tpanes"></div>
    </div>
  </div>
</div>
</div><!-- /#app -->

<!-- Modals -->
<div class="mov" id="mod-mem" onclick="ovClick(event,'mem')">
  <div class="modal">
    <div class="mhd"><div class="mtabs"><div class="mtab active" onclick="switchMTab(this,'mem-p')">Memories</div></div><button class="mclose" onclick="closeMod('mem')">×</button></div>
    <div class="mbody"><div id="mem-p" class="mpanel active">
      <div class="add-row"><textarea id="mem-inp" rows="2" placeholder="e.g. My target network is 10.10.0.0/24"></textarea><button class="add-btn" onclick="addMem()">Add</button></div>
      <div id="mem-list"></div>
    </div></div>
  </div>
</div>

<div class="mov" id="mod-rules" onclick="ovClick(event,'rules')">
  <div class="modal">
    <div class="mhd"><div class="mtabs"><div class="mtab active" onclick="switchMTab(this,'rule-p')">Rules</div></div><button class="mclose" onclick="closeMod('rules')">×</button></div>
    <div class="mbody"><div id="rule-p" class="mpanel active">
      <div class="add-row"><textarea id="rule-inp" rows="2" placeholder="e.g. Always save scan results to /tmp/"></textarea><button class="add-btn" onclick="addRule()">Add</button></div>
      <div id="rule-list"></div>
    </div></div>
  </div>
</div>

<div class="mov" id="mod-settings" onclick="ovClick(event,'settings')">
  <div class="modal" style="width:560px">
    <div class="mhd">
      <div class="mtabs">
        <div class="mtab active" onclick="switchMTab(this,'key-p');loadKeys()">API Keys</div>
        <div class="mtab" onclick="switchMTab(this,'usage-p');loadUsage()">Usage</div>
      </div>
      <button class="mclose" onclick="closeMod('settings')">×</button>
    </div>
    <div class="mbody">
      <div id="key-p" class="mpanel active">
        <div style="display:flex;flex-direction:column;gap:5px;margin-bottom:12px">
          <div class="add-row" style="margin-bottom:0">
            <input type="text" id="key-inp" placeholder="Paste API key (AIzaSy...)" autocomplete="off" spellcheck="false" onkeydown="if(event.key==='Enter')addKey()">
            <input type="text" id="key-name-inp" placeholder="Label (optional)" style="max-width:110px;flex:none" autocomplete="off">
            <button class="add-btn" onclick="addKey()">Add</button>
          </div>
          <div style="display:flex;align-items:center;gap:10px;padding:0 2px">
            <label style="display:flex;align-items:center;gap:5px;font-size:10px;font-family:var(--mn);color:var(--tx3);cursor:pointer">
              <input type="checkbox" id="key-show" onchange="document.getElementById('key-inp').type=this.checked?'text':'password'" style="accent-color:var(--ac)"> show key
            </label>
            <span style="font-size:10px;color:var(--tx3);font-family:var(--mn)">Free key: <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--ac)">aistudio.google.com</a></span>
          </div>
        </div>
        <div id="key-list"></div>
      </div>
      <div id="usage-p" class="mpanel"><div id="usage-list"></div></div>
    </div>
  </div>
</div>

<script src="/script.js"></script>
</body>
</html>"""


def get_html() -> str:
    """Return the HTML string (entry point for routes.py)."""
    return HTML
