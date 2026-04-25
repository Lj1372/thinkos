# ThinkOS — Applied Mental Model Flow
**Date:** 2026-04-25
**Sub-project:** 2 of 4
**Status:** Approved for implementation

---

## Overview

Sub-project 2 transforms the current lens experience from a one-shot query into a guided three-part loop: intake before the AI runs, reflection after the result, and a clarity rating at the end. The goal is to make each lens session feel like a complete thinking session — richer input going in, committed action coming out, and a data trail that shows whether the app is actually improving the user's decision-making over time.

The existing lens tools are unchanged. This work wraps them in a guided flow.

---

## What Changes vs What Stays

**Stays the same:**
- All lens tools (REI, Ladder, Kingdom, Blind, Socratic, all expert lenses, all extended lenses)
- The `launchLens(id)` call signature
- The AI prompt/API pipeline
- The existing "Save takeaway" button on results
- Expert lenses (legal, medical, therapist, etc.) — they keep the current direct-launch flow

**Changes:**
- Core 10 lenses get an intake form shown before the AI runs
- A "Reflect on this →" button is added to all lens results
- A clarity rating (👍 / 👎) appears after saving a reflection
- One new nullable `clarity` column on the `sessions` Supabase table

---

## 1. Intake System

### Trigger
When `launchLens(id)` is called for one of the 10 core lenses, the intake form renders inside the existing lens panel instead of immediately submitting to the AI. For all other lenses, behaviour is unchanged.

### Core Lenses With Intake
```javascript
const LENS_INTAKE = {
  inversion: [
    { id: 'outcome',  label: 'What outcome do you want?',                    placeholder: 'e.g. Feel confident I made the right call…' },
    { id: 'fear',     label: "What's your biggest fear about this?",          placeholder: 'e.g. That I'm making this up to escape…' }
  ],
  first_principles: [
    { id: 'wisdom',   label: "What's the conventional wisdom you've been following?", placeholder: 'e.g. You need 2 years of savings before leaving…' },
    { id: 'constraints', label: 'What constraints feel non-negotiable?',      placeholder: 'e.g. Family, mortgage, health insurance…' }
  ],
  stoic: [
    { id: 'worry',    label: "What's worrying you most?",                     placeholder: 'e.g. Making the wrong call and regretting it…' },
    { id: 'ideal',    label: "What's your ideal outcome?",                    placeholder: 'e.g. Peace of mind whatever I decide…' }
  ],
  premortem: [
    { id: 'plan',     label: "What's the plan you're stress-testing?",        placeholder: 'e.g. Leaving my job in 3 months…' },
    { id: 'deadline', label: 'When do you need to decide?',                   placeholder: 'e.g. End of this month…' }
  ],
  feynman: [
    { id: 'concept',  label: "What are you trying to understand?",            placeholder: 'e.g. Why I keep procrastinating on this…' },
    { id: 'gap',      label: 'Where does your explanation break down?',       placeholder: 'e.g. I can explain it to myself but not to others…' }
  ],
  systems: [
    { id: 'system',   label: "What system are you operating in?",             placeholder: 'e.g. A corporate job with a risk-averse culture…' },
    { id: 'change',   label: "What's changed recently that's causing problems?", placeholder: 'e.g. New manager, restructure, shifted priorities…' }
  ],
  steelman: [
    { id: 'view',     label: "What's your current view?",                     placeholder: 'e.g. I should leave because I'm undervalued…' },
    { id: 'opponent', label: "Who's most likely to disagree with you?",       placeholder: 'e.g. My partner, my manager, my risk-averse self…' }
  ],
  regret: [
    { id: 'paths',    label: "What are the two paths?",                       placeholder: 'e.g. Stay for another year vs leave now…' },
    { id: 'timeframe',label: "Are you thinking 1 year or 10 years out?",      placeholder: 'e.g. 10 years — I want to look back with no regrets…' }
  ],
  secondorder: [
    { id: 'decision', label: "What decision are you about to make?",          placeholder: 'e.g. Accept the offer and give notice…' },
    { id: 'timeline', label: "What's your timeline?",                         placeholder: 'e.g. Need to decide by Friday…' }
  ],
  future_self: [
    { id: 'stuck',    label: "What are you stuck on?",                        placeholder: 'e.g. Whether to bet on myself or play it safe…' },
    { id: 'horizon',  label: "1 year or 10 years — which timeframe matters most?", placeholder: 'e.g. 10 years — short term pain is acceptable…' }
  ]
};
```

### Intake UI
- Renders inside the existing `.lens-panel` for that lens — no new screen, no modal
- Shows: lens icon + name, "Set up your situation — 30 seconds" subtitle, 1–2 input fields, "Run [Lens Name] →" button
- Styled consistently with the existing dark UI (same input style as vault enrich form)
- Skip link: small "Skip intake →" text link below the button for users who want to go straight to the result

### How Intake Answers Reach the AI
`launchLens` is overridden using a closure pattern to intercept core lens launches. A `_intakeSubmitting` flag prevents recursion:

```javascript
// Override launchLens to add intake for core lenses
const _launchLensOriginal = launchLens;
launchLens = function(id) {
  if (LENS_INTAKE[id] && !_intakeSubmitting) {
    renderIntakeForm(id);
  } else {
    _launchLensOriginal(id);
  }
};
```

`submitWithIntake(lensId)` reads the intake field values, temporarily enriches the thought, calls the original `launchLens`, then restores the thought:

