# Dashboard, Daily Workout & Insight Vault — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a personal thinking dashboard to the ThinkOS home screen, a daily workout card, and an Insight Vault screen — all using existing data with no new backend routes.

**Architecture:** All changes are in `static/index.html`. The dashboard injects content at the TOP of `#view-home` above the existing hero input. A new `#view-vault` tool-view screen handles the Insight Vault. All data comes from existing `getSessions()`, `getLocalMemories()`, and `_journalSessions` — no new Supabase tables except two nullable columns on `memories`.

**Tech Stack:** Vanilla JS, CSS custom properties, Supabase JS v2 (already initialised as `_sb`), existing `switchTool()` / `showToast()` / `launchLens()` patterns.

---

## File Map

| File | What changes |
|------|-------------|
| `static/index.html` | CSS additions, HTML additions to `#view-home`, new `#view-vault` section, new JS functions, `switchTool()` update, sidebar link, `onLogin()` call |
| Supabase (manual SQL — run once) | `ALTER TABLE memories ADD COLUMN IF NOT EXISTS insight_title TEXT, next_action TEXT` |

---

## Task 1: Supabase Schema Migration

**Files:**
- Manual SQL via Supabase dashboard SQL editor

- [ ] **Step 1: Run migration SQL**

Log into Supabase dashboard → SQL Editor → run:

```sql
ALTER TABLE memories ADD COLUMN IF NOT EXISTS insight_title TEXT;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS next_action TEXT;
```

- [ ] **Step 2: Verify columns exist**

In Supabase SQL Editor run:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'memories'
AND column_name IN ('insight_title', 'next_action');
```

Expected: 2 rows returned, both `text` type.

---

## Task 2: CSS — Dashboard + Vault Styles

**Files:**
- Modify: `static/index.html` — insert CSS before the closing `</style>` tag

- [ ] **Step 1: Find insertion point**

Search for this line near the end of the CSS block:
```css
/* ── ThinkOS Companion ── */
```
Insert ALL new CSS BEFORE that line.

- [ ] **Step 2: Add the CSS block**

Insert this entire block before `/* ── ThinkOS Companion ── */`:

```css
/* ── Personal Dashboard ── */
.dashboard-wrap { padding: 0 0 24px; }
.dashboard-greeting { font-size: 22px; font-weight: 800; color: var(--text); margin-bottom: 4px; line-height: 1.2; }
.dashboard-streak-line { font-size: 13px; color: var(--muted); margin-bottom: 16px; }
.dashboard-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 16px; }
.dash-stat { background: var(--surface2); border: 1px solid var(--border); border-radius: 12px; padding: 12px 10px; text-align: center; }
.dash-stat-value { font-size: 22px; font-weight: 800; color: var(--text); line-height: 1; margin-bottom: 4px; }
.dash-stat-label { font-size: 10px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }
@media(max-width:480px) { .dashboard-stats { grid-template-columns: repeat(2, 1fr); } }

