import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

_dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_dotenv_path, override=True)

app = Flask(__name__, static_folder='static')

OPENROUTER_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL       = 'anthropic/claude-haiku-4-5'
MODEL_RICH  = 'anthropic/claude-haiku-4-5'

# ─── Stripe ────────────────────────────────────────────────────────────────────
# TODO: Set these in your .env / Railway environment variables
STRIPE_SECRET_KEY      = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET  = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_PRICE_MONTHLY   = os.environ.get('STRIPE_PRICE_MONTHLY', '')   # price_xxx  $9/month
STRIPE_PRICE_ANNUAL    = os.environ.get('STRIPE_PRICE_ANNUAL', '')    # price_xxx  $79/year
STRIPE_PRICE_LIFETIME  = os.environ.get('STRIPE_PRICE_LIFETIME', '')  # price_xxx  $149 one-time
APP_URL                = os.environ.get('APP_URL', 'http://localhost:5000')

# ─── System Prompts ────────────────────────────────────────────────────────────

REI_PROMPT = """You are the REI Council — three internal minds every human carries. When given a situation or decision, each mind speaks in its authentic voice.

INSTINCT (oldest mind):
- Worldview: danger is everywhere; must protect what matters
- Motivation: fear and envy — scans for threat and loss
- Voice: blunt, cautious, sometimes uncomfortably honest about what's really feared
- Speaks in short, direct sentences. Names the fear people won't admit.

EMOTION (opposite of Instinct):
- Worldview: good dominates; life rewards boldness
- Motivation: competitiveness — wants to be seen, celebrated, to win
- Voice: enthusiastic, visual, story-driven. Sees the best case vividly.
- Sometimes naive about real risks.

REASON (youngest mind):
- Worldview: neutral — problems to be solved, advantages to be seized
- Motivation: greed for efficiency, control, and strategic advantage
- Voice: precise, structured, analytical. Cold but accurate.
- Missing human factors the other two feel.

RULES:
- Each mind speaks 2-4 sentences in FIRST PERSON as that mind
- Respond to the SPECIFIC situation — no generic advice
- majority_view: where 2+ minds agree (the Council's signal to act)
- action_question: one sharp question under 20 words that cuts to the real decision
- alignment: "divided" (all disagree) | "partial" (2 agree) | "strong" (all agree)

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "instinct": "...",
  "emotion": "...",
  "reason": "...",
  "majority_view": "...",
  "action_question": "...",
  "alignment": "divided|partial|strong"
}"""

LADDER_PROMPT = """You are a Ladder Diagnostician using the Information Ladder — 5 rungs of reality and thinking:

RUNG 1 — MATHEMATICS: Pure logic, pattern, formal structure. Reality's skeleton. No physical substance.
RUNG 2 — PHYSICS: Matter, energy, causality, space-time. What maths describes when touching the world.
RUNG 3 — CONSCIOUSNESS: Subjective experience, mind, qualia, awareness. What it is like to be something. Cannot be reduced to physics.
RUNG 4 — MEANING: Purpose, narrative, values, ethics, beauty, love. What consciousness reaches for beyond survival.
RUNG 5 — GOD: Ultimate reality, uncaused cause, transcendence. The source from which all rungs emerge.

Key principle: Each rung EMERGES from the one below but cannot be REDUCED to it.

When given a question or problem:
1. current_rung: which rung is the person actually operating on (1-5)?
2. rung_name: name of that rung
3. current_view: what this question looks like from that rung (2-3 sentences)
4. below_view: what happens when you reduce it one rung down — what gets lost (2-3 sentences, null if rung 1)
5. above_view: what emerges when you rise one rung up — what becomes visible (2-3 sentences, null if rung 5)
6. ascent_question: one question under 25 words that pulls toward the higher rung

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "current_rung": <1-5>,
  "rung_name": "...",
  "current_view": "...",
  "below_view": "...",
  "above_view": "...",
  "ascent_question": "..."
}"""

SOCRATIC_PROMPT = """You are a Socratic thinking partner. Your only tool is questions. You never give answers, opinions, or explanations.

Rules:
- Ask exactly ONE question — nothing else, no preamble
- Challenge an assumption in what they said, not just continue their thought
- Banned words: "interesting", "great", "exactly", "absolutely", "good point", "indeed"
- If they ask you a direct question, respond with a question about why they're asking
- Questions must be SHORT — under 20 words
- The best questions make people pause, feel slightly uncomfortable, then think harder
- You are not here to comfort. You are here to sharpen.

Reply with nothing but the question itself."""

# ─── OpenRouter call ───────────────────────────────────────────────────────────

def call_ai(system, messages, max_tokens=1024, model=None):
    headers = {
        'Authorization': f'Bearer {OPENROUTER_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'ThinkOS'
    }
    body = {
        'model': model or MODEL,
        'max_tokens': max_tokens,
        'messages': [{'role': 'system', 'content': system}] + messages
    }
    r = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=45)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content'].strip()


def parse_json(text):
    """Extract and parse JSON from model output, handling markdown fences and preamble."""
    t = text.strip()
    # Strip markdown code fences anywhere in response
    if '```' in t:
        # grab content between first ``` and last ```
        start = t.find('```')
        end   = t.rfind('```')
        if start != end:
            chunk = t[start+3:end].strip()
            # strip language tag (e.g. "json\n")
            if chunk and not chunk.startswith('{') and not chunk.startswith('['):
                chunk = chunk.split('\n', 1)[-1].strip()
            t = chunk
    # Find outermost JSON object or array
    for opener, closer in [('{', '}'), ('[', ']')]:
        s = t.find(opener)
        e = t.rfind(closer)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(t[s:e+1])
            except json.JSONDecodeError:
                pass
    # Last resort — try raw
    return json.loads(t)

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/icons/<path:filename>')
def icons(filename):
    return send_from_directory('static/icons', filename)


