# ThinkOS Sprint 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform ThinkOS from a 4-tab layout into a full OS-feeling app with a persistent sidebar, Full Council session, Blind Spot tool, saved history, templates, voice input, dark/light mode, keyboard shortcuts, and mobile bottom nav.

**Architecture:** The frontend is a single `static/index.html` SPA — no build toolchain. The backend is `app.py` (Flask + OpenRouter). Two new API endpoints are added to `app.py`. The entire frontend is rewritten from scratch (new layout), preserving all existing API call logic and result-rendering patterns.

**Tech Stack:** Python/Flask, vanilla JS, CSS custom properties, Web Speech API, localStorage, OpenRouter API (claude-haiku-4-5)

---

## File Map

| File | Action | What changes |
|---|---|---|
| `app.py` | Modify | Add `BLINDSPOT_PROMPT`, `SYNTHESIS_PROMPT`, `/api/blindspot`, `/api/synthesis` routes |
| `static/index.html` | Full rewrite | New sidebar layout + all 10 Sprint 1 features |

---

## Task 1: Add Blind Spot backend endpoint

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add BLINDSPOT_PROMPT and route to app.py**

Open `app.py`. After the `KINGDOM_PROMPT` block and before `@app.route('/api/kingdom')`, add:

```python
BLINDSPOT_PROMPT = """You are a Blind Spot Detector. Your job is to find the ONE perspective that is completely absent from someone's thinking about a situation.

Rules:
- Identify ONE specific missing angle — not generic "consider all sides" advice
- Name it precisely (e.g. "the impact on your team", "the long-term version of yourself", "the person who disagrees with you most")
- why_its_missing: why this angle is psychologically easy to avoid (1-2 sentences)
- reframe: one specific reframe of the situation from this missing perspective (2-3 sentences)
- blind_spot_question: one sharp question under 20 words that forces the missing perspective

If context about REI/Ladder results is provided, cross-reference them: "Both Instinct and Reason focused on X — what's neither seeing?"

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "missing_perspective": "...",
  "why_its_missing": "...",
  "reframe": "...",
  "blind_spot_question": "..."
}"""

SYNTHESIS_PROMPT = """You are a Council Synthesist. You have been given the results of four thinking tools applied to the same situation: REI Council (three minds), The Information Ladder (which rung), Kingdom Lens (biblical perspective), and a Blind Spot Detector (missing angle).

Your job: read across all four results and write a synthesis — what do they collectively reveal that none says alone?

Rules:
- synthesis: 3-4 sentences. What is the deeper pattern across all four lenses? Be specific to this situation.
- synthesis_question: ONE question under 25 words that cuts to the heart of what all four lenses are pointing at
- Do not summarise each tool — synthesise across them
- Be direct. No hedging. No "it seems like."

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "synthesis": "...",
  "synthesis_question": "..."
}"""
```

- [ ] **Step 2: Add /api/blindspot route**

After the `/api/kingdom` route, add:

```python
@app.route('/api/blindspot', methods=['POST'])
def blindspot():
    data = request.get_json()
    situation = (data or {}).get('situation', '').strip()
    context = (data or {}).get('context', '').strip()
    if not situation:
        return jsonify({'error': 'No situation provided'}), 400
    prompt = situation
    if context:
        prompt = f"{situation}\n\nContext from other tools:\n{context}"
    try:
        text = call_ai(BLINDSPOT_PROMPT, [{'role': 'user', 'content': prompt}])
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/synthesis', methods=['POST'])
def synthesis():
    data = request.get_json()
    parts = []
    if data.get('rei'):
        r = data['rei']
        parts.append(f"REI Council — Instinct: {r.get('instinct','')} | Emotion: {r.get('emotion','')} | Reason: {r.get('reason','')} | Council view: {r.get('majority_view','')} | Alignment: {r.get('alignment','')}")
    if data.get('ladder'):
        l = data['ladder']
        parts.append(f"Information Ladder — Rung {l.get('current_rung','')} ({l.get('rung_name','')}): {l.get('current_view','')} | Ascent: {l.get('ascent_question','')}")
    if data.get('kingdom'):
        k = data['kingdom']
        parts.append(f"Kingdom Lens — Kingdom: {k.get('kingdom','')} | Eternal weight: {k.get('eternal_weight','')} | Path: {k.get('the_path','')} | Question: {k.get('kingdom_question','')}")
    if data.get('blind_spot'):
        b = data['blind_spot']
        parts.append(f"Blind Spot — Missing: {b.get('missing_perspective','')} | Reframe: {b.get('reframe','')}")
    if not parts:
        return jsonify({'error': 'No tool results provided'}), 400
    combined = '\n\n'.join(parts)
    try:
        text = call_ai(SYNTHESIS_PROMPT, [{'role': 'user', 'content': combined}], max_tokens=512)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

- [ ] **Step 3: Restart Flask and test blindspot endpoint**

In terminal:
```bash
cd "C:\Users\john_\OneDrive\Desktop\New folder\think-os"
python app.py
```

In a second terminal:
```bash
curl -s -X POST http://localhost:5000/api/blindspot \
  -H "Content-Type: application/json" \
  -d "{\"situation\": \"I want to leave my job to build my own company\"}" | python -m json.tool
```

Expected: JSON with `missing_perspective`, `why_its_missing`, `reframe`, `blind_spot_question` keys.

- [ ] **Step 4: Test synthesis endpoint**

```bash
curl -s -X POST http://localhost:5000/api/synthesis \
  -H "Content-Type: application/json" \
  -d "{\"rei\": {\"instinct\": \"Fear of failure\", \"emotion\": \"Excited\", \"reason\": \"Runway is 6 months\", \"majority_view\": \"Do it carefully\", \"alignment\": \"partial\"}, \"ladder\": {\"current_rung\": 4, \"rung_name\": \"Meaning\", \"current_view\": \"This is about identity\", \"ascent_question\": \"What kind of person do you want to be?\"}}" | python -m json.tool
```

Expected: JSON with `synthesis` and `synthesis_question` keys.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: add /api/blindspot and /api/synthesis endpoints"
```

---

## Task 2: HTML skeleton — sidebar layout

**Files:**
- Rewrite: `static/index.html`

Start a fresh `index.html`. Keep the `<head>` metadata and CSS variable structure from the existing file. Build the HTML skeleton only — no JS yet, no styling yet beyond the layout frame.

- [ ] **Step 1: Write the new HTML skeleton**

Replace `static/index.html` entirely with:

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ThinkOS</title>
<style>
/* ── Reset ── */
* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── CSS Variables — dark theme ── */
:root {
  --bg:        #0a0a0a;
  --surface:   #141414;
  --surface2:  #1c1c1c;
  --border:    #262626;
  --text:      #efefef;
  --muted:     #555;
  --instinct:  #f59e0b;
  --emotion:   #60a5fa;
  --reason:    #34d399;
  --ladder:    #a78bfa;
  --socratic:  #f472b6;
  --kingdom:   #fbbf24;
  --kingdom2:  #92400e;
  --blind:     #fb923c;
  --radius:    10px;
  --sb-width:  240px;
}

/* ── Light theme overrides ── */
[data-theme="light"] {
  --bg:       #f8f7f4;
  --surface:  #ffffff;
  --surface2: #f0eeeb;
  --border:   #e0ddd8;
  --text:     #1a1a1a;
  --muted:    #888;
}

body {
  background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh; display: flex;
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sb-width); background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  padding: 20px 16px 16px; gap: 10px;
  position: fixed; top: 0; left: 0; bottom: 0;
  overflow-y: auto; z-index: 100;
}
.logo { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; flex-shrink: 0; }
.logo span { color: var(--ladder); }

/* ── Main area ── */
.main {
  margin-left: var(--sb-width);
  flex: 1; display: flex; flex-direction: column;
  min-height: 100vh;
}
.main-inner { padding: 28px 32px 80px; max-width: 900px; width: 100%; margin: 0 auto; }

/* ── Mobile ── */
@media(max-width:640px) {
  .sidebar { display: none; }
  .main { margin-left: 0; }
  .bottom-nav { display: flex !important; }
  .mobile-thought-bar { display: block !important; }
}
.bottom-nav {
  display: none; position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--surface); border-top: 1px solid var(--border);
  height: 60px; z-index: 200; align-items: stretch;
}
.mobile-thought-bar {
  display: none; padding: 10px 16px;
  background: var(--surface); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 99;
}
</style>
</head>
<body>

<!-- ── Sidebar ── -->
<aside class="sidebar" id="sidebar">
  <!-- populated in Task 3 -->
  <div class="logo">Think<span>OS</span></div>
</aside>

<!-- ── Mobile thought bar (hidden on desktop) ── -->
<div class="mobile-thought-bar" id="mobile-thought-bar">
  <!-- populated in Task 3 -->
</div>

<!-- ── Main content ── -->
<div class="main">
  <div class="main-inner" id="main-inner">
    <!-- tool views populated in Task 5+ -->
  </div>
</div>

<!-- ── Mobile bottom nav ── -->
<nav class="bottom-nav" id="bottom-nav">
  <!-- populated in Task 11 -->
</nav>

