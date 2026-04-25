# Applied Mental Model Flow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the 10 core lenses in a guided intake → AI → reflect → rate loop that collects richer context before the AI runs and converts results into committed actions.

**Architecture:** All changes in `static/index.html`. `launchLens()` gains an early-return that shows an inline intake form for core lenses. After the AI result renders, a "Reflect" button is injected. Reflection auto-saves an enriched Vault card, then shows a 👍/👎 clarity rating. No new backend routes. One manual Supabase column (`sessions.clarity BOOLEAN`).

**Tech Stack:** Vanilla JS, CSS custom properties, existing `submitLens()` / `saveMemoryAnchor()` / `injectPostCouncilActions()` patterns, Supabase JS v2.

---

## File Map

| File | What changes |
|------|-------------|
| `static/index.html` | CSS block, `LENS_INTAKE` constant, `_intakeSubmitting` flag, `renderIntakeForm()`, `submitWithIntake()`, `skipIntake()`, modified `launchLens()`, modified `submitLens()`, `injectReflectButton()`, `showReflection()`, `saveReflection()`, `showClarityRating()`, `rateClarity()` |
| Supabase (manual SQL — run once) | `ALTER TABLE sessions ADD COLUMN IF NOT EXISTS clarity BOOLEAN;` |

---

## Codebase Reference

Key locations in `static/index.html`:
- `function launchLens(id)` — line 6778. The function to modify.
- `function activateLens(lensId)` — line 6397. Sets up the lens view + calls `switchTool('lens')`.
- `async function submitLens()` — line 6446. Calls the API and renders the result.
- `function renderLensResult(d, cfg)` — line 6495. Populates panels, synthesis, question, action.
- `function injectPostCouncilActions(resultsWrapId, lensId)` — line 4987. Adds Save/Copy/Export bar.
- `function injectContinueBar(resultsWrapId, lensId)` — line 6808. Adds related lens suggestions.
- `function saveMemoryAnchor(thought, takeaway, tool)` — line 5928. Saves a memory to localStorage + Supabase.
- `window._lastLensResult` — set inside `submitLens()` at line 6532. Holds `{ tool, thought, result }` for the most recent lens run.
- `getLocalMemories()` — returns array from localStorage key `MEMORY_KEY`.
- `MEMORY_KEY` — the localStorage key for memories (search for `MEMORY_KEY =` to find definition).
- `MEMORY_MAX` — max memories to store.
- `_sbUser`, `_sb` — Supabase auth user and client.
- `_journalSessions` — in-memory array of cloud sessions.
- `showToast(msg)` — toast notification helper.
- `esc(t)` — HTML escaping helper.
- `LP_CORE_LENSES`, `getLensById(id)` — lens config lookup.
- CSS insertion point: `/* ── ThinkOS Companion ── */`
- JS insertion point: `// ── ThinkOS Companion ────────────────────────────────────────────────────────`

The `#view-lens` HTML structure (lines 2250–2279):
```html
<div class="tool-view" id="view-lens">
  <div class="tool-header">...</div>
  <div id="lens-pill"></div>
  <button class="btn-submit" id="lens-submit-btn" onclick="submitLens()">Run Lens</button>
  <div class="results-wrap" id="lens-results">
    <div class="lens-panels" id="lens-panels-grid"></div>
    <div class="lens-synthesis" id="lens-synthesis-box">...</div>
    <div class="lens-bottom">...</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <button class="copy-btn" onclick="copyLensResult()">Copy results</button>
      ...
    </div>
  </div>
</div>
```

The intake form is injected AFTER `#lens-submit-btn` (using `insertAdjacentElement('afterend')`).
The reflect button and rating are appended to `#lens-results` by `injectReflectButton()`.

---

## Task 1: CSS — Intake, Reflection, Clarity Rating Styles

**Files:**
- Modify: `static/index.html` — insert CSS before `/* ── ThinkOS Companion ── */`