@app.route('/api/rei', methods=['POST'])
def rei_council():
    data = request.get_json()
    situation = (data or {}).get('situation', '').strip()
    if not situation:
        return jsonify({'error': 'No situation provided'}), 400
    try:
        text = call_ai(REI_PROMPT, [{'role': 'user', 'content': situation}])
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ladder', methods=['POST'])
def ladder():
    data = request.get_json()
    question = (data or {}).get('question', '').strip()
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    try:
        text = call_ai(LADDER_PROMPT, [{'role': 'user', 'content': question}])
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/socratic', methods=['POST'])
def socratic():
    data = request.get_json()
    messages = (data or {}).get('messages', [])
    if not messages:
        return jsonify({'error': 'No messages provided'}), 400
    try:
        reply = call_ai(SOCRATIC_PROMPT, messages, max_tokens=128)
        return jsonify({'question': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

SYNTHESIS_PROMPT = """You are a Council Synthesist. You have been given the results of multiple thinking tools applied to the same situation. These always include REI Council, The Information Ladder, Kingdom Lens, and Blind Spot Detector — and may also include First Principles and Inversion analyses.

Your job: read across ALL provided results and write a synthesis — what do they collectively reveal that none says alone?

Rules:
- synthesis: 3-4 sentences. What is the deeper pattern across ALL lenses? Be specific to this situation.
- synthesis_question: ONE question under 25 words that cuts to the heart of what all lenses are pointing at
- Do not summarise each tool — synthesise across them. Find the convergence.
- If First Principles or Inversion are included, use them to stress-test the synthesis
- Be direct. No hedging. No "it seems like."

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "synthesis": "...",
  "synthesis_question": "..."
}"""

PRO_SYNTHESIS_PROMPT = """You are a Master Synthesist. You have been given the results of multiple thinking lenses applied to the same situation or question. Your job is to find the cross-lens pattern — what emerges when you read them all together that no single lens could reveal alone.

Rules:
- synthesis: 4-5 sentences. Find the deepest pattern. What are all the lenses converging on? What tension or contradiction do they reveal? What does this mean for the person?
- synthesis_question: ONE devastating question under 30 words that cuts across everything and forces clarity
- key_insight: ONE sentence — the single most important thing all these lenses are saying
- action: The one concrete next step that is supported by the most lenses
- Be ruthlessly specific to this situation. No generic advice.
- Do not summarise — synthesise. Find what none of them say alone.

Respond ONLY with valid JSON. No markdown, no extra text:
{
  "synthesis": "...",
  "synthesis_question": "...",
  "key_insight": "...",
  "action": "..."
}"""

KINGDOM_PROMPT = """You are a Kingdom Lens advisor. You help people see their real-life situations through a biblical lens — not piously or with religious clichés, but with the honest, direct wisdom of Scripture applied to actual human experience.

You respond through SIX dimensions:

KINGDOM VIEW — What does God's intended reality say about this situation? Jesus always saw what IS and what SHOULD BE simultaneously. What would this look like if God's will were fully done here?

THE PERSON — Jesus looked past every label to the human underneath. Who is the real person in this situation? What are they protecting, wanting, afraid of? (If about the user themselves, turn it inward.)

ETERNAL WEIGHT — Jesus had different scales than the world. Weigh this situation by what actually matters long-term and eternally — not by social approval, comfort, or short-term outcomes.

THE PATH THROUGH — Jesus never avoided suffering; he walked through it redemptively. Is there something being formed in this difficulty that bypassing it would prevent? What is God potentially doing through this, not just to this person?

BIBLICAL ANALOGY — Find the most fitting biblical character or story that mirrors this situation. Be specific: name the person, describe their situation briefly, and draw the parallel clearly. Use real people (Joseph, David, Ruth, Peter, Paul, the Prodigal Son, Esther, Job, etc.) — not vague references.

SCRIPTURE & WISDOM — Give 2-3 specific Bible verses (with references) that speak directly to this situation. After each verse, add one sentence of applied wisdom — what this verse means for THIS specific situation, not just in general.

RULES:
- Be honest and direct. No church clichés.
- Each lens: 2-3 sentences max. Be specific to the situation.
- biblical_analogy: real named person/story, 1 sentence each field
- scripture: exactly 2 verses, accurate quotes, 1-sentence applied wisdom each
- kingdom_question: under 25 words, sharp and reframing
- Speak plainly.

Respond ONLY with valid JSON, no markdown fences:
{
  "kingdom": "...",
  "the_person": "...",
  "eternal_weight": "...",
  "the_path": "...",
  "biblical_analogy": {
    "person_or_story": "...",
    "their_situation": "...",
    "the_parallel": "..."
  },
  "scripture": [
    {"reference": "...", "verse": "...", "applied": "..."},
    {"reference": "...", "verse": "...", "applied": "..."}
  ],
  "kingdom_question": "..."
}"""


@app.route('/api/kingdom', methods=['POST'])
def kingdom():
    data = request.get_json()
    situation = (data or {}).get('situation', '').strip()
    if not situation:
        return jsonify({'error': 'No situation provided'}), 400
    try:
        text = call_ai(KINGDOM_PROMPT, [{'role': 'user', 'content': situation}], max_tokens=1200, model=MODEL_RICH)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
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
    # Extended lenses (First Principles + Inversion added to Full Council)
    if data.get('fp'):
        fp = data['fp']
        panels_text = ' | '.join([f"{p.get('label','')}={p.get('text','')[:80]}" for p in fp.get('panels', [])[:3]])
        parts.append(f"First Principles — {fp.get('synthesis','')} [{panels_text}]")
    if data.get('inversion'):
        inv = data['inversion']
        panels_text = ' | '.join([f"{p.get('label','')}={p.get('text','')[:80]}" for p in inv.get('panels', [])[:3]])
        parts.append(f"Inversion — {inv.get('synthesis','')} [{panels_text}]")
    if not parts:
        return jsonify({'error': 'No tool results provided'}), 400
    combined = '\n\n'.join(parts)
    try:
        text = call_ai(SYNTHESIS_PROMPT, [{'role': 'user', 'content': combined}], max_tokens=512)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pro-synthesis', methods=['POST'])
def pro_synthesis():
    """Mega-synthesis across any set of lens results for Pro Council."""
    data = request.get_json()
    thought = data.get('thought', '')
    results = data.get('results', [])  # list of {lens_name, synthesis, question, action, panels}
    if not results:
        return jsonify({'error': 'No lens results provided'}), 400
    parts = [f"The situation/thought: {thought}\n"]
    for r in results:
        name = r.get('lens_name', 'Unknown lens')
        synth = r.get('synthesis', '')
        question = r.get('question', '')
        action = r.get('action', '')
        panels = r.get('panels', [])
        panel_summary = ' | '.join([f"{p.get('label','')}={p.get('text','')[:70]}" for p in panels[:3]])
        parts.append(f"{name}:\n  Core insight: {synth}\n  Key question: {question}\n  Action: {action}\n  Detail: [{panel_summary}]")
    combined = '\n\n'.join(parts)
    try:
        text = call_ai(PRO_SYNTHESIS_PROMPT, [{'role': 'user', 'content': combined}], max_tokens=700)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Stripe Checkout ───────────────────────────────────────────────────────────

SUPABASE_URL     = os.environ.get('SUPABASE_URL', 'https://plbmidsmtbkggehmoeuf.supabase.co')
SUPABASE_SERVICE = os.environ.get('SUPABASE_SERVICE_KEY', '')
VAPID_PUBLIC_KEY  = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_EMAIL       = os.environ.get('VAPID_EMAIL', 'mailto:support@thinkos.app')

def _sb_headers():
    return {
        'apikey': SUPABASE_SERVICE,
        'Authorization': f'Bearer {SUPABASE_SERVICE}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }

def _ensure_referral_coupon(stripe):
    """Create the REFERRAL1MO coupon once if it doesn't exist."""
    try:
        stripe.Coupon.retrieve('REFERRAL1MO')
    except stripe.error.InvalidRequestError:
        stripe.Coupon.create(
            id='REFERRAL1MO',
            duration='once',
            percent_off=100,
            name='1 Month Free – Referral Reward',
            max_redemptions=10000,
        )


@app.route('/api/create-checkout', methods=['POST'])
def create_checkout():
    if not STRIPE_SECRET_KEY:
        return jsonify({'error': 'Payments not configured yet'}), 503
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        data         = request.get_json() or {}
        plan         = data.get('plan', 'monthly')
        email        = data.get('email', '')
        referral_code = data.get('referral_code', '').strip()

        price_map = {
            'monthly':  STRIPE_PRICE_MONTHLY,
            'annual':   STRIPE_PRICE_ANNUAL,
            'lifetime': STRIPE_PRICE_LIFETIME,
        }
        price_id = price_map.get(plan, STRIPE_PRICE_MONTHLY)
        if not price_id:
            return jsonify({'error': f'Price ID for plan "{plan}" not set'}), 503

        mode = 'payment' if plan == 'lifetime' else 'subscription'
        params = dict(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode=mode,
            success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}" + (f"&ref={referral_code}" if referral_code else ""),
            cancel_url=f"{APP_URL}/",
            allow_promotion_codes=True,
        )
        if email:
            params['customer_email'] = email

        # Apply 1-month-free coupon for referred users (subscriptions only)
        if referral_code and mode == 'subscription':
            _ensure_referral_coupon(stripe)
            params['discounts'] = [{'coupon': 'REFERRAL1MO'}]
            params.pop('allow_promotion_codes', None)  # can't mix with discounts

        session = stripe.checkout.Session.create(**params)
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-referral', methods=['POST'])
def process_referral():
    """Called from success page. Awards 1 month free to the referrer via Stripe balance credit."""
    if not STRIPE_SECRET_KEY or not SUPABASE_SERVICE:
        return jsonify({'ok': False}), 200  # silent fail
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        data          = request.get_json() or {}
        referral_code = data.get('referral_code', '').strip()
        referee_email = data.get('referee_email', '').strip()
        if not referral_code or not referee_email:
            return jsonify({'ok': False, 'error': 'Missing params'}), 400

        # Look up referrer in Supabase
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/referrals",
            headers={**_sb_headers(), 'Prefer': 'return=representation'},
            params={'referrer_code': f'eq.{referral_code}', 'status': 'eq.pending', 'limit': '1'}
        )
        rows = resp.json() if resp.ok else []
        if not rows:
            return jsonify({'ok': False, 'error': 'Referral not found or already used'}), 200

        referral = rows[0]
        referrer_user_id = referral.get('referrer_user_id')

        # Get referrer's Stripe customer ID from profiles
        prof_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            headers={**_sb_headers(), 'Prefer': 'return=representation'},
            params={'id': f'eq.{referrer_user_id}', 'limit': '1'}
        )
        profiles = prof_resp.json() if prof_resp.ok else []
        stripe_customer_id = (profiles[0].get('stripe_customer_id', '') if profiles else '')

        if stripe_customer_id:
            # Credit A$9 (900 cents AUD) to referrer's Stripe balance — auto-deducts from next invoice
            stripe.Customer.create_balance_transaction(
                stripe_customer_id,
                amount=-900,  # negative = credit
                currency='aud',
                description=f'Referral reward: {referee_email} subscribed',
            )

        # Mark referral as rewarded
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/referrals",
            headers=_sb_headers(),
            params={'referrer_code': f'eq.{referral_code}'},
            json={'status': 'rewarded', 'referee_email': referee_email, 'rewarded_at': 'now()'}
        )

        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/verify-session', methods=['POST'])
