# ThinkOS — Dashboard, Daily Workout & Insight Vault
**Date:** 2026-04-25  
**Sub-project:** 1 of 4  
**Status:** Approved for implementation

---

## Overview

This spec covers the first sub-project of the ThinkOS personal thinking OS upgrade:

1. **Personal Thinking Dashboard** — replaces the current home screen with a context-aware, data-rich entry point
2. **Daily Thinking Workout** — a semi-personalised daily challenge card on the dashboard
3. **Insight Vault** — a richer view of the existing memories system with optional enrichment

The existing decision-making tools (lenses, council, journal, planner) are unchanged. This work wraps them in a richer personal context.

---

## 1. Personal Thinking Dashboard

### Replaces
The current home screen (`switchTool('home')`) which shows a blank thought input and lens grid.

### Layout: Command Centre + Personal Greeting

```
┌─────────────────────────────────────────────┐
│  Good morning, John 👋                       │
│  You've been thinking clearly for 7 days.    │
├──────────┬──────────┬──────────┬─────────────┤
│ 23       │ 🔥 7     │ 12       │ 8           │
│ Sessions │ Streak   │ Insights │ Models used │
├─────────────────────────────────────────────┤
│  ⚡ TODAY'S WORKOUT                          │
│  Use Inversion: what would guarantee        │
│  failure for "should I leave my job"?       │
│  [Start workout →]                          │
├─────────────────────────────────────────────┤
│  What's on your mind?                       │
│  [thought input]                            │
│  [quick lens chips: Council · First P · …]  │
├─────────────────────────────────────────────┤
│  RECENT SESSIONS                            │
│  · Should I leave my job? — 2h ago         │
│  · Business idea validation — yesterday    │
├─────────────────────────────────────────────┤
│  LAST INSIGHT                               │
│  "The real cost isn't failure — it's        │
│   staying" → [View Vault]                   │
└─────────────────────────────────────────────┘
```

### Sections

#### Greeting Line
- `"Good [morning/afternoon/evening], [first name] 👋"` — name pulled from `_sbUser.user_metadata.name` or email prefix; time-of-day from `new Date().getHours()`
- Second line: streak message if streak ≥ 2 days, otherwise motivational fallback (`"Ready to think clearly today."`)
- Logged-out fallback: `"Welcome to ThinkOS 👋 — your personal thinking OS"`

#### Stats Bar (4 tiles)
| Tile | Value | Source |
|------|-------|--------|
| Sessions | Count of all saved sessions | `getSessions().length` + cloud sessions |
| Streak | Days in a row with ≥1 session | Computed from session `created_at` dates |
| Insights | Count of memories/insights saved | `getLocalMemories().length` |
| Models used | Count of distinct lens IDs used | Derived from session history |

- Stats are computed client-side from existing localStorage + Supabase data — no new backend required
- Stats bar is read-only (no tap action on tiles in v1)

#### Daily Workout Card
See Section 2.

#### Thought Input
- Identical to the existing `#global-thought` textarea — same element, just repositioned within the dashboard layout
- Quick-lens chips below input: 3 chips showing recommended lenses (from `suggest-lens` API if thought is present, else defaults: `council`, `first_principles`, `inversion`)
- Tapping a chip calls `launchLens(id)` with the current thought — identical to tapping a lens from the home grid

#### Recent Sessions
- Last 3 sessions from `_journalSessions` (already loaded on login)
- Each row: thought truncated to 60 chars + relative timestamp
- Tap → sets `#global-thought` value to the session's thought, then calls `switchTool('journal')` and highlights that session row (same UX as tapping a session in the Journal). Does NOT auto-run any lens.

#### Last Insight Peek
- The single most recently saved memory/insight
- Shows: takeaway text (truncated to 100 chars) + `[View Vault →]` link that `switchTool('vault')`
- Hidden if no insights saved yet

### Implementation Notes
- The dashboard is a new `tool` ID: `'home'` (currently `home` exists but is sparse — we replace its content)
- `switchTool('home')` calls `renderDashboard()` which computes all stats and injects HTML
- `renderDashboard()` is called on login completion and on every `switchTool('home')`
- Streak calculation: iterate session `created_at` dates, count consecutive calendar days ending today. Cached in `localStorage` with a TTL of 1 day.
- No new Supabase tables required for this section

---

## 2. Daily Thinking Workout

### Concept
One mental model challenge per day. Rotating schedule across all 30+ lenses. The challenge is the same for all users on a given day (deterministic by date), but the *situation prompt* is seeded from the user's most recent saved thought.

### Card Behaviour
- Card appears on the dashboard as a distinct, purple-accented section
- Shows: lens name, emoji, the challenge question, and the user's last thought pre-filled
- Primary CTA: `[Start workout →]` → opens the lens runner for that day's lens with the thought pre-filled in `#global-thought`
- If user has already completed today's workout (tracked in localStorage): card shows `✓ Done today` with a summary of what they ran
- Card is always visible regardless of paid status — workout is a free feature