<script>
// JS populated task by task
</script>
</body>
</html>
```

- [ ] **Step 2: Verify layout in browser**

Start Flask (`python app.py`), open http://localhost:5000. You should see a blank page with a thin left sidebar (240px) containing just "ThinkOS". No errors in console.

- [ ] **Step 3: Commit**

```bash
git add static/index.html
git commit -m "feat: sidebar layout skeleton"
```

---

## Task 3: Sidebar content — thought field, tool nav, sessions

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add sidebar CSS**

Inside the `<style>` block, after the `.bottom-nav` rule, add:

```css
/* ── Sidebar elements ── */
.sb-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--muted); flex-shrink: 0;
}
.sb-thought-wrap { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.sb-thought-row { display: flex; gap: 6px; align-items: flex-start; }
.sb-textarea {
  flex: 1; background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius); color: var(--text); font-size: 13px;
  line-height: 1.55; padding: 10px 12px; resize: none; min-height: 80px;
  outline: none; font-family: inherit; transition: border-color 0.15s;
}
.sb-textarea:focus { border-color: var(--ladder); }
.sb-textarea::placeholder { color: var(--muted); }
.btn-voice {
  background: none; border: 1px solid var(--border); border-radius: 8px;
  padding: 8px; color: var(--muted); cursor: pointer; font-size: 14px;
  transition: all 0.15s; flex-shrink: 0; line-height: 1;
}
.btn-voice:hover { color: var(--text); border-color: #555; }
.btn-voice.listening { color: var(--socratic); border-color: var(--socratic); animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

.btn-full-council {
  background: var(--ladder); color: #000; border: none; border-radius: var(--radius);
  padding: 10px; font-size: 13px; font-weight: 700; cursor: pointer;
  transition: opacity 0.15s; width: 100%; flex-shrink: 0;
}
.btn-full-council:hover { opacity: 0.85; }
.btn-full-council:disabled { opacity: 0.4; cursor: not-allowed; }

.sb-divider { height: 1px; background: var(--border); flex-shrink: 0; }

.tool-nav { display: flex; flex-direction: column; gap: 3px; flex-shrink: 0; }
.tool-btn {
  padding: 9px 12px; border-radius: 8px; border: none; background: transparent;
  color: var(--muted); font-size: 13px; font-weight: 500; cursor: pointer;
  text-align: left; transition: all 0.15s; width: 100%;
}
.tool-btn:hover { background: var(--surface2); color: var(--text); }
.tool-btn.active { font-weight: 600; }
.tool-btn.active-rei      { background: #2a1f06; color: var(--instinct); }
.tool-btn.active-ladder   { background: #1e1830; color: var(--ladder); }
.tool-btn.active-kingdom  { background: #2a1e06; color: var(--kingdom); }
.tool-btn.active-socratic { background: #271326; color: var(--socratic); }
.tool-btn.active-blind    { background: #2a1500; color: var(--blind); }
.tool-btn.active-council  { background: #1e1830; color: var(--ladder); }

.btn-templates {
  background: none; border: 1px solid var(--border); border-radius: 8px;
  color: var(--muted); font-size: 12px; padding: 8px 12px; cursor: pointer;
  transition: all 0.15s; text-align: left; width: 100%; flex-shrink: 0;
}
.btn-templates:hover { color: var(--text); border-color: #555; }

.session-list { display: flex; flex-direction: column; gap: 3px; flex: 1; overflow-y: auto; min-height: 0; }
.session-item {
  padding: 7px 10px; border-radius: 7px; font-size: 11px; color: var(--muted);
  cursor: pointer; transition: all 0.15s; display: flex; align-items: center;
  justify-content: space-between; gap: 6px; border: 1px solid transparent;
}
.session-item:hover { background: var(--surface2); color: var(--text); }
.session-item.active { background: var(--surface2); color: var(--text); border-color: var(--border); }
.session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-del {
  opacity: 0; background: none; border: none; color: var(--muted);
  cursor: pointer; font-size: 13px; padding: 0 2px; flex-shrink: 0;
}
.session-item:hover .session-del { opacity: 1; }
.btn-view-all {
  font-size: 11px; color: var(--muted); background: none; border: none;
  cursor: pointer; padding: 4px 10px; text-align: center; transition: color 0.15s;
}
.btn-view-all:hover { color: var(--text); }

.sb-bottom { margin-top: auto; display: flex; justify-content: flex-end; padding-top: 8px; flex-shrink: 0; }
.btn-theme {
  background: none; border: 1px solid var(--border); border-radius: 8px;
  padding: 6px 10px; font-size: 14px; cursor: pointer; color: var(--muted);
  transition: all 0.15s;
}
.btn-theme:hover { color: var(--text); border-color: #555; }
```

- [ ] **Step 2: Replace sidebar HTML content**

Replace the entire `<aside class="sidebar" ...>` block with:

```html
<aside class="sidebar" id="sidebar">
  <div class="logo">Think<span>OS</span></div>

  <div class="sb-thought-wrap">
    <div class="sb-label">Current Thought</div>
    <div class="sb-thought-row">
      <textarea class="sb-textarea" id="global-thought"
        placeholder="What's on your mind?"
        oninput="onThoughtInput()"
        rows="4"></textarea>
      <button class="btn-voice" id="voice-btn" onclick="toggleVoice()" title="Voice input">🎙️</button>
    </div>
  </div>

  <button class="btn-full-council" id="full-council-btn" onclick="runFullCouncil()">⚡ Full Council</button>

  <div class="sb-divider"></div>
  <div class="sb-label">Tools</div>
  <nav class="tool-nav">
    <button class="tool-btn" data-tool="rei"      onclick="switchTool('rei')">REI Council</button>
    <button class="tool-btn" data-tool="ladder"   onclick="switchTool('ladder')">The Ladder</button>
    <button class="tool-btn" data-tool="kingdom"  onclick="switchTool('kingdom')">Kingdom Lens</button>
    <button class="tool-btn" data-tool="socratic" onclick="switchTool('socratic')">Socratic</button>
    <button class="tool-btn" data-tool="blind"    onclick="switchTool('blind')">🔍 Blind Spot</button>
  </nav>

  <div class="sb-divider"></div>
  <button class="btn-templates" onclick="openTemplates()">📋 Templates</button>

  <div class="sb-divider"></div>
  <div class="sb-label">Recent Sessions</div>
  <div class="session-list" id="session-list"></div>
  <button class="btn-view-all" onclick="openSessionsModal()">View all →</button>

  <div class="sb-bottom">
    <button class="btn-theme" onclick="toggleTheme()" id="theme-btn" title="Toggle theme">🌓</button>
  </div>
</aside>
```

- [ ] **Step 3: Add mobile thought bar HTML**

Replace the `<div class="mobile-thought-bar" ...>` with:

```html
<div class="mobile-thought-bar" id="mobile-thought-bar">
  <textarea class="sb-textarea" id="mobile-thought"
    placeholder="What's on your mind?"
    oninput="onMobileThoughtInput()"
    rows="2"
    style="min-height:50px;"></textarea>
</div>
```

- [ ] **Step 4: Add core JS — thought sync, tool switching, theme**

Replace the empty `<script>` block with:

```html
<script>
// ── State ──────────────────────────────────────────────────────
let currentTool = 'rei';
let lastResults = {};
let lastInputs  = {};
let socratiMessages = [];

// ── Thought field sync ─────────────────────────────────────────
function getThought() {
  return document.getElementById('global-thought').value.trim();
}
function onThoughtInput() {
  const val = document.getElementById('global-thought').value;
  const mob = document.getElementById('mobile-thought');
  if (mob) mob.value = val;
  localStorage.setItem('thinkos_thought', val);
}
function onMobileThoughtInput() {
  const val = document.getElementById('mobile-thought').value;
  document.getElementById('global-thought').value = val;
  localStorage.setItem('thinkos_thought', val);
}
function restoreThought() {
  const saved = localStorage.getItem('thinkos_thought') || '';
  document.getElementById('global-thought').value = saved;
  const mob = document.getElementById('mobile-thought');
  if (mob) mob.value = saved;
}

// ── Tool switching ─────────────────────────────────────────────
const TOOL_COLORS = { rei:'rei', ladder:'ladder', kingdom:'kingdom', socratic:'socratic', blind:'blind', council:'council' };

function switchTool(tool) {
  currentTool = tool;
  // update sidebar buttons
  document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.className = 'tool-btn';
    if (btn.dataset.tool === tool) btn.classList.add('active', 'active-' + tool);
  });
  // update bottom nav
  document.querySelectorAll('.bnav-btn').forEach(btn => {
    btn.className = 'bnav-btn';
    if (btn.dataset.tool === tool) btn.classList.add('active-' + tool);
  });
  // show the right view
  document.querySelectorAll('.tool-view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById('view-' + tool);
  if (view) view.classList.add('active');
  // sync thought into tool's input if it has one
  const thought = getThought();
  const inputMap = { rei: 'rei-input', ladder: 'ladder-input', kingdom: 'kingdom-input', blind: 'blind-input' };
  const inputId = inputMap[tool];
  if (inputId) {
    const el = document.getElementById(inputId);
    if (el && !el.value && thought) el.value = thought;
  }
}

// ── Theme toggle ───────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('thinkos_theme', next);
  document.getElementById('theme-btn').textContent = next === 'dark' ? '🌓' : '☀️';
}
function restoreTheme() {
  const saved = localStorage.getItem('thinkos_theme');
  const system = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  const theme = saved || system;
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = theme === 'dark' ? '🌓' : '☀️';
}

// ── Utility ────────────────────────────────────────────────────
function esc(t) {
  return String(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
async function callAPI(endpoint, body) {
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

// ── Voice input ────────────────────────────────────────────────
let recognition = null;
function toggleVoice() {
  const btn = document.getElementById('voice-btn');
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Voice input not supported in this browser. Try Chrome.');
    return;
  }
  if (recognition) {
    recognition.stop(); recognition = null;
    btn.classList.remove('listening'); return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.continuous = true; recognition.interimResults = false;
  recognition.onresult = e => {
    const transcript = Array.from(e.results).map(r => r[0].transcript).join(' ');
    const ta = document.getElementById('global-thought');
    ta.value = (ta.value ? ta.value + ' ' : '') + transcript;
    onThoughtInput();
  };
  recognition.onerror = () => { recognition = null; btn.classList.remove('listening'); };
  recognition.onend   = () => { recognition = null; btn.classList.remove('listening'); };
  recognition.start();
  btn.classList.add('listening');
}

// ── Keyboard shortcuts ─────────────────────────────────────────
document.addEventListener('keydown', e => {
  const mod = e.metaKey || e.ctrlKey;
  if (mod && e.key === 'k') { e.preventDefault(); document.getElementById('global-thought').focus(); }
  if (mod && e.shiftKey && e.key === 'F') { e.preventDefault(); runFullCouncil(); }
  if (mod && e.key === 'Enter') { e.preventDefault(); submitCurrentTool(); }
  if (mod && e.key === '1') { e.preventDefault(); switchTool('rei'); }
  if (mod && e.key === '2') { e.preventDefault(); switchTool('ladder'); }
  if (mod && e.key === '3') { e.preventDefault(); switchTool('kingdom'); }
  if (mod && e.key === '4') { e.preventDefault(); switchTool('socratic'); }
  if (mod && e.key === '5') { e.preventDefault(); switchTool('blind'); }
  if (e.key === 'Escape') { closeAllModals(); }
});
function submitCurrentTool() {
  const fns = { rei: submitREI, ladder: submitLadder, kingdom: submitKingdom, blind: submitBlind, socratic: submitSocratic };
  if (fns[currentTool]) fns[currentTool]();
}
function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('visible'));
}

// Stubs — filled in later tasks
function runFullCouncil() {}
function openTemplates() {}
function openSessionsModal() {}
function submitREI() {}
function submitLadder() {}
function submitKingdom() {}
function submitBlind() {}
function submitSocratic() {}
function renderSessions() {}

// ── Init ───────────────────────────────────────────────────────
restoreTheme();
restoreThought();
switchTool('rei');
renderSessions();
</script>
```

- [ ] **Step 5: Verify in browser**

Reload http://localhost:5000. You should see:
- Sidebar with logo, empty textarea, "⚡ Full Council" button, 5 tool nav buttons, "📋 Templates", "Recent Sessions", and theme toggle
- Theme toggle switches between dark and dark-ish light mode and persists on refresh
- Typing in the thought field persists on refresh
- `Cmd/Ctrl+K` focuses the thought field
- `Cmd/Ctrl+1–5` switches the active tool button highlight

- [ ] **Step 6: Commit**

```bash
git add static/index.html
git commit -m "feat: sidebar content, theme toggle, voice input, keyboard shortcuts"
```

---

## Task 4: Progress bar + tool view container

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add progress bar CSS + tool view CSS**

Add inside `<style>`:

```css
/* ── Progress bar ── */
.progress-bar-wrap {
  position: sticky; top: 0; z-index: 50;
  height: 3px; background: transparent; overflow: hidden;
  margin: -28px -32px 28px;
}
.progress-bar {
  height: 100%; width: 0%; transition: width 0.3s ease;
  border-radius: 0 2px 2px 0;
}
.progress-bar.running { animation: glow 1.5s ease-in-out infinite alternate; }
@keyframes glow { from { filter: brightness(1); } to { filter: brightness(1.4); } }
.loading-msg-wrap { display: none; align-items: center; gap: 10px; padding: 20px 0 8px; }
.loading-msg-wrap.visible { display: flex; }
.loading-msg { font-size: 13px; color: var(--muted); font-style: italic; }

/* ── Tool views ── */
.tool-view { display: none; }
.tool-view.active { display: block; }

.tool-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.tool-title { font-size: 18px; font-weight: 700; }
.tool-desc { font-size: 13px; color: var(--muted); line-height: 1.6; flex: 1; }

.thought-pill {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 10px 14px; margin-bottom: 16px;
  font-size: 13px; color: var(--muted);
}
.thought-pill-text { flex: 1; color: var(--text); font-style: italic; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.thought-pill-edit { font-size: 11px; color: var(--muted); cursor: pointer; text-decoration: underline; white-space: nowrap; }
.thought-pill-edit:hover { color: var(--text); }

.btn-submit {
  padding: 10px 22px; border-radius: 99px; border: none;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: opacity 0.15s, transform 0.1s; margin-top: 8px;
}
.btn-submit:hover { opacity: 0.88; }
.btn-submit:active { transform: scale(0.97); }
.btn-submit:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }
.btn-rei      { background: var(--instinct); color: #000; }
.btn-ladder   { background: var(--ladder);   color: #000; }
.btn-kingdom  { background: var(--kingdom);  color: #000; }
.btn-socratic { background: var(--socratic); color: #000; }
.btn-blind    { background: var(--blind);    color: #000; }

.results-wrap { margin-top: 24px; display: none; }
.results-wrap.visible { display: block; }

/* ── Copy button ── */
.copy-btn {
  display: inline-flex; align-items: center; gap: 5px;
  background: none; border: 1px solid var(--border); color: var(--muted);
  font-size: 11px; padding: 4px 10px; border-radius: 6px; cursor: pointer;
  transition: all 0.15s; margin-top: 14px;
}
.copy-btn:hover { color: var(--text); border-color: #555; }
.copy-btn.copied { color: var(--reason); border-color: var(--reason); }
```

- [ ] **Step 2: Add the main-inner HTML with progress bar and tool views**

Replace `<div class="main-inner" id="main-inner">` and its contents with:

```html
<div class="main-inner" id="main-inner">
  <!-- Progress bar -->
  <div class="progress-bar-wrap" id="progress-wrap">
    <div class="progress-bar" id="progress-bar"></div>
  </div>

  <!-- Loading message -->
  <div class="loading-msg-wrap" id="loading-msg-wrap">
    <div class="loading-msg" id="loading-msg">Thinking...</div>
  </div>

  <!-- Tool views — populated in Tasks 5-9 -->
  <div class="tool-view" id="view-rei"></div>
  <div class="tool-view" id="view-ladder"></div>
  <div class="tool-view" id="view-kingdom"></div>
  <div class="tool-view" id="view-socratic"></div>
  <div class="tool-view" id="view-blind"></div>
  <div class="tool-view" id="view-council"></div>
</div>
```

- [ ] **Step 3: Add progress bar JS functions**

Add to `<script>` (before the `// ── Init` section):

```javascript
// ── Progress bar ──────────────────────────────────────────────
const TOOL_BAR_COLORS = {
  rei: '#f59e0b', ladder: '#a78bfa', kingdom: '#fbbf24',
  socratic: '#f472b6', blind: '#fb923c', council: '#a78bfa'
};
const LOADING_MSGS = {
  rei:      ['Instinct is speaking...','Emotion weighs in...','Reason calculates...','Finding the majority...'],
  ladder:   ['Finding your rung...','Looking above and below...','Formulating the ascent question...'],
  kingdom:  ['Searching Scripture...','Finding the parallel...','Applying the lenses...','Weighing eternity...'],
  socratic: ['Sharpening the question...'],
  blind:    ['Scanning for blind spots...','What is nobody saying...','Finding the missing angle...'],
  council:  ['Consulting REI Council... (1/4)','Climbing the Ladder... (2/4)','Seeing through the Kingdom lens... (3/4)','Detecting blind spots... (4/4)','Synthesising across all lenses...']
};
let _loadingInterval = null;
let _progressInterval = null;
let _progressValue = 0;

function startLoading(tool) {
  const bar = document.getElementById('progress-bar');
  const wrap = document.getElementById('loading-msg-wrap');
  const msg  = document.getElementById('loading-msg');
  // colour
  bar.style.background = TOOL_BAR_COLORS[tool] || '#a78bfa';
  bar.classList.add('running');
  // animate 0 → 85
  _progressValue = 0; bar.style.width = '0%';
  clearInterval(_progressInterval);
  _progressInterval = setInterval(() => {
    if (_progressValue < 85) { _progressValue += (85 - _progressValue) * 0.04; bar.style.width = _progressValue + '%'; }
  }, 100);
  // messages
  wrap.classList.add('visible');
  const msgs = LOADING_MSGS[tool] || ['Thinking...'];
  let i = 0; msg.textContent = msgs[0];
  clearInterval(_loadingInterval);
  _loadingInterval = setInterval(() => { i = (i+1)%msgs.length; msg.textContent = msgs[i]; }, 1800);
  // disable submit btn
  const btn = document.getElementById(tool + '-submit-btn');
  if (btn) btn.disabled = true;
}

function stopLoading(tool) {
  const bar = document.getElementById('progress-bar');
  clearInterval(_progressInterval); clearInterval(_loadingInterval);
  bar.style.width = '100%';
  setTimeout(() => { bar.style.transition = 'opacity 0.4s'; bar.style.opacity = '0';
    setTimeout(() => { bar.style.width='0%'; bar.style.opacity='1'; bar.style.transition='width 0.3s ease'; bar.classList.remove('running'); }, 400);
  }, 300);
  document.getElementById('loading-msg-wrap').classList.remove('visible');
  const btn = document.getElementById(tool + '-submit-btn');
  if (btn) btn.disabled = false;
}
```

- [ ] **Step 4: Add thought pill JS**

Add to `<script>` (before `// ── Init`):

```javascript
// ── Thought pill ──────────────────────────────────────────────
function renderThoughtPill(containerId) {
  const thought = getThought();
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!thought) { el.innerHTML = ''; return; }
  el.innerHTML = `<div class="thought-pill">
    <span style="font-size:12px;color:var(--muted)">🔒</span>
    <span class="thought-pill-text">${esc(thought)}</span>
    <span class="thought-pill-edit" onclick="document.getElementById('global-thought').focus()">edit</span>
  </div>`;
}
```

- [ ] **Step 5: Verify in browser**

Reload. The main area should be blank (no tool views yet). No errors in console.

- [ ] **Step 6: Commit**

```bash
git add static/index.html
git commit -m "feat: progress bar and tool view containers"
```

---

## Task 5: REI Council tool view

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add REI CSS**

Add inside `<style>`:

```css
/* ── REI ── */
.rei-cards { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-bottom: 16px; }
@media(max-width:640px){ .rei-cards { grid-template-columns: 1fr; } }
.mind-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; border-top-width: 3px; }
.mind-card.instinct { border-top-color: var(--instinct); }
.mind-card.emotion  { border-top-color: var(--emotion); }
.mind-card.reason   { border-top-color: var(--reason); }
.mind-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 10px; }
.mind-card.instinct .mind-label { color: var(--instinct); }
.mind-card.emotion  .mind-label { color: var(--emotion); }
.mind-card.reason   .mind-label { color: var(--reason); }
.mind-text { font-size: 14px; line-height: 1.65; color: #ccc; }
.rei-bottom { display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: start; margin-bottom: 14px; }
@media(max-width:600px){ .rei-bottom { grid-template-columns: 1fr; } }
.majority-box { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.majority-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
.majority-text { font-size: 14px; line-height: 1.6; }
.alignment-badge { padding: 8px 16px; border-radius: 99px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap; align-self: start; }
.alignment-divided { background: #3a1010; color: #f87171; }
.alignment-partial  { background: #2a2010; color: var(--instinct); }
.alignment-strong   { background: #0f2a1a; color: var(--reason); }
.action-question { padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--text); border-radius: var(--radius); font-size: 15px; font-style: italic; color: var(--text); line-height: 1.5; }
```

- [ ] **Step 2: Populate view-rei HTML**

Replace `<div class="tool-view" id="view-rei"></div>` with:

```html
<div class="tool-view" id="view-rei">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--instinct)">REI Council</div>
    <div class="tool-desc">Three minds — <strong>Instinct</strong> (fear, protection), <strong>Emotion</strong> (desire, vision), <strong>Reason</strong> (analysis, strategy) — then where they agree.</div>
  </div>
  <div id="rei-pill"></div>
  <button class="btn-submit btn-rei" id="rei-submit-btn" onclick="submitREI()">Consult the Council</button>
  <div class="results-wrap" id="rei-results">
    <div class="rei-cards">
      <div class="mind-card instinct"><div class="mind-label">Instinct</div><div class="mind-text" id="rei-instinct"></div></div>
      <div class="mind-card emotion"><div class="mind-label">Emotion</div><div class="mind-text" id="rei-emotion"></div></div>
      <div class="mind-card reason"><div class="mind-label">Reason</div><div class="mind-text" id="rei-reason"></div></div>
    </div>
    <div class="rei-bottom">
      <div class="majority-box"><div class="majority-label">Council View</div><div class="majority-text" id="rei-majority"></div></div>
      <div class="alignment-badge" id="rei-alignment"></div>
    </div>
    <div class="action-question" id="rei-action"></div>
    <button class="copy-btn" onclick="copyResult('rei')">Copy results</button>
  </div>
</div>
```

- [ ] **Step 3: Replace submitREI stub with real implementation**

Find `function submitREI() {}` and replace with:

```javascript
async function submitREI() {
  const input = getThought();
  if (!input) { document.getElementById('global-thought').focus(); return; }
  lastInputs.rei = input;
  renderThoughtPill('rei-pill');
  startLoading('rei');
  document.getElementById('rei-results').classList.remove('visible');
  try {
    const d = await callAPI('/api/rei', { situation: input });
    lastResults.rei = d;
    document.getElementById('rei-instinct').textContent = d.instinct;
    document.getElementById('rei-emotion').textContent  = d.emotion;
    document.getElementById('rei-reason').textContent   = d.reason;
    document.getElementById('rei-majority').textContent = d.majority_view;
    document.getElementById('rei-action').textContent   = '\u201c' + d.action_question + '\u201d';
    const badge = document.getElementById('rei-alignment');
    const labels = { divided:'Divided', partial:'Partial Alignment', strong:'Strong Alignment' };
    badge.textContent = labels[d.alignment] || d.alignment;
    badge.className = 'alignment-badge alignment-' + d.alignment;
    document.getElementById('rei-results').classList.add('visible');
    saveSession();
  } catch(e) { alert('Error: ' + e.message); }
  finally { stopLoading('rei'); }
}
```

- [ ] **Step 4: Test REI in browser**

Switch to REI Council in sidebar. Type a situation in the thought field. Click "Consult the Council". Verify:
- Progress bar animates with amber colour
- Loading messages cycle
- Results appear with 3 mind cards, alignment badge, action question

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat: REI Council tool view wired up"
```

---

## Task 6: Ladder, Kingdom, Socratic, Blind Spot tool views

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add Ladder CSS**

Add inside `<style>`:

```css
/* ── Ladder ── */
.ladder-layout { display: grid; grid-template-columns: 130px 1fr; gap: 24px; align-items: start; }
@media(max-width:560px){ .ladder-layout { grid-template-columns: 1fr; } }
.ladder-visual { display: flex; flex-direction: column; gap: 3px; }
.rung { display: flex; align-items: center; gap: 10px; padding: 7px 12px; border-radius: 8px; border: 1px solid transparent; }
.rung-num { font-size: 11px; font-weight: 700; color: var(--muted); width: 14px; text-align: right; }
.rung-name { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.rung.active { background: #1e1830; border-color: var(--ladder); }
.rung.active .rung-num, .rung.active .rung-name { color: var(--ladder); }
.rung-connector { width: 2px; height: 8px; background: var(--border); margin-left: 22px; }
.ladder-info { display: flex; flex-direction: column; gap: 12px; }
.ladder-view { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.ladder-view-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
.lv-above .ladder-view-label { color: var(--ladder); }
.lv-current { border-top: 2px solid var(--ladder) !important; }
.lv-current .ladder-view-label { color: var(--text); }
.lv-below .ladder-view-label { color: var(--muted); }
.ladder-view-text { font-size: 14px; line-height: 1.65; color: #ccc; }
.ladder-view.dim { opacity: 0.45; }
.ascent-q { padding: 14px 18px; background: #1e1830; border: 1px solid var(--ladder); border-radius: var(--radius); font-size: 15px; font-style: italic; color: var(--ladder); line-height: 1.5; }
```

- [ ] **Step 2: Add Kingdom, Socratic, Blind Spot CSS**

Add inside `<style>`:

```css
/* ── Kingdom ── */
.kingdom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px; }
@media(max-width:640px){ .kingdom-grid { grid-template-columns: 1fr; } }
.k-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; border-top: 3px solid var(--kingdom); }
.k-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--kingdom); margin-bottom: 10px; }
.k-text  { font-size: 14px; line-height: 1.65; color: #ccc; }
.analogy-card { background: #1a1200; border: 1px solid #3d2e00; border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.analogy-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.analogy-title { font-size: 13px; font-weight: 700; color: var(--kingdom); text-transform: uppercase; letter-spacing: 0.08em; }
.analogy-person { font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.analogy-situation { font-size: 13px; color: #aaa; line-height: 1.6; margin-bottom: 10px; font-style: italic; }
.analogy-parallel { font-size: 14px; color: #ddd; line-height: 1.65; }
.scripture-section { margin-bottom: 16px; }
.scripture-title { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }
.verse-card { background: var(--surface2); border: 1px solid var(--border); border-left: 3px solid var(--kingdom); border-radius: var(--radius); padding: 16px; margin-bottom: 10px; }
.verse-ref  { font-size: 11px; font-weight: 700; color: var(--kingdom); margin-bottom: 6px; }
.verse-text { font-size: 14px; font-style: italic; color: #ddd; line-height: 1.6; margin-bottom: 8px; }
.verse-applied { font-size: 13px; color: #aaa; line-height: 1.6; border-top: 1px solid var(--border); padding-top: 8px; }
.kingdom-q { padding: 16px 20px; background: #1a1200; border: 1px solid var(--kingdom); border-radius: var(--radius); font-size: 16px; font-style: italic; color: var(--kingdom); line-height: 1.5; }

/* ── Socratic ── */
.chat-window { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); min-height: 260px; max-height: 420px; overflow-y: auto; padding: 18px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 14px; }
.chat-empty { color: var(--muted); font-size: 14px; text-align: center; margin: auto; line-height: 1.7; }
.msg { display: flex; flex-direction: column; gap: 4px; max-width: 86%; }
.msg-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
.msg-text { padding: 11px 15px; border-radius: 10px; font-size: 14px; line-height: 1.6; }
.msg.user { align-self: flex-end; text-align: right; }
.msg.user .msg-label { color: var(--muted); }
.msg.user .msg-text  { background: var(--surface2); color: var(--text); }
.msg.socratic { align-self: flex-start; }
.msg.socratic .msg-label { color: var(--socratic); }
.msg.socratic .msg-text  { background: #1e1030; border: 1px solid #3a1a4a; color: var(--text); font-style: italic; }
.chat-input-row { display: flex; gap: 10px; align-items: flex-end; }
.chat-input-row textarea { flex: 1; min-height: 50px; max-height: 120px; resize: none; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 15px; line-height: 1.6; padding: 12px; outline: none; font-family: inherit; }
.reset-btn { background: none; border: 1px solid var(--border); color: var(--muted); padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: all 0.15s; margin-top: 8px; }
.reset-btn:hover { color: var(--text); border-color: #555; }

/* ── Blind Spot ── */
.blind-cards { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-bottom: 16px; }
@media(max-width:640px){ .blind-cards { grid-template-columns: 1fr; } }
.blind-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; border-top: 3px solid var(--blind); }
.blind-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--blind); margin-bottom: 10px; }
.blind-text { font-size: 14px; line-height: 1.65; color: #ccc; }
.blind-q { padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--blind); border-radius: var(--radius); font-size: 15px; font-style: italic; color: var(--blind); line-height: 1.5; }
```

- [ ] **Step 3: Populate Ladder view HTML**

Replace `<div class="tool-view" id="view-ladder"></div>` with:

```html
<div class="tool-view" id="view-ladder">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--ladder)">The Ladder</div>
    <div class="tool-desc">Reality has 5 rungs: <strong>Mathematics → Physics → Consciousness → Meaning → God</strong>. Where is your question — and what becomes visible one rung higher?</div>
  </div>
  <div id="ladder-pill"></div>
  <button class="btn-submit btn-ladder" id="ladder-submit-btn" onclick="submitLadder()">Diagnose</button>
  <div class="results-wrap" id="ladder-results">
    <div class="ladder-layout">
      <div class="ladder-visual" id="ladder-visual"></div>
      <div class="ladder-info">
        <div class="ladder-view lv-above dim" id="lv-above"><div class="ladder-view-label">One rung up</div><div class="ladder-view-text" id="lv-above-text"></div></div>
        <div class="ladder-view lv-current"><div class="ladder-view-label">Current rung</div><div class="ladder-view-text" id="lv-current-text"></div></div>
        <div class="ladder-view lv-below dim" id="lv-below"><div class="ladder-view-label">One rung down</div><div class="ladder-view-text" id="lv-below-text"></div></div>
        <div class="ascent-q" id="ladder-ascent"></div>
      </div>
    </div>
    <button class="copy-btn" onclick="copyResult('ladder')">Copy results</button>
  </div>
</div>
```

- [ ] **Step 4: Populate Kingdom view HTML**

Replace `<div class="tool-view" id="view-kingdom"></div>` with:

```html
<div class="tool-view" id="view-kingdom">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--kingdom)">Kingdom Lens</div>
    <div class="tool-desc">See your situation through a <strong>biblical lens</strong> — four perspectives, a biblical analogy, and Scripture applied directly to your situation.</div>
  </div>
  <div id="kingdom-pill"></div>
  <button class="btn-submit btn-kingdom" id="kingdom-submit-btn" onclick="submitKingdom()">See Through the Lens</button>
  <div class="results-wrap" id="kingdom-results">
    <div class="kingdom-grid">
      <div class="k-card"><div class="k-label">Kingdom View</div><div class="k-text" id="k-kingdom"></div></div>
      <div class="k-card"><div class="k-label">The Person</div><div class="k-text" id="k-person"></div></div>
      <div class="k-card"><div class="k-label">Eternal Weight</div><div class="k-text" id="k-eternal"></div></div>
      <div class="k-card"><div class="k-label">The Path Through</div><div class="k-text" id="k-path"></div></div>
    </div>
    <div class="analogy-card">
      <div class="analogy-header"><div style="font-size:18px">📜</div><div class="analogy-title">Biblical Parallel</div></div>
      <div class="analogy-person" id="k-analogy-person"></div>
      <div class="analogy-situation" id="k-analogy-situation"></div>
      <div class="analogy-parallel" id="k-analogy-parallel"></div>
    </div>
    <div class="scripture-section">
      <div class="scripture-title">Scripture & Applied Wisdom</div>
      <div id="k-scripture"></div>
    </div>
    <div class="kingdom-q" id="k-question"></div>
    <button class="copy-btn" onclick="copyResult('kingdom')">Copy results</button>
  </div>
</div>
```

- [ ] **Step 5: Populate Socratic view HTML**

Replace `<div class="tool-view" id="view-socratic"></div>` with:

```html
<div class="tool-view" id="view-socratic">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--socratic)">Socratic</div>
    <div class="tool-desc">A thinking partner that <strong>only asks questions</strong>. No answers, no comfort. The best questions make you pause, then think harder.</div>
  </div>
  <div class="chat-window" id="chat-window">
    <div class="chat-empty" id="chat-empty">Type a thought, problem, or belief.<br>The Socratic will ask you a question you won't expect.</div>
  </div>
  <div class="chat-input-row">
    <textarea id="socratic-input" placeholder="Type your thought..." rows="2"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();submitSocratic();}"></textarea>
    <button class="btn-submit btn-socratic" id="socratic-submit-btn" onclick="submitSocratic()">Ask</button>
  </div>
  <button class="reset-btn" onclick="resetSocratic()">Clear conversation</button>
</div>
```

- [ ] **Step 6: Populate Blind Spot view HTML**

Replace `<div class="tool-view" id="view-blind"></div>` with:

```html
<div class="tool-view" id="view-blind">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--blind)">🔍 Blind Spot</div>
    <div class="tool-desc">What perspective is <strong>completely missing</strong> from your thinking? One specific blind spot — not generic advice.</div>
  </div>
  <div id="blind-pill"></div>
  <button class="btn-submit btn-blind" id="blind-submit-btn" onclick="submitBlind()">Find My Blind Spot</button>
  <div class="results-wrap" id="blind-results">
    <div class="blind-cards">
      <div class="blind-card"><div class="blind-label">Missing Perspective</div><div class="blind-text" id="blind-missing"></div></div>
      <div class="blind-card"><div class="blind-label">Why It's Blind</div><div class="blind-text" id="blind-why"></div></div>
      <div class="blind-card"><div class="blind-label">The Reframe</div><div class="blind-text" id="blind-reframe"></div></div>
    </div>
    <div class="blind-q" id="blind-q"></div>
    <button class="copy-btn" onclick="copyResult('blind')">Copy results</button>
  </div>
</div>
```

- [ ] **Step 7: Replace all 4 remaining JS stubs with real implementations**

Find the stubs `function submitLadder() {}`, `function submitKingdom() {}`, `function submitBlind() {}`, `function submitSocratic() {}` and replace with:

```javascript
const RUNG_NAMES = ['Mathematics','Physics','Consciousness','Meaning','God'];

async function submitLadder() {
  const input = getThought();
  if (!input) { document.getElementById('global-thought').focus(); return; }
  lastInputs.ladder = input;
  renderThoughtPill('ladder-pill');
  startLoading('ladder');
  document.getElementById('ladder-results').classList.remove('visible');
  try {
    const d = await callAPI('/api/ladder', { question: input });
    lastResults.ladder = d;
    const rung = d.current_rung;
    const visual = document.getElementById('ladder-visual');
    visual.innerHTML = '';
    for (let i = 5; i >= 1; i--) {
      const div = document.createElement('div');
      div.className = 'rung' + (i === rung ? ' active' : '');
      div.innerHTML = `<span class="rung-num">${i}</span><span class="rung-name">${RUNG_NAMES[i-1]}</span>`;
      visual.appendChild(div);
      if (i > 1) { const c = document.createElement('div'); c.className='rung-connector'; visual.appendChild(c); }
    }
    document.getElementById('lv-current-text').textContent = d.current_view;
    document.getElementById('lv-above-text').textContent   = d.above_view || '(highest rung)';
    document.getElementById('lv-below-text').textContent   = d.below_view || '(lowest rung)';
    document.getElementById('ladder-ascent').textContent   = '\u201c' + d.ascent_question + '\u201d';
    document.getElementById('lv-above').classList.toggle('dim', !d.above_view);
    document.getElementById('lv-below').classList.toggle('dim', !d.below_view);
    document.getElementById('ladder-results').classList.add('visible');
    saveSession();
  } catch(e) { alert('Error: ' + e.message); }
  finally { stopLoading('ladder'); }
}

async function submitKingdom() {
  const input = getThought();
  if (!input) { document.getElementById('global-thought').focus(); return; }
  lastInputs.kingdom = input;
  renderThoughtPill('kingdom-pill');
  startLoading('kingdom');
  document.getElementById('kingdom-results').classList.remove('visible');
  try {
    const d = await callAPI('/api/kingdom', { situation: input }, 1200);
    lastResults.kingdom = d;
    document.getElementById('k-kingdom').textContent = d.kingdom;
    document.getElementById('k-person').textContent  = d.the_person;
    document.getElementById('k-eternal').textContent = d.eternal_weight;
    document.getElementById('k-path').textContent    = d.the_path;
    document.getElementById('k-analogy-person').textContent    = d.biblical_analogy.person_or_story;
    document.getElementById('k-analogy-situation').textContent = d.biblical_analogy.their_situation;
    document.getElementById('k-analogy-parallel').textContent  = d.biblical_analogy.the_parallel;
    const scriptureEl = document.getElementById('k-scripture');
    scriptureEl.innerHTML = '';
    (d.scripture || []).forEach(s => {
      const card = document.createElement('div'); card.className = 'verse-card';
      card.innerHTML = `<div class="verse-ref">${esc(s.reference)}</div><div class="verse-text">\u201c${esc(s.verse)}\u201d</div><div class="verse-applied">${esc(s.applied)}</div>`;
      scriptureEl.appendChild(card);
    });
    document.getElementById('k-question').textContent = '\u201c' + d.kingdom_question + '\u201d';
    document.getElementById('kingdom-results').classList.add('visible');
    saveSession();
  } catch(e) { alert('Error: ' + e.message); }
  finally { stopLoading('kingdom'); }
}

async function submitBlind() {
  const input = getThought();
  if (!input) { document.getElementById('global-thought').focus(); return; }
  lastInputs.blind = input;
  renderThoughtPill('blind-pill');
  startLoading('blind');
  document.getElementById('blind-results').classList.remove('visible');
  try {
    let context = '';
    if (lastResults.rei) context += `REI — Instinct: ${lastResults.rei.instinct} | Emotion: ${lastResults.rei.emotion} | Reason: ${lastResults.rei.reason}\n`;
    if (lastResults.ladder) context += `Ladder — Rung ${lastResults.ladder.current_rung} (${lastResults.ladder.rung_name}): ${lastResults.ladder.current_view}\n`;
    const d = await callAPI('/api/blindspot', { situation: input, context: context.trim() });
    lastResults.blind = d;
    document.getElementById('blind-missing').textContent = d.missing_perspective;
    document.getElementById('blind-why').textContent     = d.why_its_missing;
    document.getElementById('blind-reframe').textContent = d.reframe;
    document.getElementById('blind-q').textContent       = '\u201c' + d.blind_spot_question + '\u201d';
    document.getElementById('blind-results').classList.add('visible');
    saveSession();
  } catch(e) { alert('Error: ' + e.message); }
  finally { stopLoading('blind'); }
}

async function submitSocratic() {
  const input = document.getElementById('socratic-input').value.trim();
  if (!input) return;
  document.getElementById('socratic-input').value = '';
  document.getElementById('chat-empty').style.display = 'none';
  addChatMsg('user', input);
  socratiMessages.push({ role: 'user', content: input });
  document.getElementById('socratic-submit-btn').disabled = true;
  try {
    const d = await callAPI('/api/socratic', { messages: socratiMessages });
    addChatMsg('socratic', d.question);
    socratiMessages.push({ role: 'assistant', content: d.question });
  } catch(e) { addChatMsg('socratic', 'Error: ' + e.message); }
  finally { document.getElementById('socratic-submit-btn').disabled = false; }
}
function addChatMsg(role, text) {
  const win = document.getElementById('chat-window');
  const div = document.createElement('div'); div.className = 'msg ' + role;
  div.innerHTML = `<div class="msg-label">${role==='user'?'You':'Socratic'}</div><div class="msg-text">${esc(text)}</div>`;
  win.appendChild(div); win.scrollTop = win.scrollHeight;
}
function resetSocratic() {
  socratiMessages = [];
  document.getElementById('chat-window').innerHTML = '<div class="chat-empty" id="chat-empty">Type a thought, problem, or belief.<br>The Socratic will ask you a question you won\'t expect.</div>';
}
```

- [ ] **Step 8: Add copyResult function**

Add to `<script>`:

```javascript
function copyResult(mode) {
  const d = lastResults[mode]; if (!d) return;
  let text = '';
  if (mode === 'rei') text = `INSTINCT: ${d.instinct}\n\nEMOTION: ${d.emotion}\n\nREASON: ${d.reason}\n\nCOUNCIL VIEW: ${d.majority_view}\n\nALIGNMENT: ${d.alignment}\n\nKEY QUESTION: ${d.action_question}`;
  else if (mode === 'ladder') text = `RUNG ${d.current_rung} — ${d.rung_name}\n\nCURRENT VIEW: ${d.current_view}\n\nONE RUNG UP: ${d.above_view}\n\nONE RUNG DOWN: ${d.below_view}\n\nASCENT QUESTION: ${d.ascent_question}`;
  else if (mode === 'kingdom') { const v=(d.scripture||[]).map(s=>`${s.reference}: "${s.verse}" — ${s.applied}`).join('\n\n'); text=`KINGDOM VIEW: ${d.kingdom}\n\nTHE PERSON: ${d.the_person}\n\nETERNAL WEIGHT: ${d.eternal_weight}\n\nTHE PATH: ${d.the_path}\n\nBIBLICAL: ${d.biblical_analogy.person_or_story}\n\nSCRIPTURE:\n${v}\n\nQUESTION: ${d.kingdom_question}`; }
  else if (mode === 'blind') text = `MISSING PERSPECTIVE: ${d.missing_perspective}\n\nWHY IT'S BLIND: ${d.why_its_missing}\n\nREFRAME: ${d.reframe}\n\nQUESTION: ${d.blind_spot_question}`;
  navigator.clipboard.writeText(text).then(() => {
    const btn = event.target; btn.textContent='Copied!'; btn.classList.add('copied');
    setTimeout(()=>{ btn.textContent='Copy results'; btn.classList.remove('copied'); }, 2000);
  });
}
```

- [ ] **Step 9: Test all 4 tools**

Test each tool in browser: Ladder (purple bar), Kingdom (gold bar), Blind Spot (orange bar), Socratic (pink). Verify results render correctly and copy button works.

- [ ] **Step 10: Commit**

```bash
git add static/index.html
git commit -m "feat: Ladder, Kingdom, Socratic, Blind Spot tool views"
```

---

## Task 7: Save & History (localStorage)

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add sessions JS**

Replace `function saveSession() {}` stub (or add if not present) and replace `function renderSessions() {}` stub:

```javascript
// ── Sessions ──────────────────────────────────────────────────
function getSessions() {
  try { return JSON.parse(localStorage.getItem('thinkos_sessions') || '[]'); } catch { return []; }
}
function saveSession() {
  const thought = getThought(); if (!thought) return;
  const sessions = getSessions();
  const id = Date.now().toString();
  const title = thought.slice(0, 45) + (thought.length > 45 ? '…' : '');
  // remove existing session with same thought prefix to avoid duplicates
  const filtered = sessions.filter(s => s.title !== title);
  filtered.unshift({ id, title, thought, timestamp: Date.now(), results: { ...lastResults } });
  if (filtered.length > 50) filtered.splice(50);
  localStorage.setItem('thinkos_sessions', JSON.stringify(filtered));
  renderSessions();
}
function deleteSession(id) {
  const sessions = getSessions().filter(s => s.id !== id);
  localStorage.setItem('thinkos_sessions', JSON.stringify(sessions));
  renderSessions();
}
function loadSession(id) {
  const session = getSessions().find(s => s.id === id); if (!session) return;
  document.getElementById('global-thought').value = session.thought;
  onThoughtInput();
  lastResults = { ...session.results };
  // restore visible results
  if (lastResults.rei) {
    const d = lastResults.rei;
    document.getElementById('rei-instinct').textContent = d.instinct;
    document.getElementById('rei-emotion').textContent  = d.emotion;
    document.getElementById('rei-reason').textContent   = d.reason;
    document.getElementById('rei-majority').textContent = d.majority_view;
    document.getElementById('rei-action').textContent   = '\u201c' + d.action_question + '\u201d';
    const badge = document.getElementById('rei-alignment');
    badge.textContent = {divided:'Divided',partial:'Partial Alignment',strong:'Strong Alignment'}[d.alignment]||d.alignment;
    badge.className = 'alignment-badge alignment-' + d.alignment;
    document.getElementById('rei-results').classList.add('visible');
    renderThoughtPill('rei-pill');
  }
  if (lastResults.blind) {
    const d = lastResults.blind;
    document.getElementById('blind-missing').textContent = d.missing_perspective;
    document.getElementById('blind-why').textContent     = d.why_its_missing;
    document.getElementById('blind-reframe').textContent = d.reframe;
    document.getElementById('blind-q').textContent       = '\u201c' + d.blind_spot_question + '\u201d';
    document.getElementById('blind-results').classList.add('visible');
    renderThoughtPill('blind-pill');
  }
  switchTool(lastResults.rei ? 'rei' : lastResults.ladder ? 'ladder' : 'kingdom');
  renderSessions();
}
function renderSessions() {
  const list = document.getElementById('session-list'); if (!list) return;
  const sessions = getSessions().slice(0, 8);
  list.innerHTML = sessions.length ? '' : '<div style="font-size:11px;color:var(--muted);padding:6px 10px">No sessions yet</div>';
  sessions.forEach(s => {
    const item = document.createElement('div'); item.className = 'session-item';
    item.innerHTML = `<span class="session-title">${esc(s.title)}</span><button class="session-del" onclick="event.stopPropagation();deleteSession('${s.id}')" title="Delete">×</button>`;
    item.onclick = () => loadSession(s.id);
    list.appendChild(item);
  });
}
```

- [ ] **Step 2: Add export-to-markdown function**

```javascript
function exportMarkdown() {
  const thought = getThought() || 'Untitled session';
  let md = `# ${thought}\n\n_Exported from ThinkOS — ${new Date().toLocaleDateString()}_\n\n`;
  if (lastResults.rei) {
    const d = lastResults.rei;
    md += `## REI Council\n\n**Instinct:** ${d.instinct}\n\n**Emotion:** ${d.emotion}\n\n**Reason:** ${d.reason}\n\n**Council View:** ${d.majority_view}\n\n**Alignment:** ${d.alignment}\n\n**Key Question:** ${d.action_question}\n\n`;
  }
  if (lastResults.ladder) {
    const d = lastResults.ladder;
    md += `## The Ladder — Rung ${d.current_rung}: ${d.rung_name}\n\n**Current View:** ${d.current_view}\n\n**One Rung Up:** ${d.above_view || 'N/A'}\n\n**One Rung Down:** ${d.below_view || 'N/A'}\n\n**Ascent Question:** ${d.ascent_question}\n\n`;
  }
  if (lastResults.kingdom) {
    const d = lastResults.kingdom;
    md += `## Kingdom Lens\n\n**Kingdom View:** ${d.kingdom}\n\n**The Person:** ${d.the_person}\n\n**Eternal Weight:** ${d.eternal_weight}\n\n**The Path:** ${d.the_path}\n\n**Biblical Parallel:** ${d.biblical_analogy.person_or_story} — ${d.biblical_analogy.the_parallel}\n\n`;
    (d.scripture||[]).forEach(s => { md += `> **${s.reference}:** "${s.verse}"\n> ${s.applied}\n\n`; });
    md += `**Kingdom Question:** ${d.kingdom_question}\n\n`;
  }
  if (lastResults.blind) {
    const d = lastResults.blind;
    md += `## Blind Spot\n\n**Missing:** ${d.missing_perspective}\n\n**Why:** ${d.why_its_missing}\n\n**Reframe:** ${d.reframe}\n\n**Question:** ${d.blind_spot_question}\n\n`;
  }
  if (lastResults.synthesis) {
    const d = lastResults.synthesis;
    md += `## Council Synthesis\n\n${d.synthesis}\n\n**Synthesis Question:** ${d.synthesis_question}\n\n`;
  }
  const blob = new Blob([md], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = thought.slice(0,40).replace(/[^a-z0-9 ]/gi,'_') + '.md';
  a.click();
}
```

- [ ] **Step 3: Test sessions**

Run a REI query. Reload page. Should see session in sidebar list. Click it → restores thought and REI results. Hover session → delete button appears. Click delete → session removed.

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: save & history with localStorage, export to markdown"
```

---

## Task 8: Full Council Session + Synthesis view

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add Full Council view CSS**

Add inside `<style>`:

```css
/* ── Full Council view ── */
.council-view { display: flex; flex-direction: column; gap: 24px; }
.synthesis-card {
  background: linear-gradient(135deg, #1a0a30, #0a1a20);
  border: 1px solid #3a2a5a; border-radius: 14px; padding: 24px;
}
.synthesis-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ladder); margin-bottom: 12px; }
.synthesis-text { font-size: 15px; line-height: 1.7; color: #e0e0e0; margin-bottom: 14px; }
.synthesis-q { font-size: 16px; font-style: italic; color: #fff; padding-top: 14px; border-top: 1px solid #3a2a5a; line-height: 1.5; }
.council-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.council-section-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; cursor: pointer; transition: background 0.15s;
  border-bottom: 1px solid var(--border);
}
.council-section-header:hover { background: var(--surface2); }
.council-section-title { font-size: 14px; font-weight: 700; }
.council-section-toggle { color: var(--muted); font-size: 12px; }
.council-section-body { padding: 18px; }
.council-section.collapsed .council-section-body { display: none; }
.council-section.collapsed .council-section-toggle::before { content: '▶ Show'; }
.council-section:not(.collapsed) .council-section-toggle::before { content: '▼ Hide'; }
.council-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-export { background: none; border: 1px solid var(--border); color: var(--muted); padding: 9px 18px; border-radius: 99px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.btn-export:hover { color: var(--text); border-color: #555; }
```

- [ ] **Step 2: Populate Full Council view HTML**

Replace `<div class="tool-view" id="view-council"></div>` with:

```html
<div class="tool-view" id="view-council">
  <div class="tool-header">
    <div class="tool-title" style="color:var(--ladder)">⚡ Full Council</div>
    <div class="tool-desc">All four lenses in sequence — REI, Ladder, Kingdom, Blind Spot — then a synthesis that reads across all of them.</div>
  </div>
  <div id="council-pill"></div>
  <div class="council-view" id="council-view">

    <!-- Synthesis -->
    <div class="synthesis-card" id="council-synthesis" style="display:none">
      <div class="synthesis-label">⚡ Council Synthesis</div>
      <div class="synthesis-text" id="synth-text"></div>
      <div class="synthesis-q" id="synth-q"></div>
    </div>

    <!-- REI section -->
    <div class="council-section collapsed" id="cs-rei" style="display:none">
      <div class="council-section-header" onclick="toggleCouncilSection('cs-rei')">
        <span class="council-section-title" style="color:var(--instinct)">REI Council</span>
        <span class="council-section-toggle"></span>
      </div>
      <div class="council-section-body" id="cs-rei-body"></div>
    </div>

    <!-- Ladder section -->
    <div class="council-section collapsed" id="cs-ladder" style="display:none">
      <div class="council-section-header" onclick="toggleCouncilSection('cs-ladder')">
        <span class="council-section-title" style="color:var(--ladder)">The Ladder</span>
        <span class="council-section-toggle"></span>
      </div>
      <div class="council-section-body" id="cs-ladder-body"></div>
    </div>

    <!-- Kingdom section -->
    <div class="council-section collapsed" id="cs-kingdom" style="display:none">
      <div class="council-section-header" onclick="toggleCouncilSection('cs-kingdom')">
        <span class="council-section-title" style="color:var(--kingdom)">Kingdom Lens</span>
        <span class="council-section-toggle"></span>
      </div>
      <div class="council-section-body" id="cs-kingdom-body"></div>
    </div>

    <!-- Blind Spot section -->
    <div class="council-section collapsed" id="cs-blind" style="display:none">
      <div class="council-section-header" onclick="toggleCouncilSection('cs-blind')">
        <span class="council-section-title" style="color:var(--blind)">🔍 Blind Spot</span>
        <span class="council-section-toggle"></span>
      </div>
      <div class="council-section-body" id="cs-blind-body"></div>
    </div>

    <!-- Actions -->
    <div class="council-actions" id="council-actions" style="display:none">
      <button class="btn-export" onclick="exportMarkdown()">Export as Markdown</button>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Replace runFullCouncil stub with real implementation**

Find `function runFullCouncil() {}` and replace:

```javascript
async function runFullCouncil() {
  const input = getThought();
  if (!input) { document.getElementById('global-thought').focus(); return; }
  switchTool('council');
  renderThoughtPill('council-pill');
  // hide all sections
  ['council-synthesis','cs-rei','cs-ladder','cs-kingdom','cs-blind','council-actions']
    .forEach(id => { const el=document.getElementById(id); if(el) el.style.display='none'; });

  document.getElementById('full-council-btn').disabled = true;
  startLoading('council');
  try {
    // 1. REI
    const rei = await callAPI('/api/rei', { situation: input });
    lastResults.rei = rei;
    showCouncilSection('cs-rei', renderREIBody(rei));

    // 2. Ladder
    const ladder = await callAPI('/api/ladder', { question: input });
    lastResults.ladder = ladder;
    showCouncilSection('cs-ladder', renderLadderBody(ladder));

    // 3. Kingdom
    const kingdom = await callAPI('/api/kingdom', { situation: input });
    lastResults.kingdom = kingdom;
    showCouncilSection('cs-kingdom', renderKingdomBody(kingdom));

    // 4. Blind Spot
    let context = `REI — Instinct: ${rei.instinct} | Emotion: ${rei.emotion} | Reason: ${rei.reason}\nLadder — Rung ${ladder.current_rung}: ${ladder.current_view}`;
    const blind = await callAPI('/api/blindspot', { situation: input, context });
    lastResults.blind = blind;
    showCouncilSection('cs-blind', renderBlindBody(blind));

    // 5. Synthesis
    const synth = await callAPI('/api/synthesis', { rei, ladder, kingdom, blind_spot: blind });
    lastResults.synthesis = synth;
    document.getElementById('synth-text').textContent = synth.synthesis;
    document.getElementById('synth-q').textContent = '\u201c' + synth.synthesis_question + '\u201d';
    document.getElementById('council-synthesis').style.display = 'block';
    document.getElementById('council-actions').style.display = 'flex';
    saveSession();
  } catch(e) { alert('Full Council error: ' + e.message); }
  finally { stopLoading('council'); document.getElementById('full-council-btn').disabled = false; }
}

function showCouncilSection(id, html) {
  const el = document.getElementById(id); if (!el) return;
  document.getElementById(id + '-body').innerHTML = html;
  el.style.display = 'block';
}
function toggleCouncilSection(id) {
  document.getElementById(id).classList.toggle('collapsed');
}

function renderREIBody(d) {
  const labels = {divided:'Divided',partial:'Partial Alignment',strong:'Strong Alignment'};
  return `<div class="rei-cards">
    <div class="mind-card instinct"><div class="mind-label">Instinct</div><div class="mind-text">${esc(d.instinct)}</div></div>
    <div class="mind-card emotion"><div class="mind-label">Emotion</div><div class="mind-text">${esc(d.emotion)}</div></div>
    <div class="mind-card reason"><div class="mind-label">Reason</div><div class="mind-text">${esc(d.reason)}</div></div>
  </div>
  <div class="rei-bottom">
    <div class="majority-box"><div class="majority-label">Council View</div><div class="majority-text">${esc(d.majority_view)}</div></div>
    <div class="alignment-badge alignment-${d.alignment}">${labels[d.alignment]||d.alignment}</div>
  </div>
  <div class="action-question">\u201c${esc(d.action_question)}\u201d</div>`;
}

function renderLadderBody(d) {
  let rungs = '';
  for (let i=5;i>=1;i--) {
    rungs += `<div class="rung${i===d.current_rung?' active':''}"><span class="rung-num">${i}</span><span class="rung-name">${RUNG_NAMES[i-1]}</span></div>`;
    if (i>1) rungs += `<div class="rung-connector"></div>`;
  }
  return `<div class="ladder-layout">
    <div class="ladder-visual">${rungs}</div>
    <div class="ladder-info">
      <div class="ladder-view lv-above${!d.above_view?' dim':''}"><div class="ladder-view-label">One rung up</div><div class="ladder-view-text">${esc(d.above_view||'(highest rung)')}</div></div>
      <div class="ladder-view lv-current"><div class="ladder-view-label">Current rung</div><div class="ladder-view-text">${esc(d.current_view)}</div></div>
      <div class="ladder-view lv-below${!d.below_view?' dim':''}"><div class="ladder-view-label">One rung down</div><div class="ladder-view-text">${esc(d.below_view||'(lowest rung)')}</div></div>
      <div class="ascent-q">\u201c${esc(d.ascent_question)}\u201d</div>
    </div>
  </div>`;
}

function renderKingdomBody(d) {
  const verses = (d.scripture||[]).map(s=>`<div class="verse-card"><div class="verse-ref">${esc(s.reference)}</div><div class="verse-text">\u201c${esc(s.verse)}\u201d</div><div class="verse-applied">${esc(s.applied)}</div></div>`).join('');
  return `<div class="kingdom-grid">
    <div class="k-card"><div class="k-label">Kingdom View</div><div class="k-text">${esc(d.kingdom)}</div></div>
    <div class="k-card"><div class="k-label">The Person</div><div class="k-text">${esc(d.the_person)}</div></div>
    <div class="k-card"><div class="k-label">Eternal Weight</div><div class="k-text">${esc(d.eternal_weight)}</div></div>
    <div class="k-card"><div class="k-label">The Path Through</div><div class="k-text">${esc(d.the_path)}</div></div>
  </div>
  <div class="analogy-card">
    <div class="analogy-header"><div style="font-size:18px">📜</div><div class="analogy-title">Biblical Parallel</div></div>
    <div class="analogy-person">${esc(d.biblical_analogy.person_or_story)}</div>
    <div class="analogy-situation">${esc(d.biblical_analogy.their_situation)}</div>
    <div class="analogy-parallel">${esc(d.biblical_analogy.the_parallel)}</div>
  </div>
  <div class="scripture-section"><div class="scripture-title">Scripture & Applied Wisdom</div>${verses}</div>
  <div class="kingdom-q">\u201c${esc(d.kingdom_question)}\u201d</div>`;
}

function renderBlindBody(d) {
  return `<div class="blind-cards">
    <div class="blind-card"><div class="blind-label">Missing Perspective</div><div class="blind-text">${esc(d.missing_perspective)}</div></div>
    <div class="blind-card"><div class="blind-label">Why It's Blind</div><div class="blind-text">${esc(d.why_its_missing)}</div></div>
    <div class="blind-card"><div class="blind-label">The Reframe</div><div class="blind-text">${esc(d.reframe)}</div></div>
  </div>
  <div class="blind-q">\u201c${esc(d.blind_spot_question)}\u201d</div>`;
}
```

- [ ] **Step 4: Test Full Council**

Type a situation. Click "⚡ Full Council". Verify:
- Switches to Full Council view
- Progress bar cycles through messages "(1/4)" to "(5/4) Synthesising..."
- Each section appears as it completes
- Synthesis card appears at top with gradient background
- "Export as Markdown" button appears, clicking downloads a `.md` file

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat: Full Council session with synthesis and collapsible sections"
```

---

## Task 9: Workflow Templates modal

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add modal CSS**

Add inside `<style>`:

```css
/* ── Modals ── */
.modal-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.8); z-index: 300;
  align-items: center; justify-content: center; padding: 20px;
}
.modal-overlay.visible { display: flex; }
.modal-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 28px; width: 100%; max-width: 580px;
  max-height: 80vh; overflow-y: auto;
}
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 6px; }
.modal-subtitle { font-size: 13px; color: var(--muted); margin-bottom: 20px; }
.modal-close {
  float: right; background: none; border: none; color: var(--muted);
  font-size: 20px; cursor: pointer; line-height: 1; margin-top: -4px;
}
.modal-close:hover { color: var(--text); }
.template-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media(max-width:500px){ .template-grid { grid-template-columns: 1fr; } }
.template-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px; cursor: pointer;
  transition: all 0.15s;
}
.template-card:hover { border-color: var(--ladder); background: #1a1530; }
.template-name { font-size: 14px; font-weight: 700; margin-bottom: 6px; }
.template-desc { font-size: 12px; color: var(--muted); margin-bottom: 10px; line-height: 1.5; }
.template-chain { display: flex; gap: 4px; flex-wrap: wrap; }
.chain-tag { font-size: 10px; padding: 2px 8px; border-radius: 99px; font-weight: 600; }
.ct-rei      { background: #2a1a06; color: var(--instinct); }
.ct-ladder   { background: #1a1030; color: var(--ladder); }
.ct-kingdom  { background: #1a1200; color: var(--kingdom); }
.ct-socratic { background: #1a0820; color: var(--socratic); }
.ct-blind    { background: #1a0e00; color: var(--blind); }
```

- [ ] **Step 2: Add templates modal HTML**

Add before `</body>`:

```html
<!-- Templates modal -->
<div class="modal-overlay" id="templates-modal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeAllModals()">×</button>
    <div class="modal-title">Choose a Template</div>
    <div class="modal-subtitle">Pre-built thinking sequences for common situations</div>
    <div class="template-grid">
      <div class="template-card" onclick="selectTemplate('big-decision')">
        <div class="template-name">🔮 Big Life Decision</div>
        <div class="template-desc">Major choices with long-term consequences</div>
        <div class="template-chain"><span class="chain-tag ct-rei">REI</span><span class="chain-tag ct-ladder">Ladder</span><span class="chain-tag ct-kingdom">Kingdom</span><span class="chain-tag ct-blind">Blind Spot</span></div>
      </div>
      <div class="template-card" onclick="selectTemplate('conflict')">
        <div class="template-name">⚡ Conflict with Someone</div>
        <div class="template-desc">Tension or breakdown in a relationship</div>
        <div class="template-chain"><span class="chain-tag ct-rei">REI</span><span class="chain-tag ct-socratic">Socratic</span></div>
      </div>
      <div class="template-card" onclick="selectTemplate('creative-block')">
        <div class="template-name">🎨 Creative Block</div>
        <div class="template-desc">Stuck on a project or creative decision</div>
        <div class="template-chain"><span class="chain-tag ct-ladder">Ladder</span><span class="chain-tag ct-socratic">Socratic</span></div>
      </div>
      <div class="template-card" onclick="selectTemplate('discernment')">
        <div class="template-name">✝️ Spiritual Discernment</div>
        <div class="template-desc">Faith-based direction and calling</div>
        <div class="template-chain"><span class="chain-tag ct-kingdom">Kingdom</span><span class="chain-tag ct-socratic">Socratic</span></div>
      </div>
      <div class="template-card" onclick="selectTemplate('pressure-test')">
        <div class="template-name">🧠 Pressure Test an Idea</div>
        <div class="template-desc">Challenge an idea before committing</div>
        <div class="template-chain"><span class="chain-tag ct-rei">REI</span><span class="chain-tag ct-blind">Blind Spot</span></div>
      </div>
      <div class="template-card" onclick="selectTemplate('hard-conversation')">
        <div class="template-name">💬 Hard Conversation</div>
        <div class="template-desc">Preparing for a difficult talk</div>
        <div class="template-chain"><span class="chain-tag ct-rei">REI</span><span class="chain-tag ct-socratic">Socratic</span></div>
      </div>
    </div>
  </div>
</div>

<!-- Sessions modal -->
<div class="modal-overlay" id="sessions-modal">
  <div class="modal-box">
    <button class="modal-close" onclick="closeAllModals()">×</button>
    <div class="modal-title">All Sessions</div>
    <div style="margin-bottom:12px"><input id="sessions-search" type="text" placeholder="Search sessions..." oninput="renderAllSessions()" style="width:100%;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:9px 12px;color:var(--text);font-size:13px;outline:none;"></div>
    <div id="all-sessions-list"></div>
  </div>
</div>
```

- [ ] **Step 3: Replace openTemplates and openSessionsModal stubs**

Find `function openTemplates() {}` and `function openSessionsModal() {}` and replace:

```javascript
const TEMPLATES = {
  'big-decision':    { name:'Big Life Decision',    placeholder:'I'm trying to decide whether to...' },
  'conflict':        { name:'Conflict with Someone', placeholder:'I'm in conflict with someone about...' },
  'creative-block':  { name:'Creative Block',        placeholder:'I'm stuck on...' },
  'discernment':     { name:'Spiritual Discernment', placeholder:'I'm seeking guidance on...' },
  'pressure-test':   { name:'Pressure Test an Idea', placeholder:'I'm considering the idea that...' },
  'hard-conversation':{ name:'Hard Conversation',   placeholder:'I need to have a conversation about...' }
};

function openTemplates() {
  document.getElementById('templates-modal').classList.add('visible');
}
function selectTemplate(id) {
  closeAllModals();
  const tmpl = TEMPLATES[id]; if (!tmpl) return;
  const ta = document.getElementById('global-thought');
  if (!ta.value.trim()) ta.placeholder = tmpl.placeholder;
  ta.focus();
  // if thought already exists, run Full Council immediately
  if (ta.value.trim()) runFullCouncil();
}
function openSessionsModal() {
  document.getElementById('sessions-modal').classList.add('visible');
  renderAllSessions();
}
function renderAllSessions() {
  const query = (document.getElementById('sessions-search')?.value || '').toLowerCase();
  const all = getSessions().filter(s => !query || s.title.toLowerCase().includes(query));
  const list = document.getElementById('all-sessions-list');
  list.innerHTML = all.length ? '' : '<div style="color:var(--muted);font-size:13px;padding:10px 0">No sessions found</div>';
  all.forEach(s => {
    const item = document.createElement('div');
    item.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:10px 12px;border-radius:8px;cursor:pointer;border:1px solid transparent;margin-bottom:4px;';
    item.innerHTML = `<div><div style="font-size:13px;font-weight:600;color:var(--text)">${esc(s.title)}</div><div style="font-size:11px;color:var(--muted)">${new Date(s.timestamp).toLocaleDateString()}</div></div><button style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:15px" onclick="event.stopPropagation();deleteSession('${s.id}');renderAllSessions()">×</button>`;
    item.onmouseenter = () => item.style.background = 'var(--surface2)';
    item.onmouseleave = () => item.style.background = '';
    item.onclick = () => { loadSession(s.id); closeAllModals(); };
    list.appendChild(item);
  });
}
```

- [ ] **Step 4: Test templates modal**

Click "📋 Templates" in sidebar. Modal opens. Click "Big Life Decision". Modal closes, thought field gets placeholder. Type a thought and click "📋 Templates" → "Big Life Decision" again — this time Full Council runs immediately.

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat: workflow templates modal with 6 pre-built sequences"
```

---

## Task 10: Mobile bottom nav

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add bottom nav CSS**

Add inside `<style>`:

```css
/* ── Mobile bottom nav ── */
.bnav-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 3px; background: none; border: none;
  color: var(--muted); font-size: 10px; font-weight: 600;
  cursor: pointer; padding: 6px 4px; transition: color 0.15s;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.bnav-btn .bnav-icon { font-size: 18px; line-height: 1; }
.bnav-btn:hover { color: var(--text); }
.bnav-btn.active-rei      { color: var(--instinct); }
.bnav-btn.active-ladder   { color: var(--ladder); }
.bnav-btn.active-kingdom  { color: var(--kingdom); }
.bnav-btn.active-socratic { color: var(--socratic); }
.bnav-btn.active-blind    { color: var(--blind); }
.fab-council {
  display: none; position: fixed; bottom: 72px; right: 16px;
  background: var(--ladder); color: #000; border: none; border-radius: 99px;
  padding: 14px 18px; font-size: 13px; font-weight: 700; cursor: pointer;
  box-shadow: 0 4px 20px rgba(167,139,250,0.4); z-index: 201; transition: all 0.15s;
}
.fab-council:hover { transform: scale(1.05); }
@media(max-width:640px) {
  .fab-council { display: block; }
  .main-inner { padding: 16px 16px 80px; }
}
```

- [ ] **Step 2: Replace bottom nav HTML**

Replace `<nav class="bottom-nav" id="bottom-nav"><!-- populated in Task 11 --></nav>` with:

```html
<nav class="bottom-nav" id="bottom-nav">
  <button class="bnav-btn" data-tool="rei"      onclick="switchTool('rei')"><span class="bnav-icon">🧠</span>REI</button>
  <button class="bnav-btn" data-tool="ladder"   onclick="switchTool('ladder')"><span class="bnav-icon">🪜</span>Ladder</button>
  <button class="bnav-btn" data-tool="kingdom"  onclick="switchTool('kingdom')"><span class="bnav-icon">✝️</span>Kingdom</button>
  <button class="bnav-btn" data-tool="socratic" onclick="switchTool('socratic')"><span class="bnav-icon">❓</span>Socratic</button>
  <button class="bnav-btn" data-tool="blind"    onclick="switchTool('blind')"><span class="bnav-icon">🔍</span>Blind Spot</button>
</nav>

<!-- Full Council FAB for mobile -->
<button class="fab-council" onclick="runFullCouncil()">⚡ Full Council</button>
```

- [ ] **Step 3: Test on mobile**

Open http://localhost:5000 in Chrome DevTools with mobile viewport (e.g. iPhone 12). Verify:
- Sidebar is hidden
- Bottom nav bar shows 5 tool icons
- Tapping tools switches the active view
- Active tool icon gets the tool's colour
- FAB button shows bottom-right, triggers Full Council
- Thought field shows at top as a sticky bar

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: mobile bottom nav and FAB for Full Council"
```

---

## Task 11: Final wiring — thought pill sync + init

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Update switchTool to sync thought pills**

Find the `function switchTool(tool)` block and update — add `renderThoughtPill` call at end:

```javascript
function switchTool(tool) {
  currentTool = tool;
  document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.className = 'tool-btn';
    if (btn.dataset.tool === tool) btn.classList.add('active', 'active-' + tool);
  });
  document.querySelectorAll('.bnav-btn').forEach(btn => {
    btn.className = 'bnav-btn';
    if (btn.dataset.tool === tool) btn.classList.add('active-' + tool);
  });
  document.querySelectorAll('.tool-view').forEach(v => v.classList.remove('active'));
  const view = document.getElementById('view-' + tool);
  if (view) view.classList.add('active');
  const thought = getThought();
  const inputMap = { rei: 'rei-input', ladder: 'ladder-input', kingdom: 'kingdom-input', blind: 'blind-input' };
  const inputId = inputMap[tool];
  if (inputId) {
    const el = document.getElementById(inputId);
    if (el && !el.value && thought) el.value = thought;
  }
  // update thought pill in the active view
  const pillMap = { rei:'rei-pill', ladder:'ladder-pill', kingdom:'kingdom-pill', blind:'blind-pill', council:'council-pill' };
  if (pillMap[tool]) renderThoughtPill(pillMap[tool]);
}
```

- [ ] **Step 2: Update onThoughtInput to sync pills**

Find `function onThoughtInput()` and add pill sync at end:

```javascript
function onThoughtInput() {
  const val = document.getElementById('global-thought').value;
  const mob = document.getElementById('mobile-thought');
  if (mob) mob.value = val;
  localStorage.setItem('thinkos_thought', val);
  // sync pill in current view
  const pillMap = { rei:'rei-pill', ladder:'ladder-pill', kingdom:'kingdom-pill', blind:'blind-pill', council:'council-pill' };
  if (pillMap[currentTool]) renderThoughtPill(pillMap[currentTool]);
}
```

- [ ] **Step 3: Full end-to-end test**

Test this full flow:
1. Open http://localhost:5000 in a new private window (no localStorage)
2. Type a thought in sidebar
3. Click "REI Council" → should auto-fill and show thought pill
4. Run REI → results appear
5. Click "Blind Spot" → thought pre-filled, run it
6. Click "⚡ Full Council" → all 4 tools run in sequence, synthesis appears
7. Click "Export as Markdown" → file downloads with all results
8. Reload page → thought and session restored, session appears in sidebar
9. Click session in sidebar → restores results
10. Toggle theme → persists on reload
11. Press Cmd+K → focuses thought field
12. Press Escape → closes any open modal
13. Open on mobile viewport → bottom nav visible, FAB visible

- [ ] **Step 4: Final commit**

```bash
git add static/index.html app.py
git commit -m "feat: ThinkOS Sprint 1 complete — sidebar, Full Council, Blind Spot, templates, history, voice, dark mode, keyboard shortcuts, mobile nav"
```

---

## Self-Review

**Spec coverage check:**
- ✅ §1 Sidebar architecture — Tasks 2, 3
- ✅ §2 Global thought field — Task 3 (`getThought()`, `onThoughtInput()`, localStorage)
- ✅ §3 Full Council session — Task 8
- ✅ §4 Workflow Templates — Task 9
- ✅ §5 Save & History — Task 7
- ✅ §6 Blind Spot Detector — Tasks 1, 6
- ✅ §7 Premium Progress Bar — Task 4
- ✅ §8 Dark/Light Mode — Task 3 (`toggleTheme`, CSS variables)
- ✅ §9 Keyboard Shortcuts — Task 3 (`keydown` handler)
- ✅ §10 Mobile Bottom Nav — Task 10
- ✅ Backend: `/api/blindspot`, `/api/synthesis` — Task 1

**No placeholders found.**

**Type consistency:** `lastResults`, `lastInputs`, `socratiMessages`, `currentTool` defined once in Task 3 and used consistently. `callAPI`, `esc`, `getThought` defined once and referenced throughout. `renderREIBody`, `renderLadderBody`, `renderKingdomBody`, `renderBlindBody` defined in Task 8 and used only there.
