# ThinkOS Sprint 1 — Design Spec
**Date:** 2026-04-16  
**Scope:** Full UI rebuild + 10 new features  
**Target:** Single-file SPA (`static/index.html`) + minor `app.py` additions

---

## Overview

ThinkOS currently has 4 tools in a tab layout. Sprint 1 transforms it into an OS-feeling app with a persistent sidebar, a new Full Council mode, saved history, and 6 UX upgrades. Everything stays in a single HTML file + Flask backend — no build toolchain, no frameworks.

---

## 1. Layout — Sidebar Architecture

Replace the current top-tab layout with a **two-panel layout**:

### Left sidebar (240px, fixed)
Top to bottom:
1. **Logo** — "Think**OS**" with purple accent
2. **Current Thought** label + textarea (auto-grows, ~80px min)
3. **⚡ Full Council** button (primary CTA — purple)
4. **🎙️ Voice input** mic icon button (inline with thought field)
5. Divider
6. **Tools** label + tool nav buttons (stacked, full-width):
   - REI Council
   - The Ladder
   - Kingdom Lens
   - Socratic
   - 🔍 Blind Spot *(new)*
7. Divider
8. **📋 Templates** button (ghost style, opens modal)
9. Divider
10. **Recent Sessions** label + list of saved sessions (clickable)
11. Bottom: **🌓 theme toggle** icon (dark/light)

### Right main area (flex: 1)
- Shows the active tool's output
- No tabs — tool switching happens via sidebar nav
- Active tool label shown at top of main area
- Thought is "locked in" from sidebar — shown as a read-only pill at top of main, with a subtle 🔒 icon and "edit" link that focuses the sidebar textarea

### Mobile (< 640px)
- Sidebar collapses to a **bottom navigation bar** (fixed, 5 icons: REI, Ladder, Kingdom, Socratic, Blind Spot)
- Thought field moves to top of main area as a collapsible bar
- Full Council and Templates accessible via a "⋯" menu button in bottom nav

---

## 2. Global "Current Thought" Field

- Single textarea in the sidebar — the source of truth for all tools
- When user switches tools, the thought is pre-filled automatically
- Shows a subtle "feeds all tools" hint on first visit
- Persists to `localStorage` so it survives page refresh
- Voice input button (🎙️) sits inline — click to start Web Speech API dictation, click again to stop. Appends to existing text.

---

## 3. Full Council Session

### Trigger
- "⚡ Full Council" button in sidebar

### Sequence
Runs all 4 tools in order: REI → Ladder → Kingdom Lens → Blind Spot  
(Socratic is conversational so excluded from auto-sequence)

### Progress UI
- Premium animated progress bar replaces the spinner (see §7)
- Shows which tool is currently running: "Consulting REI Council... (1/4)"

### Report Layout
The main area switches to "Full Council" view:

**Top — Synthesis card** (new `/api/synthesis` endpoint):
- AI reads all 4 results and writes a 3–4 sentence synthesis paragraph
- Ends with one sharp synthesis question
- Styled with gradient background (dark purple → dark teal)

**Below — Full detail sections**, each collapsible:
1. **REI Council** — full 3 mind cards + majority + alignment badge + action question
2. **The Ladder** — full rung visual + above/current/below views + ascent question
3. **Kingdom Lens** — full 4 lens cards + biblical analogy + scripture cards + kingdom question
4. **Blind Spot** — full output (see §6)

**Bottom** — "Export as Markdown" button + "Share" button

### New backend endpoint
```
POST /api/synthesis
Body: { rei: {...}, ladder: {...}, kingdom: {...}, blind_spot: {...} }
Returns: { synthesis: "...", synthesis_question: "..." }
```

---

## 4. Workflow Templates

### Trigger
"📋 Templates" button in sidebar → opens modal overlay

### Modal design
- Full-screen dark overlay
- Centered card (max 560px wide)
- Title: "Choose a Thinking Template"
- Subtitle: "Pre-built sequences for common situations"
- 6 template cards in a 2-column grid:

| Template | Tools | Description |
|---|---|---|
| 🔮 Big Life Decision | REI → Ladder → Kingdom → Blind Spot | Major choices with long-term consequences |
| ⚡ Conflict with Someone | REI → Socratic | Tension or breakdown in a relationship |
| 🎨 Creative Block | Ladder → Socratic | Stuck on a project or creative decision |
| ✝️ Spiritual Discernment | Kingdom → Socratic | Faith-based direction and calling |
| 🧠 Pressure Test an Idea | REI → Blind Spot | Challenge an idea before committing |
| 💬 Hard Conversation | REI → Socratic | Preparing for a difficult talk |

### Behaviour
- Click a template card → modal closes, template name shown in sidebar, thought field focused
- If thought field already has content → runs Full Council with the template's tool sequence
- If thought field is empty → shows placeholder hint text matching the template