### Daily Lens Rotation
```javascript
const WORKOUT_LENSES = [
  'inversion', 'first_principles', 'stoic', 'premortem', 'feynman',
  'systems', 'regret', 'steelman', 'energy', 'probabilistic',
  'secondorder', 'antifragile', 'future_self', 'kahneman', 'frankl',
  'historical', 'competence', 'naval', 'mentor', 'virtue',
  'memento', 'character', 'mimetic', 'stakeholder', 'legal',
  'medical', 'scientist', 'math_teacher', 'therapist', 'strategist'
];

function getTodaysWorkout() {
  const dayIndex = Math.floor(Date.now() / 86400000); // days since epoch
  const lensId = WORKOUT_LENSES[dayIndex % WORKOUT_LENSES.length];
  return lensId;
}
```

### Challenge Prompts
Each lens in `WORKOUT_LENSES` gets a short, punchy workout prompt. Examples:
- `inversion` → "What would guarantee this fails? List everything."
- `first_principles` → "Strip every assumption. What do you know for certain?"
- `stoic` → "What's in your control here — and what must you release?"
- `premortem` → "It's 12 months from now and it failed. Why?"
- `feynman` → "Explain this like you're teaching a 12-year-old."

Stored as a `WORKOUT_PROMPTS` object in frontend JS.

### Completion Tracking
```javascript
// Mark complete
localStorage.setItem('thinkos_workout_' + getTodayKey(), lensId);

// Check complete
const done = localStorage.getItem('thinkos_workout_' + getTodayKey());
```
Where `getTodayKey()` returns `YYYY-MM-DD` string.

### Situation Seeding
- On card render: pull `getThought()` or last session's thought from `_journalSessions[0]?.thought`
- Display as: `"Apply it to: '[thought truncated to 60 chars]'"`
- Fallback: `"Apply it to your most pressing decision right now"`

---

## 3. Insight Vault

### Concept
A richer view of the existing `memories` table. Memories remain the AI context layer; the Insight Vault is the UI layer on top of them. Users can optionally enrich any memory into a full insight card.

### New Tool: `vault`
- Added to `switchTool()` routing
- Accessible from: dashboard "Last Insight" link, bottom nav (replaces or joins existing nav), sidebar

### Schema Change
Add two optional columns to the `memories` table in Supabase:
```sql
ALTER TABLE memories ADD COLUMN IF NOT EXISTS insight_title TEXT;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS next_action TEXT;
```
Frontend writes these via Supabase JS `.update()`. No backend route needed.

### Card Design: Two States

**Unenriched (auto-saved memory):**
- Dashed purple border
- Shows: lens emoji + name, relative date, takeaway text
- `[+ Enrich →]` button on right → opens inline enrichment form

**Enriched (full insight card):**
- Solid purple border + subtle glow `box-shadow: 0 0 20px rgba(167,139,250,0.08)`
- Shows: `insight_title` (bold), lens + date, takeaway (blockquote style), next_action (green accent box)
- Gold star `✦` badge top-right

### Enrichment Flow
Tapping `[+ Enrich →]` on any card expands an inline form (no modal):
```
Title:       [________________]
Next Action: [________________]
             [Save insight ✓ ]
```
On save: `_sb.from('memories').update({ insight_title, next_action }).eq('id', id)`
Card immediately re-renders as enriched state.

### Vault Layout
- Header: "💡 Insight Vault" + count (`12 insights · 4 enriched`)
- Filter tabs: `All` | `Enriched ✦` | `[lens name]` (dynamic, from distinct lens IDs in memories)
- Cards stack vertically, newest first
- Empty state: "No insights yet. Run a lens and save your takeaway to start building your vault."

### Vault Access
- **v1: sidebar link + "View Vault →" link on dashboard only.** The bottom nav stays at 4 items (Home, Council, Journal, Planner) to avoid mobile crowding. Vault is accessible via the sidebar "More" button and the dashboard insight peek.
- `switchTool('vault')` → calls `renderVault()`

---

## Data Flow Summary

```
Existing Data                    New UI Layer
─────────────                    ────────────
sessions (localStorage+Supabase) → Stats bar, Recent Sessions, Streak
memories (localStorage+Supabase) → Insight Vault cards
                                 → Last Insight peek on dashboard
WORKOUT_LENSES array (JS const)  → Daily Workout card
getTodaysWorkout() (date math)   → Which lens shows today
localStorage workout key         → Completion state
```

---

## What Does NOT Change

- All existing lens tools (REI, Ladder, Kingdom, Blind, Socratic, all extended lenses) — unchanged
- The `switchTool()` navigation pattern — extended, not replaced
- Journal, Planner, Analytics, Help screens — unchanged
- Supabase schema (except two new nullable columns on `memories`)
- The Companion chatbot — unchanged
- Auth, sync, cookie logic — unchanged

---

## Files to Modify

| File | Changes |
|------|---------|
| `static/index.html` | New `renderDashboard()`, `renderVault()` functions; dashboard HTML section; vault HTML section; stats computation; workout card; bottom nav update; CSS for dashboard, stats bar, workout card, insight cards |
| `app.py` | No changes required for this sub-project |
| Supabase (manual) | `ALTER TABLE memories ADD COLUMN insight_title TEXT, next_action TEXT` |

---

## Out of Scope (later sub-projects)

- Applied Mental Model Flow (Sub-project 2)
- AI Mentor Modes (Sub-project 3)
- Search by Problem (Sub-project 3)
- Progressive Mastery stages (Sub-project 4)
- Growth Map visualisation (Sub-project 4)