/* Daily Workout Card */
.dash-workout { background: linear-gradient(135deg, rgba(124,58,237,.15), rgba(167,139,250,.08)); border: 1px solid rgba(167,139,250,.35); border-radius: 14px; padding: 14px 16px; margin-bottom: 14px; }
.dash-workout-label { font-size: 10px; font-weight: 800; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.dash-workout-lens { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.dash-workout-prompt { font-size: 13px; color: var(--text); line-height: 1.5; margin-bottom: 6px; }
.dash-workout-situation { font-size: 12px; color: var(--muted); font-style: italic; margin-bottom: 12px; }
.dash-workout-btn { background: #7c3aed; border: none; color: #fff; border-radius: 8px; padding: 8px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .15s; }
.dash-workout-btn:hover { opacity: .85; }
.dash-workout-done { font-size: 13px; color: var(--muted); }

/* Recent Sessions on Dashboard */
.dash-section-label { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.dash-section { background: var(--surface2); border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; margin-bottom: 12px; }
.dash-session-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid var(--border); cursor: pointer; transition: color .15s; gap: 8px; }
.dash-session-row:last-child { border-bottom: none; padding-bottom: 0; }
.dash-session-row:hover .dash-session-thought { color: var(--text); }
.dash-session-thought { font-size: 13px; color: #aaa; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dash-session-time { font-size: 11px; color: var(--muted); flex-shrink: 0; }
.dash-empty { font-size: 12px; color: var(--muted); font-style: italic; }

/* Last Insight Peek */
.dash-insight-text { font-size: 13px; color: #aaa; font-style: italic; line-height: 1.5; margin-bottom: 8px; }
.dash-insight-vault-link { background: none; border: none; color: #a78bfa; font-size: 13px; font-weight: 600; cursor: pointer; padding: 0; }
.dash-insight-vault-link:hover { text-decoration: underline; }

/* ── Insight Vault ── */
.vault-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.vault-header-title { font-size: 20px; font-weight: 800; }
.vault-header-count { font-size: 12px; color: var(--muted); margin-bottom: 14px; }
.vault-filters { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.vault-filter { background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; padding: 6px 12px; font-size: 12px; color: var(--muted); cursor: pointer; transition: border-color .15s, color .15s; }
.vault-filter:hover { border-color: #a78bfa; color: #a78bfa; }
.vault-filter.active { background: rgba(167,139,250,.15); border-color: #a78bfa; color: #a78bfa; font-weight: 700; }
.vault-cards { display: flex; flex-direction: column; gap: 12px; }
.vault-empty { font-size: 13px; color: var(--muted); font-style: italic; padding: 24px 0; text-align: center; }

/* Vault card — unenriched */
.vault-card { background: var(--surface2); border: 1px dashed rgba(167,139,250,.4); border-radius: 14px; padding: 16px; position: relative; }
/* Vault card — enriched */
.vault-card.enriched { border-style: solid; border-color: rgba(167,139,250,.6); box-shadow: 0 0 20px rgba(167,139,250,.08); }
.vault-card-star { position: absolute; top: 12px; right: 14px; color: #f59e0b; font-size: 16px; }
.vault-card-meta { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
.vault-card-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 8px; padding-right: 24px; }
.vault-card-takeaway { font-size: 13px; color: #aaa; line-height: 1.6; border-left: 2px solid var(--border); padding-left: 10px; margin-bottom: 10px; }
.vault-card-action { background: rgba(52,211,153,.08); border: 1px solid rgba(52,211,153,.2); border-radius: 8px; padding: 8px 12px; margin-top: 8px; }
.vault-action-label { display: block; font-size: 9px; font-weight: 700; color: #34d399; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
.vault-enrich-btn { background: none; border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; font-size: 12px; color: var(--muted); cursor: pointer; margin-top: 6px; transition: border-color .15s, color .15s; }
.vault-enrich-btn:hover { border-color: #a78bfa; color: #a78bfa; }
.vault-enrich-form { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.vault-enrich-input { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 13px; color: var(--text); outline: none; font-family: inherit; }
.vault-enrich-input:focus { border-color: #7c3aed; }
.vault-save-btn { background: #7c3aed; border: none; color: #fff; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 700; cursor: pointer; align-self: flex-start; }
.vault-save-btn:hover { opacity: .85; }
```

- [ ] **Step 3: Verify in browser**

Open `http://localhost:[port]/` — no visible change yet (no HTML added), but open DevTools → Elements → confirm the new CSS class names exist in the `<style>` block.

---

## Task 3: Dashboard HTML inside `#view-home`

**Files:**
- Modify: `static/index.html` — insert at start of `#view-home` content

- [ ] **Step 1: Find the insertion point**

Locate this exact line in `#view-home`:
```html
      <div class="home-hero">
```

- [ ] **Step 2: Insert dashboard HTML BEFORE `<div class="home-hero">`**

```html
      <!-- ── Personal Dashboard ── -->
      <div class="dashboard-wrap" id="dashboard-wrap">
        <div class="dashboard-greeting" id="dashboard-greeting">Welcome to ThinkOS 👋</div>
        <div class="dashboard-streak-line" id="dashboard-streak-line">Ready to think clearly today.</div>

        <!-- Stats bar -->
        <div class="dashboard-stats">
          <div class="dash-stat">
            <div class="dash-stat-value" id="dashboard-stat-sessions">—</div>
            <div class="dash-stat-label">Sessions</div>
          </div>
          <div class="dash-stat">
            <div class="dash-stat-value" id="dashboard-stat-streak">—</div>
            <div class="dash-stat-label">Streak</div>
          </div>
          <div class="dash-stat">
            <div class="dash-stat-value" id="dashboard-stat-insights">—</div>
            <div class="dash-stat-label">Insights</div>
          </div>
          <div class="dash-stat">
            <div class="dash-stat-value" id="dashboard-stat-models">—</div>
            <div class="dash-stat-label">Models used</div>
          </div>
        </div>

        <!-- Daily Workout -->
        <div class="dash-workout" id="dashboard-workout">
          <div class="dash-workout-label">⚡ TODAY'S WORKOUT</div>
          <div class="dash-workout-lens" id="dash-workout-lens">Loading…</div>
        </div>

        <!-- Recent Sessions -->
        <div class="dash-section-label" style="margin-top:4px;">Recent Sessions</div>
        <div class="dash-section">
          <div id="dashboard-recent"><div class="dash-empty">No sessions yet.</div></div>
        </div>

        <!-- Last Insight Peek -->
        <div id="dashboard-last-insight" style="display:none;">
          <div class="dash-section-label">Last Insight</div>
          <div class="dash-section">
            <div class="dash-insight-text" id="dash-insight-text"></div>
            <button class="dash-insight-vault-link" onclick="switchTool('vault')">View Insight Vault →</button>
          </div>
        </div>

        <div class="home-divider-label" style="margin-top:8px;">Or start a new thought</div>
      </div>
      <!-- end dashboard-wrap -->

```

- [ ] **Step 3: Verify in browser**

Refresh page. The home screen should now show (above the hero input):
- "Welcome to ThinkOS 👋" heading
- A 4-tile stats bar showing `—` values
- A workout card showing "Loading…"
- "Recent Sessions" section (empty state)
- A divider "Or start a new thought"
- Then the existing hero input below

If the layout looks broken, check that you inserted BEFORE `<div class="home-hero">` not inside it.

---

## Task 4: Vault HTML Screen

**Files:**
- Modify: `static/index.html` — add new tool-view after existing tool-views

- [ ] **Step 1: Find insertion point**

Locate this comment in the HTML:
```html
    <!-- ── Account Management Modal ── -->
```

- [ ] **Step 2: Insert vault screen BEFORE that comment**

```html
    <!-- ── Insight Vault ── -->
    <div class="tool-view" id="view-vault">
      <div style="padding: 0 0 32px;">
        <div class="vault-header">
          <div class="vault-header-title">💡 Insight Vault</div>
        </div>
        <div class="vault-header-count" id="vault-header-count">Loading…</div>
        <div class="vault-filters" id="vault-filters"></div>
        <div class="vault-cards" id="vault-cards">
          <div class="vault-empty">Loading insights…</div>
        </div>
      </div>
    </div>

```

- [ ] **Step 3: Verify**

In browser DevTools, confirm `document.getElementById('view-vault')` returns an element (not null).

---

## Task 5: Update `switchTool()` and Sidebar

**Files:**
- Modify: `static/index.html` — `switchTool()` function and sidebar HTML

- [ ] **Step 1: Update `switchTool()` to render dashboard and vault**

Find this block inside `switchTool()`:
```javascript
  if (tool === 'analytics') setTimeout(loadAnalytics,    50);
  if (tool === 'journal')   setTimeout(renderJournal,    50);
  if (tool === 'planner')   setTimeout(renderSavedPlans, 50);
```

Replace with:
```javascript
  if (tool === 'analytics') setTimeout(loadAnalytics,    50);
  if (tool === 'journal')   setTimeout(renderJournal,    50);
  if (tool === 'planner')   setTimeout(renderSavedPlans, 50);
  if (tool === 'home')      setTimeout(renderDashboard,  80);
  if (tool === 'vault')     setTimeout(renderVault,      50);
```

- [ ] **Step 2: Add Vault link to sidebar**

Find this line in the sidebar HTML:
```html
  <button class="btn-templates" onclick="switchTool('analytics')" style="margin-top:4px;">📊 Analytics</button>
```

Add after it:
```html
  <button class="btn-templates" onclick="switchTool('vault')" style="margin-top:4px;">💡 Insight Vault</button>
```

- [ ] **Step 3: Verify routing**

In browser console:
```javascript
switchTool('vault');
```
Expected: The vault screen becomes visible (empty state). No JS errors.

```javascript
switchTool('home');
```
Expected: Home screen visible, no errors (renderDashboard will be called but functions don't exist yet — that's fine, we add them next).

---

## Task 6: Utility Functions

**Files:**
- Modify: `static/index.html` — insert JS functions before the `renderDashboard` call site

- [ ] **Step 1: Find insertion point**

Find this comment in the JS:
```javascript
// ── ThinkOS Companion ────────────────────────────────────────────────────────
```

Insert ALL utility functions BEFORE that comment.

- [ ] **Step 2: Add utility functions**

```javascript
// ── Dashboard Utilities ──────────────────────────────────────────────────────

function _relativeTime(date) {
  const diff = Date.now() - date.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d === 1) return 'yesterday';
  if (d < 7) return `${d} days ago`;
  return date.toLocaleDateString();
}

function _getDashboardGreeting() {
  const h = new Date().getHours();
  const tod = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  let name = '';
  if (_sbUser) {
    name = _sbUser.user_metadata?.full_name || _sbUser.user_metadata?.name || '';
    if (!name && _sbUser.email) name = _sbUser.email.split('@')[0];
    name = name.split(' ')[0]; // first name only
  }
  return name ? `Good ${tod}, ${name} 👋` : `Welcome to ThinkOS 👋`;
}

function _computeStreak() {
  const local = getSessions() || [];
  const cloud = _journalSessions || [];
  const idsSeen = new Set(local.map(s => String(s.id)));
  const all = [...local];
  cloud.forEach(s => { if (!idsSeen.has(String(s.id))) all.push(s); });

  const dates = new Set(
    all
      .filter(s => s.created_at)
      .map(s => new Date(s.created_at).toISOString().slice(0, 10))
  );

  let streak = 0;
  const today = new Date();
  for (let i = 0; i < 365; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    if (dates.has(key)) {
      streak++;
    } else if (i > 0) {
      break; // allow today to be missing (haven't used it yet)
    }
  }
  return streak;
}

function _computeDashboardStats() {
  const local = getSessions() || [];
  const cloud = _journalSessions || [];
  const idsSeen = new Set(local.map(s => String(s.id)));
  const all = [...local];
  cloud.forEach(s => { if (!idsSeen.has(String(s.id))) all.push(s); });

  const sessionCount = all.length;
  const streak = _computeStreak();
  const insightCount = (getLocalMemories() || []).length;
  const modelsUsed = new Set(
    all.map(s => s.tool || s.lens_id).filter(Boolean)
  ).size;

  return { sessionCount, streak, insightCount, modelsUsed };
}
```

- [ ] **Step 3: Verify functions are defined**

In browser console:
```javascript
console.log(_relativeTime(new Date(Date.now() - 3600000))); // expect "1h ago"
console.log(_getDashboardGreeting()); // expect greeting string
console.log(_computeDashboardStats()); // expect object with 4 keys
```

Expected: All three return correct values without errors.

---

## Task 7: Workout Constants and Helpers

**Files:**
- Modify: `static/index.html` — insert immediately after the utilities added in Task 6

- [ ] **Step 1: Add workout constants and helpers immediately after `_computeDashboardStats`**

```javascript
// ── Daily Workout ─────────────────────────────────────────────────────────────

const WORKOUT_LENSES = [
  'inversion','first_principles','stoic','premortem','feynman',
  'systems','regret','steelman','energy','probabilistic',
  'secondorder','antifragile','future_self','kahneman','frankl',
  'historical','competence','naval','mentor','virtue',
  'memento','character','mimetic','stakeholder','legal',
  'medical','scientist','math_teacher','therapist','strategist'
];

const WORKOUT_PROMPTS = {
  inversion:        'What would guarantee this fails? List everything.',
  first_principles: 'Strip every assumption. What do you know for certain?',
  stoic:            "What's in your control here — and what must you release?",
  premortem:        "It's 12 months from now and it failed. Why?",
  feynman:          "Explain this like you're teaching a 12-year-old.",
  systems:          'What feedback loops are running this situation?',
  regret:           'From age 80, which path do you regret more?',
  steelman:         'Build the strongest argument against your current view.',
  energy:           'What charges you here — and what will drain you by month 3?',
  probabilistic:    'Assign honest probabilities to the 3 most likely outcomes.',
  secondorder:      'What happens after what happens? Think 2 steps ahead.',
  antifragile:      'Does this make you stronger when things go wrong — or fragile?',
  future_self:      'What does your 10-year future self want you to know right now?',
  kahneman:         'Which cognitive bias is most distorting your view here?',
  frankl:           'What meaning is available through this difficulty?',
  historical:       'Who has faced this before — and what did they do?',
  competence:       "Are you acting from genuine knowledge — or confidence that isn't earned?",
  naval:            'What is the highest-leverage thing you could do here?',
  mentor:           'What would the wisest version of you say right now?',
  virtue:           'What would a person of excellent character do?',
  memento:          'You will die. Does that change this decision?',
  character:        "What archetype is driving you — and what's the shadow?",
  mimetic:          'Is this your desire — or are you imitating someone?',
  stakeholder:      'Who wins and who loses in each path?',
  legal:            'What rights, risks, and protections are you ignoring?',
  medical:          'What is your body telling you that your mind is ignoring?',
  scientist:        'What is your hypothesis — and how would you test it?',
  math_teacher:     'Define the problem precisely. What do you actually know?',
  therapist:        'What is this situation really about — beneath the surface?',
  strategist:       'What is the highest-leverage strategic move on this board?',
};

function getTodayKey() {
  return new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"
}

function getTodaysWorkout() {
  const dayIndex = Math.floor(Date.now() / 86400000); // days since Unix epoch
  return WORKOUT_LENSES[dayIndex % WORKOUT_LENSES.length];
}

function getWorkoutStatus() {
  return localStorage.getItem('thinkos_workout_' + getTodayKey());
}

function markWorkoutComplete(lensId) {
  localStorage.setItem('thinkos_workout_' + getTodayKey(), lensId);
}

function startDailyWorkout() {
  const lensId = getTodaysWorkout();
  markWorkoutComplete(lensId);
  // Seed thought from last session if input is empty
  if (!getThought()) {
    const last = (_journalSessions || getSessions() || [])[0];
    if (last?.thought) {
      document.getElementById('global-thought').value = last.thought;
    }
  }
  launchLens(lensId);
}
```

- [ ] **Step 2: Verify in console**

```javascript
console.log(getTodaysWorkout());      // e.g. "inversion"
console.log(WORKOUT_PROMPTS[getTodaysWorkout()]); // the prompt string
console.log(getTodayKey());           // "2026-04-25"
console.log(getWorkoutStatus());      // null (not done yet)
```

Expected: All return correct values, no errors.

---

## Task 8: `renderDashboard()` Function

**Files:**
- Modify: `static/index.html` — insert immediately after the workout helpers from Task 7

- [ ] **Step 1: Add `renderDashboard()` immediately after `startDailyWorkout()`**

```javascript
// ── Render Dashboard ──────────────────────────────────────────────────────────

function renderDashboard() {
  // ── Greeting ──
  const greetEl = document.getElementById('dashboard-greeting');
  const streakLineEl = document.getElementById('dashboard-streak-line');
  if (greetEl) greetEl.textContent = _getDashboardGreeting();

  // ── Stats ──
  const stats = _computeDashboardStats();
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('dashboard-stat-sessions', stats.sessionCount || 0);
  set('dashboard-stat-streak',   stats.streak > 0 ? '🔥' + stats.streak : stats.streak);
  set('dashboard-stat-insights', stats.insightCount || 0);
  set('dashboard-stat-models',   stats.modelsUsed || 0);
  if (streakLineEl) {
    streakLineEl.textContent = stats.streak >= 2
      ? `You've been thinking clearly for ${stats.streak} days.`
      : 'Ready to think clearly today.';
  }

  // ── Workout card ──
  const workoutEl = document.getElementById('dashboard-workout');
  if (workoutEl) {
    const lensId     = getTodaysWorkout();
    const cfg        = getLensById(lensId) || LP_CORE_LENSES.find(l => l.id === lensId) || { id: lensId, name: lensId, icon: '🧠' };
    const prompt     = WORKOUT_PROMPTS[lensId] || 'Apply this lens to your most pressing decision.';
    const done       = !!getWorkoutStatus();
    const rawThought = getThought() || ((_journalSessions || getSessions() || [])[0]?.thought || '');
    const situation  = rawThought
      ? `Apply it to: "${rawThought.slice(0, 60)}${rawThought.length > 60 ? '…' : ''}"`
      : 'Apply it to your most pressing decision right now.';

    if (done) {
      workoutEl.innerHTML = `
        <div class="dash-workout-label">⚡ TODAY'S WORKOUT</div>
        <div class="dash-workout-done">✓ Done today &nbsp;·&nbsp; <span style="color:var(--muted)">${cfg.icon} ${cfg.name}</span></div>`;
    } else {
      workoutEl.innerHTML = `
        <div class="dash-workout-label">⚡ TODAY'S WORKOUT</div>
        <div class="dash-workout-lens">${cfg.icon} ${cfg.name}</div>
        <div class="dash-workout-prompt">${esc(prompt)}</div>
        <div class="dash-workout-situation">${esc(situation)}</div>
        <button class="dash-workout-btn" onclick="startDailyWorkout()">Start workout →</button>`;
    }
  }

  // ── Recent sessions ──
  const recentEl = document.getElementById('dashboard-recent');
  if (recentEl) {
    const all = [...(_journalSessions || [])];
    // merge local sessions not already in cloud list
    const cloudIds = new Set(all.map(s => String(s.id)));
    (getSessions() || []).forEach(s => { if (!cloudIds.has(String(s.id))) all.push(s); });
    const recent = all.slice(0, 3);

    if (!recent.length) {
      recentEl.innerHTML = '<div class="dash-empty">No sessions yet. Run your first lens above.</div>';
    } else {
      recentEl.innerHTML = recent.map(s => {
        const thought  = (s.thought || '').slice(0, 60);
        const ellipsis = (s.thought || '').length > 60 ? '…' : '';
        const time     = s.created_at ? _relativeTime(new Date(s.created_at)) : '';
        const sid      = JSON.stringify(String(s.id));
        return `<div class="dash-session-row" onclick="dashOpenSession(${sid})">
          <span class="dash-session-thought">${esc(thought)}${ellipsis}</span>
          <span class="dash-session-time">${time}</span>
        </div>`;
      }).join('');
    }
  }

  // ── Last insight peek ──
  const insightWrap = document.getElementById('dashboard-last-insight');
  const insightText = document.getElementById('dash-insight-text');
  const memories = getLocalMemories() || [];
  if (insightWrap && memories.length > 0) {
    const last = memories[0];
    const preview = (last.takeaway || '').slice(0, 100);
    const ellipsis = (last.takeaway || '').length > 100 ? '…' : '';
    if (insightText) insightText.textContent = `"${preview}${ellipsis}"`;
    insightWrap.style.display = 'block';
  } else if (insightWrap) {
    insightWrap.style.display = 'none';
  }
}

function dashOpenSession(id) {
  // Set the thought in the global input then go to journal
  const all = [...(_journalSessions || []), ...(getSessions() || [])];
  const session = all.find(s => String(s.id) === String(id));
  if (session?.thought) {
    document.getElementById('global-thought').value = session.thought;
  }
  switchTool('journal');
}
```

- [ ] **Step 2: Trigger a manual render and verify**

In browser console:
```javascript
renderDashboard();
```

Expected result:
- Greeting changes from "Welcome to ThinkOS 👋" to a personalised greeting (or logged-out fallback)
- Stats tiles show real numbers (0 if no data)
- Workout card shows today's lens name and prompt
- Recent sessions shows last 3 or empty state
- Last insight peek shows if any memories exist

No JS errors in console.

---

## Task 9: Vault Render Functions

**Files:**
- Modify: `static/index.html` — insert after `dashOpenSession()` from Task 8

- [ ] **Step 1: Add vault state and all render functions**

```javascript
// ── Insight Vault ─────────────────────────────────────────────────────────────

let _vaultFilter = 'all';

function setVaultFilter(f) {
  _vaultFilter = f;
  renderVault();
}

function renderVault() {
  const memories = getLocalMemories() || [];
  const enrichedCount = memories.filter(m => m.insight_title).length;

  // Header count
  const countEl = document.getElementById('vault-header-count');
  if (countEl) {
    countEl.textContent = `${memories.length} insight${memories.length !== 1 ? 's' : ''} saved · ${enrichedCount} enriched`;
  }

  // Filter tabs
  const filterEl = document.getElementById('vault-filters');
  if (filterEl) {
    const lensIds = [...new Set(memories.map(m => m.tool).filter(Boolean))];
    filterEl.innerHTML = [
      `<button class="vault-filter ${_vaultFilter === 'all' ? 'active' : ''}" onclick="setVaultFilter('all')">All</button>`,
      `<button class="vault-filter ${_vaultFilter === 'enriched' ? 'active' : ''}" onclick="setVaultFilter('enriched')">Enriched ✦</button>`,
      ...lensIds.map(id => {
        const cfg = getLensById(id) || LP_CORE_LENSES.find(l => l.id === id) || { icon: '🔭', name: id };
        return `<button class="vault-filter ${_vaultFilter === id ? 'active' : ''}" onclick="setVaultFilter('${id}')">${cfg.icon} ${cfg.name}</button>`;
      })
    ].join('');
  }

  // Filter memories
  let filtered = memories;
  if (_vaultFilter === 'enriched') {
    filtered = memories.filter(m => m.insight_title);
  } else if (_vaultFilter !== 'all') {
    filtered = memories.filter(m => m.tool === _vaultFilter);
  }

  // Cards
  const cardsEl = document.getElementById('vault-cards');
  if (!cardsEl) return;

  if (!filtered.length) {
    cardsEl.innerHTML = `<div class="vault-empty">${
      memories.length === 0
        ? 'No insights yet. Run a lens and save your takeaway to start building your vault.'
        : 'No insights match this filter.'
    }</div>`;
    return;
  }

  cardsEl.innerHTML = filtered.map(m => _renderVaultCard(m)).join('');
}

function _renderVaultCard(m) {
  const cfg  = getLensById(m.tool) || LP_CORE_LENSES.find(l => l.id === m.tool) || { icon: '🔭', name: m.tool || 'Lens' };
  const date = m.created_at ? _relativeTime(new Date(m.created_at)) : '';
  const id   = String(m.id);

  if (m.insight_title) {
    return `<div class="vault-card enriched" id="vault-card-${id}">
      <div class="vault-card-star">✦</div>
      <div class="vault-card-meta">${cfg.icon} ${cfg.name} · ${date}</div>
      <div class="vault-card-title">${esc(m.insight_title)}</div>
      <div class="vault-card-takeaway">${esc(m.takeaway || '')}</div>
      ${m.next_action ? `<div class="vault-card-action"><span class="vault-action-label">Next Action</span>${esc(m.next_action)}</div>` : ''}
    </div>`;
  }

  return `<div class="vault-card" id="vault-card-${id}">
    <div class="vault-card-meta">${cfg.icon} ${cfg.name} · ${date}</div>
    <div class="vault-card-takeaway">${esc(m.takeaway || '')}</div>
    <button class="vault-enrich-btn" onclick="openEnrichForm('${id}')">+ Enrich →</button>
    <div class="vault-enrich-form" id="vault-enrich-form-${id}" style="display:none;">
      <input class="vault-enrich-input" id="vault-title-${id}" placeholder="Title for this insight…" />
      <input class="vault-enrich-input" id="vault-action-${id}" placeholder="Next action (optional)…" />
      <button class="vault-save-btn" onclick="saveEnrichment('${id}')">Save insight ✓</button>
    </div>
  </div>`;
}
```

- [ ] **Step 2: Verify vault renders**

In browser console:
```javascript
switchTool('vault');
```
Expected: Vault screen shows. If memories exist, cards display. If none, shows empty state message.

```javascript
// Verify filter works
setVaultFilter('enriched');
```
Expected: Only enriched cards shown (or "No insights match this filter").

---

## Task 10: Enrichment Functions

**Files:**
- Modify: `static/index.html` — insert immediately after `_renderVaultCard()`

- [ ] **Step 1: Add enrichment functions**

```javascript
function openEnrichForm(id) {
  const form = document.getElementById(`vault-enrich-form-${id}`);
  if (!form) return;
  const isOpen = form.style.display !== 'none';
  form.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) {
    document.getElementById(`vault-title-${id}`)?.focus();
  }
}

async function saveEnrichment(id) {
  const titleEl  = document.getElementById(`vault-title-${id}`);
  const actionEl = document.getElementById(`vault-action-${id}`);
  const title    = titleEl?.value?.trim() || '';
  const action   = actionEl?.value?.trim() || '';

  if (!title) { showToast('Add a title first'); return; }

  // 1. Update localStorage
  const memories = getLocalMemories();
  const idx = memories.findIndex(m => String(m.id) === String(id));
  if (idx !== -1) {
    memories[idx].insight_title = title;
    memories[idx].next_action   = action;
    localStorage.setItem(MEMORY_KEY, JSON.stringify(memories));
  }

  // 2. Update Supabase if logged in
  if (_sbUser) {
    const numId = parseInt(id, 10);
    if (!isNaN(numId)) {
      await _sb.from('memories')
        .update({ insight_title: title, next_action: action })
        .eq('id', numId)
        .eq('user_id', _sbUser.id)
        .catch(e => console.warn('Vault enrichment sync failed:', e));
    }
  }

  showToast('✦ Insight enriched!', 2000);
  renderVault();
}
```

- [ ] **Step 2: End-to-end enrichment test**

1. Navigate to vault: `switchTool('vault')`
2. If no memories exist, save one: go to home, type a thought, run First Principles, save takeaway
3. Return to vault: `switchTool('vault')`
4. Click `+ Enrich →` on a card — form should expand
5. Type a title and click `Save insight ✓`
6. Expected: Card re-renders as enriched (solid border, gold star, title shown)
7. In console: `getLocalMemories()[0].insight_title` should equal the title you typed

---

## Task 11: Wire Dashboard to `onLogin()` and Initial Load

**Files:**
- Modify: `static/index.html` — `onLogin()` function

- [ ] **Step 1: Find the onLogin function**

Locate the end of `onLogin()` — find:
```javascript
    if (currentTool === 'journal') renderJournal();
```

- [ ] **Step 2: Add dashboard render call**

Replace that line with:
```javascript
    if (currentTool === 'journal') renderJournal();
    if (currentTool === 'home')    renderDashboard();
```

- [ ] **Step 3: Also trigger on page load for logged-in users**

Find:
```javascript
let currentTool = 'rei';
```

Replace with:
```javascript
let currentTool = 'home';
```

This makes the home/dashboard the initial screen instead of REI.

Also find:
```javascript
function switchTool(tool) {
  currentTool = tool;
```

And confirm the `switchTool('home')` call at startup will trigger `renderDashboard()` via the `setTimeout(renderDashboard, 80)` added in Task 5. *(This is already handled — no further change needed.)*

- [ ] **Step 4: Verify initial load**

Hard-refresh the page (Ctrl+Shift+R). Expected:
- Home dashboard loads immediately with real stats and workout card
- Logged-in user sees personalised greeting
- Logged-out user sees "Welcome to ThinkOS 👋"
- No JS errors in console

---

## Task 12: Final Integration Verification

- [ ] **Step 1: Test dashboard flow end-to-end**

1. Open app — dashboard visible as first screen ✓
2. Stats show correct numbers ✓
3. Workout card shows today's lens with correct prompt ✓
4. Click "Start workout →" — lens opens with thought pre-filled (if any) ✓
5. Return home — workout card shows "✓ Done today" ✓

- [ ] **Step 2: Test vault flow end-to-end**

1. Click sidebar → 💡 Insight Vault ✓
2. All saved memories display as cards ✓
3. Filter tabs work (All / Enriched ✦) ✓
4. Click `+ Enrich →`, fill form, save — card becomes enriched ✓
5. Return to home — Last Insight peek shows latest memory ✓

- [ ] **Step 3: Test responsive layout**

Resize browser to 375px wide (iPhone). Verify:
- Stats bar shows 2×2 grid (not 4 in a row) ✓
- Workout card readable ✓
- Vault cards stack cleanly ✓

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: personal dashboard, daily workout, and insight vault"
git push origin main
```

Expected: Railway deploys within 90 seconds. Hard refresh live URL to verify.

---

## Self-Review Checklist

- [x] Spec section 1 (Dashboard): Tasks 2, 3, 6, 7, 8, 11 ✓
- [x] Spec section 2 (Daily Workout): Tasks 7, 8 ✓
- [x] Spec section 3 (Insight Vault): Tasks 1, 2, 4, 5, 9, 10 ✓
- [x] No placeholders — all code is complete ✓
- [x] All function names consistent across tasks (`renderDashboard`, `renderVault`, `_renderVaultCard`, `saveEnrichment`, `openEnrichForm`, `startDailyWorkout`, `dashOpenSession`) ✓
- [x] `esc()` used wherever user content is injected into HTML ✓
- [x] `MEMORY_KEY` referenced — confirmed defined at line 5788 in the file ✓
- [x] `LP_CORE_LENSES` referenced in vault render — confirmed defined in LENS_CONFIG section ✓