- [ ] **Step 1: Find insertion point**

Search for:
```css
/* ── ThinkOS Companion ── */
```
Insert ALL CSS from Step 2 IMMEDIATELY BEFORE that line.

- [ ] **Step 2: Insert CSS**

```css
/* ── Lens Intake Form ── */
.lens-intake { padding: 12px 0 4px; }
.lens-intake-subtitle { font-size: 12px; color: #a78bfa; margin-bottom: 14px; font-weight: 600; }
.lens-intake-field { margin-bottom: 12px; }
.lens-intake-label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 5px; }
.lens-intake-input { width: 100%; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 13px; color: var(--text); outline: none; font-family: inherit; box-sizing: border-box; }
.lens-intake-input:focus { border-color: #7c3aed; }
.lens-intake-btn { background: #7c3aed; border: none; color: #fff; border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 700; cursor: pointer; width: 100%; margin-top: 4px; transition: opacity .15s; }
.lens-intake-btn:hover { opacity: .85; }
.lens-intake-skip { display: block; text-align: center; color: var(--muted); font-size: 11px; margin-top: 8px; cursor: pointer; background: none; border: none; font-family: inherit; }
.lens-intake-skip:hover { color: var(--text); }

/* ── Reflection Form ── */
.reflect-wrap { margin-top: 10px; }
.reflect-btn { background: rgba(52,211,153,.12); border: 1px solid rgba(52,211,153,.35); color: #34d399; border-radius: 8px; padding: 8px 14px; font-size: 12px; font-weight: 700; cursor: pointer; transition: background .15s; }
.reflect-btn:hover { background: rgba(52,211,153,.22); }
.reflection-form { background: var(--surface2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.reflection-form-title { font-size: 13px; font-weight: 700; color: #34d399; margin-bottom: 12px; }
.reflection-label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 5px; }
.reflection-input { width: 100%; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-size: 13px; color: var(--text); outline: none; font-family: inherit; box-sizing: border-box; margin-bottom: 10px; }
.reflection-input:focus { border-color: #34d399; }
.reflection-save-btn { background: #34d399; border: none; color: #000; border-radius: 8px; padding: 9px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .15s; }
.reflection-save-btn:hover { opacity: .85; }

/* ── Clarity Rating ── */
.clarity-rating { background: var(--surface2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
.clarity-rating-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.clarity-rating-sub { font-size: 11px; color: var(--muted); margin-bottom: 14px; }
.clarity-btns { display: flex; gap: 10px; justify-content: center; margin-bottom: 10px; }
.clarity-btn { flex: 1; max-width: 130px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px 8px; cursor: pointer; transition: border-color .15s; font-family: inherit; }
.clarity-btn.yes:hover { border-color: #34d399; }
.clarity-btn.no:hover { border-color: #ef4444; }
.clarity-btn-emoji { font-size: 22px; display: block; margin-bottom: 4px; }
.clarity-btn-label { font-size: 11px; font-weight: 600; }
.clarity-btn.yes .clarity-btn-label { color: #34d399; }
.clarity-btn.no .clarity-btn-label { color: #ef4444; }
.clarity-saved-note { font-size: 10px; color: var(--muted); }
```

- [ ] **Step 3: Verify**

In browser DevTools, confirm `.lens-intake`, `.reflection-form`, and `.clarity-rating` all appear in the `<style>` block. No visible change yet.

---

## Task 2: LENS_INTAKE Constant

**Files:**
- Modify: `static/index.html` — insert JS before `// ── ThinkOS Companion ────────────────────────────────────────────────────────`

- [ ] **Step 1: Find insertion point**

Search for:
```javascript
// ── ThinkOS Companion ────────────────────────────────────────────────────────
```
Insert ALL code from Step 2 IMMEDIATELY BEFORE that line.

- [ ] **Step 2: Insert LENS_INTAKE constant**