def verify_session():
    """Called by the success page to confirm payment went through."""
    if not STRIPE_SECRET_KEY:
        return jsonify({'error': 'Payments not configured'}), 503
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        data       = request.get_json() or {}
        session_id = data.get('session_id', '')
        if not session_id:
            return jsonify({'ok': False, 'error': 'No session_id'}), 400
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status in ('paid', 'no_payment_required'):
            customer_email = session.customer_details.email if session.customer_details else ''
            plan = 'lifetime' if session.mode == 'payment' else 'subscription'
            return jsonify({'ok': True, 'email': customer_email, 'plan': plan})
        return jsonify({'ok': False, 'status': session.payment_status})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/sync-subscription', methods=['POST'])
def sync_subscription():
    """Called after login — checks Stripe for this email and updates Supabase profile."""
    if not STRIPE_SECRET_KEY:
        return jsonify({'ok': False}), 200
    try:
        import stripe
        import requests as req
        stripe.api_key = STRIPE_SECRET_KEY
        data = request.get_json() or {}
        user_id = data.get('user_id', '')
        email = data.get('email', '')
        if not user_id or not email:
            return jsonify({'ok': False, 'error': 'Missing user_id or email'}), 400

        # Check Stripe for customer with this email
        customers = stripe.Customer.list(email=email, limit=1)
        plan = 'free'
        plan_status = 'active'
        stripe_customer_id = ''

        if customers.data:
            customer = customers.data[0]
            stripe_customer_id = customer.id
            # Check subscriptions
            subs = stripe.Subscription.list(customer=customer.id, status='active', limit=1)
            if subs.data:
                sub = subs.data[0]
                price_id = sub['items']['data'][0]['price']['id']
                if price_id == STRIPE_PRICE_LIFETIME:
                    plan = 'lifetime'
                elif price_id == STRIPE_PRICE_ANNUAL:
                    plan = 'annual'
                elif price_id == STRIPE_PRICE_MONTHLY:
                    plan = 'monthly'
                else:
                    plan = 'monthly'
            else:
                # Check for one-time lifetime payment
                payments = stripe.PaymentIntent.list(customer=customer.id, limit=10)
                for pi in payments.data:
                    if pi.status == 'succeeded' and pi.amount >= 14900:
                        plan = 'lifetime'
                        break

        # Update Supabase profile using service key
        SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
        SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            headers = {
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            }
            payload = {
                'plan': plan,
                'plan_status': plan_status,
                'stripe_customer_id': stripe_customer_id,
                'updated_at': 'now()'
            }
            req.patch(
                f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
                headers=headers,
                json=payload
            )

        return jsonify({'ok': True, 'plan': plan})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Stripe sends events here — used to handle cancellations etc."""
    if not STRIPE_SECRET_KEY:
        return 'not configured', 200
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        payload    = request.get_data()
        sig_header = request.headers.get('Stripe-Signature', '')
        event      = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        # Log event type — extend here to handle cancellations, renewals, etc.
        print(f'Stripe webhook: {event["type"]}')
        return jsonify({'received': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/success')
def success_page():
    """Stripe redirects here after successful payment."""
    return send_from_directory('static', 'success.html')


INSIGHTS_PROMPT = """You are a Thinking Pattern Analyst. You have been given a person's saved ThinkOS sessions — a record of what they have been thinking about across different tools over time.