```javascript
let _intakeSubmitting = false;

function submitWithIntake(lensId) {
  const fields = LENS_INTAKE[lensId] || [];
  const extras = fields
    .map(f => {
      const val = document.getElementById(`intake-${lensId}-${f.id}`)?.value?.trim();
      return val ? `${f.label}: ${val}` : null;
    })
    .filter(Boolean)
    .join('\n');

  const thought = getThought();
  const enriched = extras ? `${thought}\n\n---\n${extras}` : thought;
  document.getElementById('global-thought').value = enriched;
  _intakeSubmitting = true;
  launchLens(lensId); // calls _launchLensOriginal via the override
  _intakeSubmitting = false;
  document.getElementById('global-thought').value = thought; // restore original
}
```

The original thought is restored after submission so the enriched context doesn't pollute the UI.

---

## 2. Reflection System

### Trigger
After any lens result renders, a **"Reflect on this →"** button appears alongside the existing "Save takeaway" button. Clicking it expands an inline reflection form below the result.

### Reflection Form
Two fields, inline (no modal):
1. **What surprised you most?** — becomes `insight_title` in the Vault card
2. **What will you do this week?** — becomes `next_action` in the Vault card

"Save to Vault →" button:
- Calls `saveReflection(sessionId)` 
- Auto-saves an enriched Vault card (uses existing `saveEnrichment()` pattern)
- Shows toast: "✦ Insight saved to Vault"
- Then transitions to the clarity rating (Step 4)

The reflection is optional — the existing "Save takeaway" flow is unchanged. The "Reflect" button is additive.

### Session Linkage
The reflection saves to the `memories` table with `insight_title` and `next_action` populated (the columns already exist from Sub-project 1). The memory is linked to the session via `session_id` (already stored on memory records).

---

## 3. Clarity Rating

### Trigger
Appears immediately after the user saves a reflection, replacing the form in place.

### UI
```
Did this help you think more clearly?
[Tracks which lenses work best for you]

  [ 👍 Yes, clearer ]   [ 👎 Not really ]
  
  Either way — your vault card is saved ✓
```

One tap dismisses. Both options store the rating and close the reflection area. Neither option is "wrong" — the data is used to surface lens recommendations over time, not to judge the session.

### Storage
- Stored immediately to `localStorage` keyed by session ID: `thinkos_clarity_<sessionId>`
- If logged in, syncs to `sessions.clarity` column via `.update()` (requires manual SQL migration)
- If the column doesn't exist yet, the sync fails silently — localStorage data is preserved

### Manual SQL Migration (run once)
```sql
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS clarity BOOLEAN;
```

---

## 4. Metrics Impact

The clarity rating feeds into future dashboard improvements:

| Future stat | Source |
|-------------|--------|
| "74% clarity rate" | `sessions` where `clarity = true` / total rated sessions |
| "Your best lens: Inversion (9/10 helpful)" | `clarity` grouped by `lens_id` |
| "Guided sessions 2× more helpful" | `clarity` grouped by whether intake was used |

For Sub-project 2, we only **collect** the data. Dashboard display of clarity metrics is Sub-project 4.

---

## 5. Technical Architecture

### Files Modified
| File | Changes |
|------|---------|
| `static/index.html` | `LENS_INTAKE` constant, `renderIntakeForm()`, `submitWithIntake()`, `launchLens()` wrapper, `showReflection()`, `saveReflection()`, `rateClarity()`, CSS for intake + reflection + rating UI |
| Supabase (manual) | `ALTER TABLE sessions ADD COLUMN IF NOT EXISTS clarity BOOLEAN;` |

### Function Map
```
launchLens(id)
  └─ if id in LENS_INTAKE → renderIntakeForm(id)
  └─ else → existing behaviour (unchanged)

renderIntakeForm(lensId)
  └─ injects intake HTML into lens panel
  └─ "Run →" button calls submitWithIntake(lensId)
  └─ "Skip →" sets _intakeSubmitting=true, calls launchLens(lensId), resets flag

submitWithIntake(lensId)
  └─ reads intake field values
  └─ appends to thought
  └─ calls runLensById(lensId)
  └─ restores original thought

[AI result renders — existing flow]
  └─ "Reflect on this →" button added to result footer

showReflection(sessionId)
  └─ expands inline reflection form below result

saveReflection(sessionId)
  └─ calls saveEnrichment() pattern (existing)
  └─ shows toast
  └─ calls showClarityRating(sessionId)

showClarityRating(sessionId)
  └─ replaces reflection form with 👍 / 👎 UI

rateClarity(sessionId, helpful)
  └─ stores to localStorage
  └─ syncs to Supabase sessions.clarity (silent fail if column missing)
  └─ dismisses rating UI
```

### Modified: `launchLens(id)`
The existing `launchLens` function is wrapped — not replaced. The wrapper checks `LENS_INTAKE` and either shows the intake form or falls through to the original behaviour.

---

## What Does NOT Change

- All lens tools, prompts, and AI pipeline — unchanged
- Expert lenses — no intake, unchanged flow
- The Journal, Planner, Analytics, Companion — unchanged
- The Insight Vault — unchanged (reflection auto-saves to it using the existing enrichment pattern)
- Auth, sync, Supabase client — unchanged
- The dashboard from Sub-project 1 — unchanged

---

## Out of Scope (later sub-projects)

- Displaying clarity rate on the dashboard (Sub-project 4)
- Lens recommendations based on clarity data (Sub-project 4)
- AI Mentor Modes (Sub-project 3)
- Search by Problem (Sub-project 3)
- Progressive Mastery stages (Sub-project 4)