---

## 5. Save & History

### Storage
- `localStorage` key: `thinkos_sessions`
- Each session: `{ id, title, thought, timestamp, results: { rei?, ladder?, kingdom?, blind_spot?, synthesis? } }`
- Title: auto-generated from first 40 chars of thought
- Max 50 sessions stored (oldest pruned)

### UI
- Sidebar "Recent Sessions" list shows last 8 sessions
- Click → restores thought + all results instantly (no API call)
- Hover → shows delete (×) button
- "View all" link → opens sessions modal with full list + search

### Export
- "Export as Markdown" button on Full Council report generates clean `.md` file and triggers browser download
- Format: thought as H1, each tool section with headers, scripture as blockquotes

---

## 6. Blind Spot Detector (New Tool)

### Purpose
Takes the current thought + any existing tool results and asks: "What perspective is completely missing here?"

### Backend
```
POST /api/blindspot
Body: { situation: "...", context?: "rei + ladder summaries if available" }
Returns: { missing_perspective: "...", why_its_missing: "...", reframe: "...", blind_spot_question: "..." }
```

### Prompt design
- Forced to identify ONE specific missing angle (not generic "consider all sides" advice)
- Cross-references REI results if available: "Instinct and Reason both said X — what's neither seeing?"
- Returns: missing perspective, why it's being avoided/missed, a reframe, and one sharp question

### UI
- Same card pattern as other tools
- 3 cards: Missing Perspective / Why It's Blind / The Reframe
- Bottom: blind spot question (styled like action_question)

---

## 7. Premium Progress Bar

Replace the current spinner with:
- Full-width animated gradient bar at top of main area
- Gradient cycles through the active tool's colour
- Underneath: mode-specific loading messages cycle every 1.2s (existing system, kept)
- Bar animates from 0% → 85% during the call, then snaps to 100% on completion and fades out
- Subtle glow effect matching tool colour

---

## 8. Dark / Light Mode Toggle

- Default: dark (current theme)
- Toggle: 🌓 icon button at bottom of sidebar
- Light theme: off-white background (`#f8f7f4`), dark text, muted tool colours
- System preference: detected via `prefers-color-scheme` on first load
- Persisted to `localStorage` key `thinkos_theme`
- CSS: swap via `data-theme="light"` on `<html>` element, all colours as CSS variables (already are)

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl + Enter` | Submit current tool |
| `Cmd/Ctrl + K` | Focus thought field (from anywhere) |
| `Cmd/Ctrl + Shift + F` | Trigger Full Council |
| `Cmd/Ctrl + 1–5` | Switch tools (1=REI, 2=Ladder, 3=Kingdom, 4=Socratic, 5=Blind Spot) |
| `Escape` | Close any open modal |

- Subtle keyboard shortcut hints shown on hover for main buttons
- First-visit tooltip: "Press ⌘K to focus your thought from anywhere"

---

## 10. Mobile Bottom Nav

On screens < 640px:
- Fixed bottom bar (60px tall, full width, dark surface)
- 5 icon+label buttons: REI, Ladder, Kingdom, Socratic, Blind Spot
- Active tool highlighted with tool colour
- Thought field: sticky bar below the header, collapsible (tap to expand)
- Full Council: prominent floating button (bottom-right FAB, purple)
- Templates: accessible via long-press or ⋯ menu

---

## Backend Changes

### New endpoints
1. `POST /api/synthesis` — reads all tool results, returns synthesis paragraph + question
2. `POST /api/blindspot` — returns missing perspective analysis

### No changes to existing endpoints
`/api/rei`, `/api/ladder`, `/api/kingdom`, `/api/socratic` unchanged.

---

## File Structure (unchanged)
```
think-os/
├── app.py              # + 2 new endpoints + SYNTHESIS_PROMPT + BLINDSPOT_PROMPT
├── static/
│   └── index.html      # Full rewrite — sidebar layout + all features
├── .env
└── requirements.txt    # unchanged
```

---

## Out of Scope (Sprint 2)
- Shareable result cards (image export)
- Public API / embed endpoint
- Cloud save (Supabase)
- Public Think Gallery

---

## Success Criteria
- [ ] Sidebar layout works on desktop and mobile
- [ ] Global thought field feeds all tools automatically
- [ ] Full Council runs all 4 tools and shows synthesis + full detail
- [ ] Templates modal opens, selecting one pre-fills and runs
- [ ] Sessions saved to localStorage, restorable from sidebar
- [ ] Blind Spot Detector returns unique, specific insight
- [ ] Progress bar replaces spinner, feels premium
- [ ] Dark/light toggle persists across refresh
- [ ] All keyboard shortcuts work
- [ ] Mobile bottom nav replaces sidebar on small screens
- [ ] Export to Markdown works