Your job: read across ALL sessions and reveal the deeper patterns, growth edges, and recurring themes.

Respond ONLY with valid JSON:
{
  "dominant_theme": "The single most recurring topic or concern across all sessions (1 sentence)",
  "thinking_style": "How this person tends to approach problems — what their REI/Ladder/Kingdom results reveal about their mind (2 sentences)",
  "growth_edge": "The one pattern that keeps appearing that they seem to be working through (2 sentences)",
  "blind_spot_pattern": "A recurring blind spot or avoided angle across sessions (1-2 sentences)",
  "strongest_lens": "Which tool reveals the most about them and why (1 sentence)",
  "insight": "One deep, specific observation about this person's thinking that they probably haven't articulated themselves (2-3 sentences)",
  "question": "One question under 25 words that cuts to the heart of what all their sessions are circling around"
}"""


@app.route('/api/insights', methods=['POST'])
def get_insights():
    """Analyse a user's saved sessions and return thinking patterns."""
    try:
        data = request.get_json() or {}
        sessions = data.get('sessions', [])
        if not sessions:
            return jsonify({'error': 'No sessions provided'}), 400

        # Build a concise summary of each session for the prompt
        parts = []
        for i, s in enumerate(sessions[:20], 1):  # cap at 20
            tool = s.get('tool', 'unknown')
            thought = s.get('thought', '')[:200]
            result = s.get('result', {})
            summary = f"Session {i} [{tool.upper()}]: \"{thought}\""
            if tool == 'rei' and result:
                summary += f" → Instinct: {result.get('instinct','')[:80]} | Alignment: {result.get('alignment','')}"
            elif tool == 'ladder' and result:
                summary += f" → Rung {result.get('current_rung','')}: {result.get('rung_name','')} | {result.get('current_view','')[:80]}"
            elif tool == 'kingdom' and result:
                summary += f" → {result.get('kingdom','')[:80]}"
            elif tool == 'blind' and result:
                summary += f" → Missing: {result.get('missing_perspective','')}"
            elif tool == 'council' and result:
                synth = result.get('synthesis', {})
                summary += f" → {synth.get('synthesis','')[:100]}" if synth else ""
            parts.append(summary)

        combined = '\n'.join(parts)
        text = call_ai(INSIGHTS_PROMPT, [{'role': 'user', 'content': combined}], max_tokens=800)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Generic Lens System ──────────────────────────────────────────────────────
# All new lenses return the same JSON shape so the frontend can use one renderer.
# { panels:[{label,text,emoji}], synthesis, question, action }