```javascript
// ── Applied Mental Model Flow ─────────────────────────────────────────────────

const LENS_INTAKE = {
  inversion: [
    { id: 'outcome',     label: 'What outcome do you want?',                         placeholder: 'e.g. Feel confident I made the right call…' },
    { id: 'fear',        label: "What's your biggest fear about this?",               placeholder: "e.g. That I'm making this up to escape…" }
  ],
  first_principles: [
    { id: 'wisdom',      label: "What's the conventional wisdom you've been following?", placeholder: 'e.g. You need 2 years of savings before leaving…' },
    { id: 'constraints', label: 'What constraints feel non-negotiable?',              placeholder: 'e.g. Family, mortgage, health insurance…' }
  ],
  stoic: [
    { id: 'worry',       label: "What's worrying you most?",                          placeholder: 'e.g. Making the wrong call and regretting it…' },
    { id: 'ideal',       label: "What's your ideal outcome?",                         placeholder: 'e.g. Peace of mind whatever I decide…' }
  ],
  premortem: [
    { id: 'plan',        label: "What's the plan you're stress-testing?",             placeholder: 'e.g. Leaving my job in 3 months…' },
    { id: 'deadline',    label: 'When do you need to decide?',                        placeholder: 'e.g. End of this month…' }
  ],
  feynman: [
    { id: 'concept',     label: "What are you trying to understand?",                 placeholder: 'e.g. Why I keep procrastinating on this…' },
    { id: 'gap',         label: 'Where does your explanation break down?',            placeholder: 'e.g. I can explain it to myself but not to others…' }
  ],
  systems: [
    { id: 'system',      label: "What system are you operating in?",                  placeholder: 'e.g. A corporate job with a risk-averse culture…' },
    { id: 'change',      label: "What's changed recently that's causing problems?",   placeholder: 'e.g. New manager, restructure, shifted priorities…' }
  ],
  steelman: [
    { id: 'view',        label: "What's your current view?",                          placeholder: "e.g. I should leave because I'm undervalued…" },
    { id: 'opponent',    label: "Who's most likely to disagree with you?",            placeholder: 'e.g. My partner, my manager, my risk-averse self…' }
  ],
  regret: [
    { id: 'paths',       label: "What are the two paths?",                            placeholder: 'e.g. Stay for another year vs leave now…' },
    { id: 'timeframe',   label: "Are you thinking 1 year or 10 years out?",           placeholder: 'e.g. 10 years — I want to look back with no regrets…' }
  ],
  secondorder: [
    { id: 'decision',    label: "What decision are you about to make?",               placeholder: 'e.g. Accept the offer and give notice…' },
    { id: 'timeline',    label: "What's your timeline?",                              placeholder: 'e.g. Need to decide by Friday…' }
  ],
  future_self: [
    { id: 'stuck',       label: "What are you stuck on?",                             placeholder: 'e.g. Whether to bet on myself or play it safe…' },
    { id: 'horizon',     label: "1 year or 10 years — which timeframe matters most?", placeholder: 'e.g. 10 years — short term pain is acceptable…' }
  ]
};

let _intakeSubmitting = false;
```

- [ ] **Step 3: Verify**

In browser console:
```javascript
console.log(Object.keys(LENS_INTAKE).length); // expect 10
console.log(LENS_INTAKE.inversion[0].label);  // expect "What outcome do you want?"
```

---

## Task 3: launchLens Modification + Intake Form Functions

**Files:**
- Modify: `static/index.html` — two edits

**Edit A — Modify `launchLens` to show intake for core lenses:**

- [ ] **Step 1: Find `launchLens` (around line 6778 — shifts with each task) and add intake check**

Find the exact text:
```javascript
function launchLens(id) {
  const thought = getThought();
```

Replace with:
```javascript
function launchLens(id) {
  // Guided intake for core lenses
  if (LENS_INTAKE[id]) {
    activateLens(id);
    renderIntakeForm(id);
    return;
  }
  const thought = getThought();
```

