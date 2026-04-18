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


# ─── Stripe Checkout ───────────────────────────────────────────────────────────

@app.route('/api/create-checkout', methods=['POST'])
def create_checkout():
    if not STRIPE_SECRET_KEY:
        return jsonify({'error': 'Payments not configured yet'}), 503
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        data      = request.get_json() or {}
        plan      = data.get('plan', 'monthly')          # monthly | annual | lifetime
        email     = data.get('email', '')
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
            success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/",
            allow_promotion_codes=True,
        )
        if email:
            params['customer_email'] = email

        session = stripe.checkout.Session.create(**params)
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  ThinkOS running at http://localhost:{port}\n')
    print(f'  Model: {MODEL}')
    print(f'  Key: {"set" if OPENROUTER_KEY else "MISSING — add OPENROUTER_API_KEY to .env"}\n')
    app.run(debug=True, port=port, host='0.0.0.0')