LENS_PROMPTS = {

'first_principles': """You are a First Principles analyst. Strip the situation to atomic truths, kill all analogies and assumptions, then rebuild the best path from scratch.

Respond ONLY with valid JSON matching this exact shape:
{
  "panels": [
    {"label":"Assumptions to Kill","emoji":"🪓","text":"List every assumption being made — challenge each one ruthlessly (3-5 assumptions, one per line)"},
    {"label":"Bedrock Truths","emoji":"🪨","text":"What do we know for certain once all assumptions are stripped away? (3-5 truths)"},
    {"label":"Rebuilt from Scratch","emoji":"🏗️","text":"Reason upward from ONLY the bedrock truths. What does the best path look like when built from zero? (3-4 sentences)"},
    {"label":"The Gap","emoji":"🔭","text":"What is the key difference between the original thinking and the first-principles answer? Be specific. (2 sentences)"}
  ],
  "synthesis": "One sentence capturing the core first-principles insight",
  "question": "One powerful question under 20 words to drill even deeper",
  "action": "The single most important next physical action"
}""",

'inversion': """You are a Charlie Munger-style Inversion analyst. Invert the problem — figure out what guarantees failure, then work backwards to success.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"What Would Guarantee Failure","emoji":"💀","text":"List every action, belief, or path that would absolutely guarantee the worst outcome. Be specific and honest. (4-6 items)"},
    {"label":"Why Those Paths Are Tempting","emoji":"🪤","text":"Why do smart people still walk into these failure traps? What makes them appealing in the moment? (2-3 sentences)"},
    {"label":"Inverted Success Map","emoji":"🗺️","text":"Now invert each failure path into its opposite. What does success look like when defined as the absence of failure? (3-4 sentences)"},
    {"label":"The Honest Risk Assessment","emoji":"⚡","text":"What is the single biggest real risk here that most people are underestimating? Don't soften it. (2-3 sentences)"}
  ],
  "synthesis": "One sentence capturing the core inversion insight",
  "question": "One uncomfortable question that the inversion reveals",
  "action": "The single most important thing to STOP doing or AVOID"
}""",

'stoic': """You are a Stoic philosophy advisor drawing on Marcus Aurelius, Epictetus, and Seneca. Apply the dichotomy of control, amor fati, and memento mori to the situation.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"In Your Control","emoji":"✊","text":"What is fully within this person's power to choose, change, or act on? List specifically. (3-5 items)"},
    {"label":"Not In Your Control","emoji":"🌊","text":"What must be released? What are they trying to control that cannot be controlled? (3-5 items)"},
    {"label":"Amor Fati — Love of Fate","emoji":"🔥","text":"How could this difficulty be not just accepted but loved? What does it make possible that nothing else could? (2-3 sentences)"},
    {"label":"What Marcus Would Do","emoji":"👑","text":"Drawing on Marcus Aurelius, what would a philosopher-king do here? Be direct, not pious. (3-4 sentences)"}
  ],
  "synthesis": "The core Stoic insight for this situation in one sentence",
  "question": "One Stoic question to sit with today",
  "action": "One concrete Stoic practice or action for this week"
}""",

'future_self': """You are channelling someone's future self — wise, clear-eyed, and honest. Write letters from their 5-year and 10-year future self about the current situation.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"Letter from 5-Year Future You","emoji":"📬","text":"Write a direct, personal letter from their 5-year future self. Warm but honest. What do they wish they'd known? What did this moment mean? (4-5 sentences, first person)"},
    {"label":"Letter from 10-Year Future You","emoji":"🌅","text":"Write a letter from 10 years out. The perspective has shifted. What looks different from this distance? (4-5 sentences, first person)"},
    {"label":"What They'd Tell You Right Now","emoji":"💡","text":"Cutting through both letters — the single most important thing your future self wants present-you to hear. (2-3 sentences)"},
    {"label":"The Cost of Inaction","emoji":"⏳","text":"If nothing changes and they look back in 10 years — what will they regret most? Be specific and honest. (2-3 sentences)"}
  ],
  "synthesis": "One sentence capturing what the future-self perspective reveals",
  "question": "What question would your 10-year future self most want you to answer today?",
  "action": "The one decision or step your future self would tell you to make right now"
}""",

'feynman': """You are a Feynman Technique coach. Force the person to explain their situation or decision in simple terms, then expose the gaps in their own understanding.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"Explain It Like You're 12","emoji":"🧒","text":"Translate the situation into the simplest possible language. No jargon, no complexity. If a child couldn't understand it, the thinking isn't clear yet. (3-4 sentences)"},
    {"label":"Where the Explanation Breaks Down","emoji":"🔍","text":"Find the exact moment the simple explanation fails or becomes vague. What word or concept couldn't actually be explained simply? This is where the real confusion lives. (2-3 sentences)"},
    {"label":"What You Don't Actually Know","emoji":"❓","text":"List the things being assumed or glossed over that aren't actually understood. These are the gaps. (3-5 items)"},
    {"label":"Rebuilt with Clarity","emoji":"💎","text":"Now explain it again — but this time only using what is genuinely understood. Strip out the gaps. What remains? (3-4 sentences)"}
  ],
  "synthesis": "The core insight the Feynman process reveals in one sentence",
  "question": "The one question that, once answered, would make the whole thing clear",
  "action": "The one thing to research, learn, or clarify before deciding"
}""",

'historical': """You are a Historical Analogies advisor. Find real people, movements, or moments in history that parallel this situation — and extract the lesson.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"Who Has Done This Before","emoji":"📜","text":"Name 2-3 real historical figures, companies, or movements that faced a remarkably similar situation. Be specific — names, years, context. (3-5 sentences)"},
    {"label":"What They Did","emoji":"⚔️","text":"What choice did they make? What was their strategy? What was the outcome? (3-4 sentences per analogy, brief)"},
    {"label":"The Lesson to Extract","emoji":"🎓","text":"What is the most transferable lesson from these historical parallels? What pattern repeats? (2-3 sentences)"},
    {"label":"The Key Difference","emoji":"🔄","text":"Where does the analogy break down? What is fundamentally different about today's context that changes what should be done? (2-3 sentences)"}
  ],
  "synthesis": "One sentence capturing the historical insight that applies now",
  "question": "What would the people in these historical examples most want you to understand?",
  "action": "The one thing history says to do — or avoid — right now"
}""",

'energy': """You are an Energy and Flow coach. Map how this decision or situation affects the person's energy — what charges them, what drains them, and what the high-energy path looks like.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"What Charges Your Energy","emoji":"⚡","text":"About this situation or path — what elements genuinely energise, excite, or give life? Be specific to this person's context. (3-5 items)"},
    {"label":"What Drains Your Energy","emoji":"🪫","text":"What aspects of this path, if pursued, will slowly leak energy? What will feel heavy in month 3 that feels fine today? (3-5 items)"},
    {"label":"90-Day Energy Forecast","emoji":"📊","text":"If they pursue this path, what will their energy look like at 30 days, 60 days, and 90 days? Honest and specific. (3-4 sentences)"},
    {"label":"The High-Energy Path","emoji":"🌟","text":"What version of this decision maximises sustained energy? What would need to be true to make this energising long-term? (3-4 sentences)"}
  ],
  "synthesis": "One sentence capturing the energy insight — does this path give or take?",
  "question": "What does your body already know about this that your mind hasn't admitted yet?",
  "action": "One change to the plan that would immediately increase energy"
}""",

'stakeholder': """You are a Stakeholder and Game Theory analyst. Map all the players affected by this situation — who wins, who loses, and what the optimal path looks like when everyone's interests are considered.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"All the Players","emoji":"♟️","text":"List every stakeholder affected by this situation — family, colleagues, users, competitors, future-self. For each: name them and their core interest. (4-7 stakeholders)"},
    {"label":"Who Wins in Each Scenario","emoji":"🏆","text":"For the 2-3 most likely paths: who benefits? Whose interests are served? Be specific about what they gain. (3-4 sentences)"},
    {"label":"Who Loses — and Why It Matters","emoji":"⚖️","text":"Who gets hurt or left behind in each path? What are the real costs to real people? (2-3 sentences)"},
    {"label":"The Optimal Path","emoji":"🤝","text":"What path creates the most value for the most stakeholders while protecting the most important relationships? (3-4 sentences)"}
  ],
  "synthesis": "One sentence capturing the game-theory insight",
  "question": "Whose interests are you most underweighting right now?",
  "action": "One conversation to have or relationship to consider before deciding"
}""",

'systems': """You are a Systems Thinking analyst. Map the feedback loops, leverage points, and systemic forces at play in this situation.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"The Feedback Loops","emoji":"🔄","text":"What reinforcing loops (things that compound) and balancing loops (things that self-correct) are at play? Name them specifically. (2-3 loops each, with examples)"},
    {"label":"The Leverage Point","emoji":"🎯","text":"Where in this system is the highest-leverage intervention point? Small change here = big systemic shift. Be precise. (2-3 sentences)"},
    {"label":"Unintended Consequences","emoji":"🌊","text":"What second and third-order effects might emerge from the most obvious action? What could this set in motion that isn't visible yet? (3-4 items)"},
    {"label":"The Systemic Path","emoji":"🌐","text":"What approach works with the system rather than against it? What path aligns with the natural forces already at play? (3-4 sentences)"}
  ],
  "synthesis": "One sentence capturing the key systems insight",
  "question": "What systemic force is doing most of the work here — and are you using it or fighting it?",
  "action": "The single highest-leverage intervention to make right now"
}""",

'probabilistic': """You are a Probabilistic Thinking and Expected Value analyst. Force rigorous probability thinking on this decision.

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"The Scenarios","emoji":"🎲","text":"List the 3-4 most realistic outcomes of this decision. For each: name it, give an honest probability estimate (%), and describe what it looks like. (be specific and calibrated)"},
    {"label":"Expected Value Analysis","emoji":"📐","text":"For each scenario: what is the value (positive or negative) of that outcome × its probability? Which path has the highest expected value? Show the reasoning. (3-4 sentences)"},
    {"label":"Where You're Probably Wrong","emoji":"🧠","text":"What probability are you almost certainly over- or under-estimating? Where is your thinking most biased? (2-3 sentences)"},
    {"label":"The Calibrated Decision","emoji":"✅","text":"Given honest probabilities and values — what does the math actually say to do? Does it match your gut? If not, why not? (3-4 sentences)"}
  ],
  "synthesis": "One sentence capturing the probabilistic insight",
  "question": "What would you need to believe to be true to change your decision — and how likely is that belief to be correct?",
  "action": "The decision the expected value analysis points to"
}"""

,'character': """You are a depth psychologist and character analyst working at the intersection of Carl Jung's archetypal theory and Jordan Peterson's synthesis of the Big Five personality model with Jungian archetypes. Analyse the person's situation, decision, or struggle through the lens of who they ARE at a psychological level — their archetype, their personality structure, and the shadow material driving them.

FOUR PANELS to return:

1. JUNGIAN ARCHETYPE — Which of Jung's core archetypes is most active in this person right now? (Hero, Shadow, Anima/Animus, Self, Persona, Trickster, Wise Old Man/Woman, Child, etc.) How is this archetype driving their behaviour or framing? What does the archetype want? What does it fear? (3-4 sentences, specific to the situation)

2. SHADOW MATERIAL — What is the Shadow (the repressed, unconscious part) doing here? What are they projecting onto others? What are they refusing to see in themselves? What quality are they disowning that is actually driving this situation? (3-4 sentences. Be direct. This is the uncomfortable truth.)

3. BIG FIVE PERSONALITY DYNAMICS — Using Peterson's interpretation of Big Five (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism), what personality traits are most visible in how they've framed this situation? Where is high Agreeableness creating a trap? Where is Neuroticism amplifying the perceived stakes? Where is low Conscientiousness or high Openness complicating the path? (Be specific to what they've written, not generic. 3-4 sentences.)

4. THE INDIVIDUATION CHALLENGE — Jung's concept of individuation is the lifelong process of becoming who you actually are. What is this situation calling this person to integrate or confront as part of their individuation journey? What would a more whole version of themselves — one who has integrated the Shadow — do here? (3-4 sentences)

Respond ONLY with valid JSON:
{
  "panels": [
    {"label":"Jungian Archetype","emoji":"🎭","text":"[Panel 1 content]"},
    {"label":"Shadow Material","emoji":"🌑","text":"[Panel 2 content]"},
    {"label":"Big Five Dynamics","emoji":"📊","text":"[Panel 3 content]"},
    {"label":"Individuation Challenge","emoji":"🌀","text":"[Panel 4 content]"}
  ],
  "synthesis": "One sentence capturing the deepest psychological truth this analysis reveals about who this person is and what this situation is asking of them",
  "question": "The one question about their own psychology they most need to sit with — under 25 words",
  "action": "The psychological work or concrete step most aligned with their individuation at this moment"
}"""

}  # end LENS_PROMPTS