**Edit B — Add `renderIntakeForm`, `submitWithIntake`, `skipIntake` functions:**

- [ ] **Step 2: Find the insertion point**

These three functions go immediately BEFORE `// ── ThinkOS Companion ────` (same block as LENS_INTAKE from Task 2). Insert immediately after the `let _intakeSubmitting = false;` line added in Task 2.

Find:
```javascript
let _intakeSubmitting = false;
```

Insert this immediately AFTER that line:

```javascript

function renderIntakeForm(lensId) {
  const cfg    = getLensById(lensId) || LP_CORE_LENSES.find(l => l.id === lensId) || { icon: '🧠', name: lensId };
  const fields = LENS_INTAKE[lensId] || [];

  // Hide the native submit button while intake is visible
  const submitBtn = document.getElementById('lens-submit-btn');
  if (submitBtn) submitBtn.style.display = 'none';

  // Remove any previous intake wrap
  document.getElementById('lens-intake-wrap')?.remove();

  const wrap = document.createElement('div');
  wrap.id = 'lens-intake-wrap';
  wrap.className = 'lens-intake';
  wrap.innerHTML = `
    <div class="lens-intake-subtitle">${cfg.icon} ${cfg.name} — Set up your situation <span style="color:var(--muted);font-weight:400">· ~30 seconds</span></div>
    ${fields.map(f => `
      <div class="lens-intake-field">
        <label class="lens-intake-label">${f.label}</label>
        <input class="lens-intake-input" id="intake-${lensId}-${f.id}" placeholder="${f.placeholder}" autocomplete="off" />
      </div>`).join('')}
    <button class="lens-intake-btn" onclick="submitWithIntake('${lensId}')">Run ${esc(cfg.name)} →</button>
    <button class="lens-intake-skip" onclick="skipIntake('${lensId}')">Skip intake →</button>
  `;

  // Inject after the submit button
  if (submitBtn) {
    submitBtn.insertAdjacentElement('afterend', wrap);
  }

  // Focus the first field
  if (fields.length) {
    setTimeout(() => document.getElementById(`intake-${lensId}-${fields[0].id}`)?.focus(), 120);
  }
}

function submitWithIntake(lensId) {
  // Remove intake UI and restore submit button
  document.getElementById('lens-intake-wrap')?.remove();
  const submitBtn = document.getElementById('lens-submit-btn');
  if (submitBtn) submitBtn.style.display = '';

  // Build enriched thought from intake answers
  const fields = LENS_INTAKE[lensId] || [];
  const extras = fields
    .map(f => {
      const val = document.getElementById(`intake-${lensId}-${f.id}`)?.value?.trim();
      return val ? `${f.label}: ${val}` : null;
    })
    .filter(Boolean)
    .join('\n');

  const thought = getThought();
  if (extras) {
    // submitLens() reads getThought() synchronously at its first line — set before calling
    document.getElementById('global-thought').value = `${thought}\n\n---\n${extras}`;
  }

  _intakeSubmitting = true;
  submitLens(); // reads enriched thought synchronously, then goes async
  _intakeSubmitting = false;

  if (extras) {
    // Restore after submitLens has captured the value
    document.getElementById('global-thought').value = thought;
  }
}

function skipIntake(lensId) {
  document.getElementById('lens-intake-wrap')?.remove();
  const submitBtn = document.getElementById('lens-submit-btn');
  if (submitBtn) submitBtn.style.display = '';
  _intakeSubmitting = true;
  submitLens();
  _intakeSubmitting = false;
}
```

- [ ] **Step 3: Verify intake flow in browser**

1. Type a thought in the input box
2. Click "🔃 Inversion" from the lens grid (or run `launchLens('inversion')` in console)
3. Expected: navigates to `#view-lens`, shows intake form with 2 questions, "Run Inversion →" button, "Skip intake →" link. The "Run Lens" button is hidden.
4. Fill in the two fields and click "Run Inversion →"
5. Expected: intake disappears, "Run Lens" button reappears briefly as "Thinking…", result renders normally