@app.route('/api/lens', methods=['POST'])
def run_lens():
    """Generic endpoint for all new lenses."""
    data      = request.get_json() or {}
    lens_id   = data.get('lens_id', '').strip()
    situation = data.get('situation', '').strip()
    if not lens_id or not situation:
        return jsonify({'error': 'lens_id and situation required'}), 400
    # Custom lens — user supplies their own prompt via the request body
    custom_prompt = data.get('custom_prompt', '').strip()
    if lens_id == 'custom' and custom_prompt:
        prompt = custom_prompt + '\n\nRespond ONLY with valid JSON matching this exact shape:\n{"panels":[{"label":"...","emoji":"...","text":"..."}],"synthesis":"...","question":"...","action":"..."}'
    else:
        prompt = LENS_PROMPTS.get(lens_id)
    if not prompt:
        return jsonify({'error': f'Unknown lens: {lens_id}'}), 400
    try:
        text = call_ai(prompt, [{'role': 'user', 'content': f'Situation / decision / thought: {situation}'}], max_tokens=900)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/suggest-lens', methods=['POST'])
def suggest_lens():
    """Given a thought, suggest the best 2 lenses to use."""
    data      = request.get_json() or {}
    thought   = data.get('thought', '').strip()
    if not thought:
        return jsonify({'suggestions': []}), 200
    all_lenses = 'rei, ladder, kingdom, socratic, blind, first_principles, inversion, stoic, future_self, feynman, historical, energy, stakeholder, systems, probabilistic, character'
    prompt = f"""Given this thought: "{thought}"

Which 2 lenses from this list would be MOST useful: {all_lenses}

Reply ONLY with valid JSON: {{"suggestions": ["lens_id_1", "lens_id_2"], "reason": "one sentence why"}}"""
    try:
        text = call_ai('You are a thinking tool selector. Respond only with valid JSON.', [{'role': 'user', 'content': prompt}], max_tokens=120)
        return jsonify(parse_json(text))
    except Exception:
        return jsonify({'suggestions': ['rei', 'blind'], 'reason': 'Default suggestion'})


FIRST_PRINCIPLES_PROMPT = """You are a First Principles Thinking analyst. When given a situation, belief, or decision, help the person strip away assumptions and reason from fundamental truths upward.

Respond ONLY with valid JSON:
{
  "assumptions": ["assumption 1", "assumption 2", "assumption 3"],
  "bedrock_truths": ["truth 1", "truth 2", "truth 3"],
  "rebuilt_answer": "The cleanest solution when reasoned up purely from the bedrock truths (3-4 sentences)",
  "gap": "The key difference between the original thinking and the first-principles answer (1-2 sentences)",
  "analogy": "A vivid, simple analogy that captures the core first-principles insight (1-2 sentences)",
  "next_question": "One powerful question under 20 words to drill even deeper",
  "confidence_shift": "higher|lower|same"
}

Rules:
- assumptions: things the person is taking for granted that may not be true (3-5 items)
- bedrock_truths: what we actually know for certain, stripped of all assumption (3-5 items)
- rebuilt_answer: reason up from ONLY the bedrock truths — no assumed context
- Be direct. Don't be gentle. First principles often reveals uncomfortable truths."""

WEEKLY_REPORT_PROMPT = """You are a personal thinking coach reviewing someone's week of thinking sessions in ThinkOS.

Given their recent sessions, write a warm but honest weekly thinking report.

Respond ONLY with valid JSON:
{
  "headline": "One punchy sentence summarising their thinking week (max 12 words)",
  "volume": "Comment on how much they've been thinking — productive, overthinking, or quiet week? (1 sentence)",
  "top_theme": "The single biggest thing on their mind this week (1 sentence)",
  "win": "One genuine positive pattern or insight from their sessions (2 sentences)",
  "challenge": "One honest challenge or stuck pattern worth addressing (2 sentences)",
  "tools_used": ["tool1", "tool2"],
  "recommendation": "One specific thing to try or think about next week (2 sentences)",
  "quote": "A short motivational quote (under 15 words) that fits their week perfectly"
}"""


@app.route('/api/first-principles', methods=['POST'])
def first_principles():
    data = request.get_json() or {}
    situation = (data or {}).get('situation', '').strip()
    if not situation:
        return jsonify({'error': 'No situation provided'}), 400
    try:
        text = call_ai(FIRST_PRINCIPLES_PROMPT, [{'role': 'user', 'content': f'Situation/belief/decision: {situation}'}], max_tokens=700)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/share-result', methods=['POST'])