Also verify skip works:
```javascript
launchLens('first_principles');
// click "Skip intake →"
// Expected: submitLens fires immediately
```

Also verify expert lenses are unchanged:
```javascript
launchLens('legal');
// Expected: no intake form, goes straight to lens view as before
```

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: lens intake form for 10 core lenses"
```

---

## Task 4: Reflection Button + Form + Save

**Files:**
- Modify: `static/index.html` — two edits

**Edit A — Call `injectReflectButton` from `submitLens` after result renders:**

- [ ] **Step 1: Find the injection point inside `submitLens`**

Find this exact block (inside the `try` block of `submitLens`):
```javascript
    injectContinueBar('lens-results', _activeLens?.id || 'lens');
    injectPostCouncilActions('lens-results', _activeLens || 'lens');
```

Replace with:
```javascript
    injectContinueBar('lens-results', _activeLens?.id || 'lens');
    injectPostCouncilActions('lens-results', _activeLens || 'lens');
    injectReflectButton('lens-results', _activeLens || 'lens');
```

**Edit B — Add reflection functions immediately after `let _intakeSubmitting = false;` block (before `// ── ThinkOS Companion`):**

- [ ] **Step 2: Find the end of `skipIntake` (closes with `}`)**

Insert the following immediately after the closing `}` of `skipIntake`:

```javascript

function injectReflectButton(containerId, lensId) {
  const wrap = document.getElementById(containerId);
  if (!wrap) return;
  wrap.querySelector('.reflect-wrap')?.remove();

  const div = document.createElement('div');
  div.className = 'reflect-wrap';
  div.innerHTML = `<button class="reflect-btn" onclick="showReflection('${lensId}')">✦ Reflect on this →</button>`;
  wrap.appendChild(div);
}

function showReflection(lensId) {
  const wrap = document.querySelector('.reflect-wrap');
  if (!wrap) return;
  wrap.innerHTML = `
    <div class="reflection-form">
      <div class="reflection-form-title">✦ Turn this insight into action</div>
      <label class="reflection-label">What surprised you most?</label>
      <input class="reflection-input" id="reflection-title" placeholder="e.g. I hadn't considered the opportunity cost…" />
      <label class="reflection-label">What will you do this week?</label>
      <input class="reflection-input" id="reflection-action" placeholder="e.g. Have an honest conversation with my manager…" />
      <button class="reflection-save-btn" onclick="saveReflection('${lensId}')">Save to Vault →</button>
    </div>
  `;
  setTimeout(() => document.getElementById('reflection-title')?.focus(), 100);
}

function saveReflection(lensId) {
  const title  = document.getElementById('reflection-title')?.value?.trim()  || '';
  const action = document.getElementById('reflection-action')?.value?.trim() || '';
  if (!title) { showToast('Add a title first'); return; }

  const thought    = getThought();
  const lastResult = window._lastLensResult;
  const takeaway   = (lastResult?.result?.synthesis || lastResult?.result?.action || '').slice(0, 200) || title;

  const mem = {
    id:            Date.now().toString(),
    thought:       thought.slice(0, 200),
    takeaway:      takeaway,
    tool:          lensId,
    insight_title: title,
    next_action:   action || null,
    created_at:    new Date().toISOString()
  };

  // Save to localStorage
  const all = getLocalMemories();
  all.unshift(mem);
  if (all.length > MEMORY_MAX) all.splice(MEMORY_MAX);
  localStorage.setItem(MEMORY_KEY, JSON.stringify(all));

  // Sync to Supabase if logged in
  if (_sbUser) {
    _sb.from('memories').insert({
      user_id:       _sbUser.id,
      thought:       mem.thought,
      takeaway:      mem.takeaway,
      tool:          mem.tool,
      created_at:    mem.created_at,
      insight_title: title,
      next_action:   action || null
    }).catch(e => console.warn('Reflection sync failed:', e));
  }

  showToast('✦ Insight saved to Vault');
  showClarityRating(lensId);
}
```

- [ ] **Step 3: Verify reflection flow**

1. Run any lens (e.g. type a thought, run `launchLens('stoic')` in console, fill intake, submit)
2. Once the result renders, scroll to bottom of `#lens-results`
3. Expected: green "✦ Reflect on this →" button appears below the Save/Copy/Export bar
4. Click it — expected: button replaced by inline reflection form with 2 inputs and "Save to Vault →"
5. Fill in both fields, click "Save to Vault →"
6. Expected: toast "✦ Insight saved to Vault", form replaced by clarity rating UI
7. In console: `getLocalMemories()[0].insight_title` — should equal what you typed

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: reflection form and vault auto-save on lens results"
```

---

## Task 5: Clarity Rating

**Files:**
- Modify: `static/index.html` — add two functions after `saveReflection`

- [ ] **Step 1: Find the end of `saveReflection` function and insert after its closing `}`**

Insert immediately after the closing `}` of `saveReflection`:

```javascript

function showClarityRating(lensId) {
  const wrap = document.querySelector('.reflect-wrap');
  if (!wrap) return;
  wrap.innerHTML = `
    <div class="clarity-rating">
      <div class="clarity-rating-title">Did this help you think more clearly?</div>
      <div class="clarity-rating-sub">Tracks which lenses work best for you over time</div>
      <div class="clarity-btns">
        <button class="clarity-btn yes" onclick="rateClarity('${lensId}', true)">
          <span class="clarity-btn-emoji">👍</span>
          <span class="clarity-btn-label">Yes, clearer</span>
        </button>
        <button class="clarity-btn no" onclick="rateClarity('${lensId}', false)">
          <span class="clarity-btn-emoji">👎</span>
          <span class="clarity-btn-label">Not really</span>
        </button>
      </div>
      <div class="clarity-saved-note">Either way — your vault card is saved ✓</div>
    </div>
  `;
}

function rateClarity(lensId, helpful) {
  // Store locally keyed by timestamp
  const key = 'thinkos_clarity_' + Date.now();
  localStorage.setItem(key, JSON.stringify({ lensId, helpful, ts: Date.now() }));

  // Sync to sessions.clarity in Supabase if logged in
  if (_sbUser && _journalSessions) {
    const recent = _journalSessions.find(s => s.tool === lensId || s.lens_id === lensId);
    if (recent?.id) {
      _sb.from('sessions')
        .update({ clarity: helpful })
        .eq('id', recent.id)
        .eq('user_id', _sbUser.id)
        .catch(e => console.warn('Clarity sync failed:', e));
    }
  }

  // Dismiss rating UI
  const wrap = document.querySelector('.reflect-wrap');
  if (wrap) {
    wrap.innerHTML = `<div style="color:var(--muted);font-size:12px;padding:8px 0;">✓ Thanks — feedback saved</div>`;
  }
}
```

- [ ] **Step 2: Verify clarity rating flow**

1. Complete the full flow: run a lens → fill intake → get result → click "Reflect" → fill form → "Save to Vault →"
2. Expected: reflection form replaced by clarity rating card with 👍 and 👎 buttons
3. Click 👍
4. Expected: card replaced by "✓ Thanks — feedback saved" message
5. In console:
```javascript
// find the clarity localStorage entry
Object.keys(localStorage).filter(k => k.startsWith('thinkos_clarity_'))
// expect one entry
JSON.parse(localStorage.getItem(Object.keys(localStorage).filter(k => k.startsWith('thinkos_clarity_'))[0]))
// expect { lensId: 'stoic', helpful: true, ts: <timestamp> }
```

- [ ] **Step 3: Commit**

```bash
git add static/index.html
git commit -m "feat: clarity rating after reflection saves to localStorage and Supabase"
```

---

## Task 6: Manual Supabase Migration + Final Verification + Push

**Files:**
- Manual SQL via Supabase dashboard
- Git push

- [ ] **Step 1: Run Supabase migration**

Log into Supabase dashboard → SQL Editor → run:
```sql
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS clarity BOOLEAN;
```

Verify:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'clarity';
```
Expected: 1 row returned, type `boolean`.