def share_result():
    """Save a result to Supabase and return a shareable ID."""
    if not SUPABASE_URL or not SUPABASE_SERVICE:
        return jsonify({'error': 'Sharing not configured'}), 503
    try:
        data = request.get_json() or {}
        tool    = data.get('tool', '')
        thought = data.get('thought', '')[:500]
        result  = data.get('result', {})
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/shared_results",
            headers={**_sb_headers(), 'Prefer': 'return=representation'},
            json={'tool': tool, 'thought': thought, 'result_json': result}
        )
        if resp.ok:
            row = resp.json()
            share_id = row[0]['id'] if isinstance(row, list) else row.get('id')
            return jsonify({'id': share_id, 'url': f"{APP_URL}/shared/{share_id}"})
        return jsonify({'error': 'Could not save result'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/shared/<share_id>')
def shared_result(share_id):
    """Render a shared result page."""
    return send_from_directory('static', 'shared.html')


@app.route('/api/get-shared/<share_id>', methods=['GET'])
def get_shared(share_id):
    """Return shared result data and increment view count."""
    if not SUPABASE_URL or not SUPABASE_SERVICE:
        return jsonify({'error': 'Not configured'}), 503
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/shared_results",
            headers={**_sb_headers(), 'Prefer': 'return=representation'},
            params={'id': f'eq.{share_id}', 'limit': '1'}
        )
        rows = resp.json() if resp.ok else []
        if not rows:
            return jsonify({'error': 'Not found'}), 404
        row = rows[0]
        # Increment view count (fire-and-forget)
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/shared_results",
            headers=_sb_headers(),
            params={'id': f'eq.{share_id}'},
            json={'view_count': row.get('view_count', 0) + 1}
        )
        return jsonify(row)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weekly-report', methods=['POST'])
def weekly_report():
    """Generate a weekly thinking report from recent sessions."""
    try:
        data     = request.get_json() or {}
        sessions = data.get('sessions', [])
        if not sessions:
            return jsonify({'error': 'No sessions provided'}), 400
        parts = []
        for i, s in enumerate(sessions[:14], 1):
            tool    = s.get('tool', 'unknown')
            thought = s.get('thought', '')[:150]
            parts.append(f"Session {i} [{tool.upper()}]: \"{thought}\"")
        combined = '\n'.join(parts)
        text = call_ai(WEEKLY_REPORT_PROMPT, [{'role': 'user', 'content': combined}], max_tokens=600)
        return jsonify(parse_json(text))
    except json.JSONDecodeError:
        return jsonify({'error': 'Parse error', 'raw': text[:500]}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_key():
    """Frontend fetches this to set up push subscription."""
    return jsonify({'key': VAPID_PUBLIC_KEY})


@app.route('/api/push-subscribe', methods=['POST'])
def push_subscribe():
    """Save a push subscription to Supabase."""
    if not SUPABASE_SERVICE:
        return jsonify({'ok': False}), 200
    try:
        data = request.get_json() or {}
        subscription = data.get('subscription', {})
        user_id      = data.get('user_id', '')
        if not subscription:
            return jsonify({'ok': False, 'error': 'No subscription'}), 400
        payload = {
            'endpoint':   subscription.get('endpoint', ''),
            'p256dh':     (subscription.get('keys') or {}).get('p256dh', ''),
            'auth':       (subscription.get('keys') or {}).get('auth', ''),
            'user_id':    user_id or None,
        }
        # Upsert by endpoint
        requests.post(
            f"{SUPABASE_URL}/rest/v1/push_subscriptions",
            headers={**_sb_headers(), 'Prefer': 'resolution=merge-duplicates'},
            json=payload
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/send-daily-notifications', methods=['POST'])
def send_daily_notifications():
    """Called by Railway cron daily. Sends a thinking prompt to all subscribers."""
    # Simple auth: require a secret header
    secret = request.headers.get('X-Cron-Secret', '')
    if secret != os.environ.get('CRON_SECRET', ''):
        return jsonify({'error': 'Unauthorized'}), 401

    if not VAPID_PRIVATE_KEY or not SUPABASE_SERVICE:
        return jsonify({'error': 'Not configured'}), 503

    import json as _json
    try:
        from pywebpush import webpush, WebPushException

        # Fetch all subscriptions
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/push_subscriptions",
            headers={**_sb_headers(), 'Prefer': 'return=representation'},
            params={'limit': '1000'}
        )
        subs = resp.json() if resp.ok else []

        PROMPTS = [
            "What's one thing you've been avoiding thinking about?",
            "What decision have you been putting off? Take 2 minutes with it.",
            "What would your future self tell you about today?",
            "What assumption are you making that might not be true?",
            "Who or what is draining your energy right now?",
            "What's the real question underneath your biggest worry?",
            "If you couldn't fail, what would you do today?",
            "What are you pretending not to know?",
        ]
        import random, datetime
        prompt = PROMPTS[datetime.date.today().toordinal() % len(PROMPTS)]

        sent = 0
        failed = 0
        for sub in subs:
            try:
                subscription_info = {
                    'endpoint': sub['endpoint'],
                    'keys': {'p256dh': sub['p256dh'], 'auth': sub['auth']}
                }
                webpush(
                    subscription_info=subscription_info,
                    data=_json.dumps({
                        'title': 'ThinkOS',
                        'body':  prompt,
                        'icon':  '/icons/icon-192.png',
                        'url':   '/'
                    }),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={'sub': VAPID_EMAIL}
                )
                sent += 1
            except WebPushException as e:
                failed += 1
                # Remove expired/invalid subscriptions
                if '410' in str(e) or '404' in str(e):
                    requests.delete(
                        f"{SUPABASE_URL}/rest/v1/push_subscriptions",
                        headers=_sb_headers(),
                        params={'endpoint': f"eq.{sub['endpoint']}"}
                    )

        return jsonify({'ok': True, 'sent': sent, 'failed': failed})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  ThinkOS running at http://localhost:{port}\n')
    print(f'  Model: {MODEL}')
    print(f'  Key: {"set" if OPENROUTER_KEY else "MISSING — add OPENROUTER_API_KEY to .env"}\n')
    app.run(debug=True, port=port, host='0.0.0.0')