- [ ] **Step 2: End-to-end test — full guided flow**

1. Open app — dashboard visible ✓
2. Type a thought: "Should I take the job offer?"
3. Click Inversion from the lens grid
4. Expected: navigates to lens view, intake form shows (NOT the AI result immediately)
5. Fill in: outcome = "Feel certain I made the right call", fear = "Leaving security for the unknown"
6. Click "Run Inversion →"
7. Expected: intake disappears, AI result renders with panels and synthesis
8. Scroll to bottom — "✦ Reflect on this →" button visible ✓
9. Click it — reflection form expands ✓
10. Fill in: surprised = "The opportunity cost was invisible to me", action = "List what staying costs me in 1yr/3yr"
11. Click "Save to Vault →"
12. Expected: toast "✦ Insight saved to Vault", clarity rating card appears ✓
13. Click 👍
14. Expected: "✓ Thanks — feedback saved" ✓
15. Navigate to 💡 Insight Vault in sidebar
16. Expected: new enriched card (solid purple border, ✦ star) at top with the title and next action ✓

- [ ] **Step 3: Verify expert lenses unchanged**

Click any expert lens (e.g. "⚖️ Legal"). Expected: no intake form, goes straight to lens view with "Run Lens" button as before.

- [ ] **Step 4: Verify skip works**

Run `launchLens('first_principles')` in console. Click "Skip intake →". Expected: AI runs immediately without intake fields.

- [ ] **Step 5: Push to Railway**

```bash
git push origin main
```

Expected: Railway deploys within 90 seconds.

---

## Self-Review

**Spec coverage check:**
- [x] Intake system (10 core lenses, 2 questions each, skip link) → Tasks 2, 3 ✓
- [x] Expert lenses unchanged → Task 3 (`LENS_INTAKE[id]` guard) ✓
- [x] launchLens wrapping without breaking existing flow → Task 3 ✓
- [x] Reflection button after all lens results → Task 4 ✓
- [x] Reflection auto-saves enriched Vault card → Task 4 `saveReflection` ✓
- [x] Clarity rating 👍/👎 after reflection → Task 5 ✓
- [x] localStorage storage for clarity → Task 5 `rateClarity` ✓
- [x] Supabase sync for clarity (silent fail) → Task 5 ✓
- [x] Manual SQL migration documented → Task 6 ✓
- [x] CSS for all three UI components → Task 1 ✓

**Type/name consistency check:**
- `LENS_INTAKE` — defined Task 2, used Tasks 3, 4 ✓
- `_intakeSubmitting` — defined Task 2, used Task 3 ✓
- `renderIntakeForm(lensId)` — defined Task 3, called from modified `launchLens` Task 3 ✓
- `submitWithIntake(lensId)` — defined Task 3, called from intake HTML Task 3 ✓
- `skipIntake(lensId)` — defined Task 3, called from intake HTML Task 3 ✓
- `injectReflectButton(containerId, lensId)` — defined Task 4, called from `submitLens` Task 4 ✓
- `showReflection(lensId)` — defined Task 4, called from reflect-btn HTML Task 4 ✓
- `saveReflection(lensId)` — defined Task 4, called from reflection form HTML Task 4 ✓
- `showClarityRating(lensId)` — defined Task 5, called from `saveReflection` Task 4 ✓
- `rateClarity(lensId, helpful)` — defined Task 5, called from clarity rating HTML Task 5 ✓
