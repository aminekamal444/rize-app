from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import base64
import io
import json
import os
from datetime import date, datetime, timezone

from lib.claude_client import get_claude, ask_claude, ask_claude_vision, ask_claude_json
from lib.supabase_client import get_supabase, get_authed_supabase, get_admin_supabase
from lib.auth import login_required, set_user_session, clear_user_session, get_current_user, get_supabase_tokens
from lib.i18n import get_language, t, is_rtl
from lib.image_utils import thumbnail_for_baseline, to_base64
from lib.prompts.baseline_score import build_baseline_score_prompt
from lib.prompts.plan_generator import build_plan_prompt, build_compact_plan_prompt, build_chunked_plan_prompt

load_dotenv()


def _safe_int(value, default=0):
    """Coerce value to int, falling back to default for None or invalid."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Expose i18n helpers to all templates
@app.context_processor
def inject_i18n():
    return {"t": t, "get_language": get_language, "is_rtl": is_rtl}

@app.context_processor
def inject_layout_flags():
    from flask import request
    show_lang_switcher = request.endpoint in (
        "home",
        "signup",
        "login",
        "onboarding_language",
    )
    show_main_nav = request.endpoint in (
        "today",
        "plan_calendar",
    )
    return {"show_lang_switcher": show_lang_switcher, "show_main_nav": show_main_nav}


def clean(value):
    return value.replace("_", " ").title() if value else ""


# ---------------------------------------------------------------------------
# Onboarding helpers
# ---------------------------------------------------------------------------

def _db():
    """
    Return a Supabase client for backend operations.

    Uses service-role key (bypasses RLS) because the supabase-py SDK does
    not reliably propagate user JWT auth via set_session(). Security is
    enforced at the app level:
      - @login_required verifies authenticated user via Flask session
      - user_id always comes from get_current_user() (Flask session)
      - All queries explicitly scoped: .eq("user_id", user_id)
      - No user-supplied input determines user_id

    RLS policies remain in place as defense-in-depth.
    """
    return get_admin_supabase()


def require_onboarding_complete():
    """
    Return a redirect response if the current user has not completed onboarding.
    Returns None if onboarding is complete (no action needed).

    Usage in a route:
        guard = require_onboarding_complete()
        if guard:
            return guard
    """
    user_id = get_current_user()
    if not user_id:
        return redirect(url_for("login"))
    try:
        db = _db()
        result = db.table("profiles").select("onboarding_complete").eq("id", user_id).single().execute()
        profile = result.data
        if not profile or not profile.get("onboarding_complete"):
            return redirect(url_for("onboarding"))
    except Exception:
        return redirect(url_for("onboarding"))
    return None


# ---------------------------------------------------------------------------
# Language switcher
# ---------------------------------------------------------------------------

@app.route("/lang/<lang_code>")
def set_language(lang_code):
    if lang_code in ("fr", "en", "ar"):
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    supabase = get_supabase()
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not email or not password:
        return render_template("signup.html", error="Email and password are required.", email=email)
    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match.", email=email)
    if len(password) < 6:
        return render_template("signup.html", error="Password must be at least 6 characters.", email=email)

    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        user = response.user
        if user:
            access_token = ""
            refresh_token = ""
            if response.session:
                access_token = response.session.access_token or ""
                refresh_token = response.session.refresh_token or ""
            set_user_session(user.id, access_token, refresh_token)
            return redirect(url_for("onboarding"))
        return render_template("signup.html", error="Could not create account. Please try again.", email=email)
    except Exception as e:
        return render_template("signup.html", error=str(e), email=email)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    supabase = get_supabase()
    email = request.form.get("email")
    password = request.form.get("password")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        user = response.user
        if user:
            # Store JWT tokens for authenticated DB/storage operations
            access_token = ""
            refresh_token = ""
            if response.session:
                access_token = response.session.access_token or ""
                refresh_token = response.session.refresh_token or ""
            set_user_session(user.id, access_token, refresh_token)
        return redirect(url_for("onboarding"))
    except Exception:
        return render_template("login.html", error="Invalid email or password")


@app.route("/logout")
def logout():
    clear_user_session()
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    guard = require_onboarding_complete()
    if guard:
        return guard
    return render_template("dashboard.html")


@app.route("/today")
@login_required
def today():
    guard = require_onboarding_complete()
    if guard:
        return guard
    user_id = get_current_user()
    try:
        db = _db()
        profile_result = db.table("profiles").select(
            "display_name, archetype, journey_day, streak_current, streak_best"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        journey_day = profile.get("journey_day") or 1

        # Fetch today's plan
        plan_result = db.table("daily_plans").select(
            "id, journey_day, focus_pillar, summary, theme, is_recovery_day"
        ).eq("user_id", user_id).eq("journey_day", journey_day).execute()
        plan_rows = plan_result.data or []
        plan = plan_rows[0] if plan_rows else {}

        # Fetch actions for today's plan
        actions = []
        if plan.get("id"):
            actions_result = db.table("daily_actions").select(
                "id, position, pillar, title, description, why, minimum, completed"
            ).eq("daily_plan_id", plan["id"]).order("position").execute()
            actions = actions_result.data or []

    except Exception:
        profile = {}
        plan = {}
        actions = []

    is_recovery = bool(plan.get("is_recovery_day"))
    all_done = is_recovery or (len(actions) > 0 and all(a.get("completed") for a in actions))
    journey_complete = (profile.get("journey_day") or 0) >= 30 and all_done

    return render_template(
        "today/index.html",
        profile=profile,
        plan=plan,
        actions=actions,
        all_done=all_done,
        is_recovery=is_recovery,
        journey_complete=journey_complete,
    )


@app.route("/today/action/<action_id>/done", methods=["POST"])
@login_required
def today_action_done(action_id):
    user_id = get_current_user()
    try:
        db = _db()
        db.table("daily_actions").update({
            "completed": True,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", action_id).eq("user_id", user_id).execute()
    except Exception:
        pass
    return redirect(url_for("today"))


@app.route("/today/complete", methods=["POST"])
@login_required
def today_complete():
    user_id = get_current_user()
    try:
        db = _db()
        profile_result = db.table("profiles").select(
            "journey_day, streak_current, streak_best"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        current_day = profile.get("journey_day") or 1
        streak = profile.get("streak_current") or 0
        best = profile.get("streak_best") or 0

        new_streak = streak + 1
        new_best = max(best, new_streak)
        # Don't advance past day 30
        new_day = min(current_day + 1, 30)

        db.table("profiles").update({
            "journey_day": new_day,
            "streak_current": new_streak,
            "streak_best": new_best,
        }).eq("id", user_id).execute()
    except Exception:
        pass
    return redirect(url_for("today"))


@app.route("/choose/<category>")
@login_required
def choose(category):
    categories = {
        "hair": {"title": "Hair & Beard", "emoji": "✂️"},
        "style": {"title": "Style & Outfits", "emoji": "👔"},
        "fitness": {"title": "Body & Fitness", "emoji": "💪"},
        "skin": {"title": "Skin & Grooming", "emoji": "🧴"},
    }
    info = categories.get(category, {"title": "Glow Up", "emoji": "✨"})
    return render_template("choose.html", category=category, title=info["title"], emoji=info["emoji"])


@app.route("/form/<category>")
@login_required
def form(category):
    forms = {
        "hair": "form_hair.html",
        "style": "form_style.html",
        "fitness": "form_fitness.html",
        "skin": "form_skin.html",
    }
    template = forms.get(category, "dashboard.html")
    return render_template(template)


@app.route("/scan/<category>", methods=["GET"])
@login_required
def scan_category(category):
    categories = {
        "hair": {"title": "Hair & Beard", "emoji": "✂️"},
        "style": {"title": "Style & Outfits", "emoji": "👔"},
        "fitness": {"title": "Body & Fitness", "emoji": "💪"},
        "skin": {"title": "Skin & Grooming", "emoji": "🧴"},
    }
    info = categories.get(category, {"title": "Glow Up", "emoji": "✨"})
    return render_template("scan.html", category=category, title=info["title"], emoji=info["emoji"])


@app.route("/scan/<category>", methods=["POST"])
@login_required
def scan_category_post(category):
    photo = request.files.get("photo")

    if not photo:
        return render_template("scan.html", error="Please upload a photo", category=category)

    image_data = base64.standard_b64encode(photo.read()).decode("utf-8")
    media_type = photo.content_type

    category_prompts = {
        "hair": "hair and beard recommendations specifically",
        "style": "style and outfit recommendations specifically",
        "fitness": "fitness and body recommendations specifically",
        "skin": "skincare and grooming recommendations specifically",
        "all": "everything — hair, beard, style, skin and fitness",
    }

    improve_text = category_prompts.get(category, "everything")

    prompt = f"""You are an expert men's glow up coach, professional barber, fashion stylist and skincare specialist.

Analyze this person's photo carefully and provide a complete personalized glow up plan.

From the photo, identify:
- Face shape (oval, round, square, heart, diamond, rectangle)
- Skin tone (light, medium, olive, dark)
- Current hair style and texture
- Facial hair status and density
- Any visible skin concerns
- Overall style and body type assessment

Then provide a detailed glow up plan focused on: {improve_text}

Structure your response with these sections:

📊 FACE ANALYSIS
Exactly what you detected from the photo — face shape, skin tone, hair type, facial hair, and overall assessment.

💇 HAIR & BEARD RECOMMENDATION
Specific haircut name and beard style for their detected face shape and why it works.

👔 STYLE RECOMMENDATION
Colors and specific outfits that suit their detected skin tone and body.

🧴 SKIN RECOMMENDATION
Routine based on visible skin condition and detected skin tone.

💪 FITNESS RECOMMENDATION
Plan based on visible body type.

🌟 TOP 3 IMMEDIATE WINS
The 3 most impactful things they can do this week.

Be specific, honest, encouraging and professional.
Do not use markdown formatting like ** or ##.
Use the emoji headers exactly as shown above."""

    try:
        result = ask_claude_vision(prompt, image_data, media_type, max_tokens=1500)
    except Exception as e:
        result = f"Error analyzing photo: {str(e)}"

    return render_template("results.html", result=result, title="Your AI Glow Up Plan", emoji="📸")


@app.route("/plan/hair", methods=["POST"])
@login_required
def plan_hair_post():
    face_shape = clean(request.form.get("face_shape"))
    hair_texture = clean(request.form.get("hair_texture"))
    hair_thickness = clean(request.form.get("hair_thickness"))
    maintenance = clean(request.form.get("maintenance"))
    lifestyle = clean(request.form.get("lifestyle"))
    beard_density = clean(request.form.get("beard_density"))
    beard_style = clean(request.form.get("beard_style"))

    prompt = f"""You are a master barber and men's grooming expert with 20 years of experience.

You follow these strict professional rules:
- Never recommend styles that add width to a round face
- Never suggest a full beard to someone with patchy growth
- Always consider maintenance time as a hard limit
- Always explain WHY a style suits their specific face shape
- Be specific with haircut names, not vague descriptions

A client has this profile:
- Face shape: {face_shape}
- Hair texture: {hair_texture}
- Hair thickness: {hair_thickness}
- Daily maintenance time: {maintenance}
- Lifestyle: {lifestyle}
- Beard density: {beard_density}
- Beard style preference: {beard_style}

Give them a detailed, specific, personalized recommendation covering:

💇 HAIRCUT RECOMMENDATION
The exact haircut name and why it suits their face shape and hair type.

✂️ HOW TO STYLE IT
Step by step daily styling routine that fits their maintenance time.

🧔 BEARD RECOMMENDATION
The best beard style for their face shape and density and exactly why.

🪒 DAILY GROOMING ROUTINE
A simple morning and night routine.

Be specific, practical, encouraging and professional.
Do not use markdown formatting like ** or ##.
Use the emoji headers exactly as shown above."""

    result = ask_claude(prompt)
    return render_template("results.html", result=result, title="Your Hair & Beard Plan", emoji="✂️")


@app.route("/plan/style", methods=["POST"])
@login_required
def plan_style_post():
    body_type = clean(request.form.get("body_type"))
    height = clean(request.form.get("height"))
    skin_tone = clean(request.form.get("skin_tone"))
    style_pref = clean(request.form.get("style_pref"))
    occasion = clean(request.form.get("occasion"))
    budget = clean(request.form.get("budget"))

    prompt = f"""You are a professional men's fashion stylist with 15 years of experience.

You follow these strict professional rules:
- Always base color recommendations on skin tone science
- Always consider body proportions when recommending fits
- Never give generic advice — every recommendation must be specific to this person
- Always explain why each recommendation works for their specific profile

A client has this profile:
- Body type: {body_type}
- Height: {height}
- Skin tone: {skin_tone}
- Style preference: {style_pref}
- Main occasion: {occasion}
- Budget: {budget}

Give them a detailed personalized style plan covering:

👔 YOUR STYLE IDENTITY
Their style type and what makes them look best.

🎨 YOUR COLOR PALETTE
Specific colors that suit their skin tone and colors to avoid.

👗 OUTFIT COMBINATIONS
3 specific complete outfits they should wear.

🛍️ WARDROBE ESSENTIALS
The 5 most important items to own based on their profile.

⚠️ WHAT TO AVOID
Specific things that don't work for their body type and style.

Be specific, practical and inspiring.
Do not use markdown formatting like ** or ##.
Use the emoji headers exactly as shown above."""

    result = ask_claude(prompt)
    return render_template("results.html", result=result, title="Your Style Plan", emoji="👔")


@app.route("/plan/fitness", methods=["POST"])
@login_required
def plan_fitness_post():
    body_type = clean(request.form.get("body_type"))
    goal = clean(request.form.get("goal"))
    activity = clean(request.form.get("activity"))
    days = clean(request.form.get("days"))
    equipment = clean(request.form.get("equipment"))

    prompt = f"""You are an elite personal trainer and fitness coach.

You follow these strict professional rules:
- Always match workout intensity to current activity level
- Never recommend advanced exercises to beginners
- Always include specific sets and reps
- Always include nutrition advice specific to their goal

A client has this profile:
- Current body type: {body_type}
- Main fitness goal: {goal}
- Current activity level: {activity}
- Training days per week: {days}
- Available equipment: {equipment}

Give them a detailed personalized fitness plan covering:

💪 YOUR WORKOUT PLAN
A specific weekly schedule with exercises, sets and reps.

🥗 NUTRITION STRATEGY
Specific nutrition advice for their goal including protein targets.

😴 RECOVERY PROTOCOL
Sleep and recovery advice to maximize results.

📈 PROGRESSION PLAN
How to progress over the next 4 weeks.

⚡ MINDSET TIPS
3 practical tips to stay consistent.

Be specific, practical and motivating.
Do not use markdown formatting like ** or ##.
Use the emoji headers exactly as shown above."""

    result = ask_claude(prompt)
    return render_template("results.html", result=result, title="Your Fitness Plan", emoji="💪")


@app.route("/score")
@login_required
def score():
    return render_template("score.html")


@app.route("/score", methods=["POST"])
@login_required
def score_post():
    photo = request.files.get("photo")
    age = request.form.get("age", "").strip()

    if not photo:
        return render_template("score.html", error="Please upload a photo")

    image_data = base64.standard_b64encode(photo.read()).decode("utf-8")
    media_type = photo.content_type

    prompt = f"""You are an elite men's image consultant scoring a client's overall presentation.

Analyze this photo and provide an honest, calibrated score across four categories. Be realistic — most people score between 50 and 75. Reserve 85+ for genuinely exceptional presentation. Reserve under 40 only for serious issues. Do not inflate scores to be polite.

Score these four categories from 0 to 100:
- HAIR: cut quality, condition, suitability for face shape, styling
- STYLE: outfit, fit, color harmony, overall presentation
- FITNESS: visible body composition, posture, athleticism
- SKIN: clarity, hydration, grooming, evenness

Then identify:
- A short tagline (2 to 4 words) describing their archetype, in title case (examples: Untapped Potential, Quiet Powerhouse, Diamond In Rough, The Modern Gentleman)
- Their single biggest visible strength, in one short sentence
- Their single biggest area for improvement, in one short sentence

Client age range: {age or "not specified"}

Respond with ONLY valid JSON. No preamble, no markdown fences, no commentary. Use this exact schema:
{{
  "hair": <integer 0 to 100>,
  "style": <integer 0 to 100>,
  "fitness": <integer 0 to 100>,
  "skin": <integer 0 to 100>,
  "overall": <integer 0 to 100, weighted average>,
  "tagline": "<2 to 4 words, title case>",
  "strength": "<one short sentence>",
  "improvement": "<one short sentence>"
}}"""

    try:
        scores = ask_claude_json(prompt, max_tokens=600, image_base64=image_data, media_type=media_type)

        for k in ("hair", "style", "fitness", "skin", "overall"):
            scores[k] = max(0, min(100, int(scores.get(k, 50))))
        scores["tagline"] = scores.get("tagline", "Glow Up Mode")
        scores["strength"] = scores.get("strength", "")
        scores["improvement"] = scores.get("improvement", "")

    except (ValueError, KeyError):
        return render_template("score.html", error="Could not read the score from your photo. Try a clearer front-facing shot in good lighting.")
    except Exception as e:
        return render_template("score.html", error=f"Something went wrong: {str(e)}")

    return render_template("score_card.html", scores=scores)


@app.route("/plan/skin", methods=["POST"])
@login_required
def plan_skin_post():
    skin_type = clean(request.form.get("skin_type"))
    concern = clean(request.form.get("concern"))
    routine = clean(request.form.get("routine"))
    age = clean(request.form.get("age"))

    prompt = f"""You are a professional skincare consultant with deep knowledge of men's skin.

You follow these strict professional rules:
- Always match routine complexity to current routine level
- Never recommend too many products at once
- Always explain why each product type is needed
- Always remind to consult a dermatologist for serious concerns

A client has this profile:
- Skin type: {skin_type}
- Main skin concern: {concern}
- Current routine: {routine}
- Age range: {age}

Give them a detailed personalized skincare plan covering:

🌅 MORNING ROUTINE
Step by step with specific product types and why each one.

🌙 NIGHT ROUTINE
Step by step with specific product types and why each one.

🧪 KEY INGREDIENTS TO LOOK FOR
Specific ingredients that target their concern.

❌ WHAT TO AVOID
Ingredients and habits that make their concern worse.

📅 WEEKLY TREATMENTS
Additional treatments to add once or twice a week.

Always remind them to consult a dermatologist for serious concerns.
Do not use markdown formatting like ** or ##.
Use the emoji headers exactly as shown above."""

    result = ask_claude(prompt)
    return render_template("results.html", result=result, title="Your Skincare Plan", emoji="🧴")


# ===========================================================================
# ONBOARDING FLOW
# ===========================================================================

MOROCCAN_CITIES = [
    "Casablanca", "Rabat", "Fès", "Marrakech", "Tanger", "Agadir",
    "Meknès", "Oujda", "Kénitra", "Tétouan", "Laâyoune", "Mohammedia",
    "El Jadida", "Béni Mellal", "Nador", "Settat", "Berrechid",
    "Khémisset", "Inzegan", "Safi",
]


@app.route("/onboarding")
@login_required
def onboarding():
    """Entry point: redirect user to the correct step based on onboarding_step."""
    user_id = get_current_user()
    try:
        db = _db()
        result = db.table("profiles").select(
            "onboarding_complete, onboarding_step"
        ).eq("id", user_id).single().execute()
        profile = result.data or {}
    except Exception:
        profile = {}

    if profile.get("onboarding_complete"):
        return redirect(url_for("today"))

    step = profile.get("onboarding_step", 0)
    step_map = {
        0: "onboarding_language",
        1: "onboarding_profile",
        2: "onboarding_goal",
        3: "onboarding_lifestyle",
        4: "onboarding_photo_1",
        5: "onboarding_analyzing",
        6: "onboarding_reveal",
        7: "onboarding_plan_reveal",
    }
    return redirect(url_for(step_map.get(step, "onboarding_language")))


# ---------------------------------------------------------------------------
# Step 1 — Language picker
# ---------------------------------------------------------------------------

@app.route("/onboarding/language", methods=["GET"])
@login_required
def onboarding_language():
    return render_template("onboarding/language.html")


@app.route("/onboarding/language", methods=["POST"])
@login_required
def onboarding_language_post():
    user_id = get_current_user()
    lang = request.form.get("language", "fr")
    if lang not in ("fr", "en", "ar"):
        lang = "fr"

    session["lang"] = lang

    try:
        db = _db()
        db.table("profiles").update({
            "preferred_language": lang,
            "onboarding_step": 1,
        }).eq("id", user_id).execute()
    except Exception:
        pass  # Non-fatal: session lang is already set

    return redirect(url_for("onboarding_profile"))


# ---------------------------------------------------------------------------
# Step 2 — Profile basics
# ---------------------------------------------------------------------------

@app.route("/onboarding/profile", methods=["GET"])
@login_required
def onboarding_profile():
    return render_template("onboarding/profile.html", cities=MOROCCAN_CITIES)


@app.route("/onboarding/profile", methods=["POST"])
@login_required
def onboarding_profile_post():
    user_id = get_current_user()
    display_name = (request.form.get("display_name") or "").strip()
    city = (request.form.get("city") or "").strip()
    age_range = (request.form.get("age_range") or "").strip()

    # Map age range string to a representative integer for the age column
    age_range_map = {
        "under_20": 18,
        "20_25": 22,
        "25_30": 27,
        "30_plus": 32,
    }

    error = None
    if not display_name:
        error = t("onboarding.profile.error.name")
    elif age_range not in age_range_map:
        error = t("onboarding.profile.error.age")

    if error:
        return render_template("onboarding/profile.html", cities=MOROCCAN_CITIES, error=error,
                               display_name=display_name, city=city, age_range=age_range)

    try:
        db = _db()
        db.table("profiles").update({
            "display_name": display_name,
            "city": city,
            "age": age_range_map[age_range],
            "onboarding_step": 2,
        }).eq("id", user_id).execute()
    except Exception as exc:
        return render_template("onboarding/profile.html", cities=MOROCCAN_CITIES,
                               error=str(exc), display_name=display_name, city=city, age_range=age_range)

    return redirect(url_for("onboarding_goal"))


# ---------------------------------------------------------------------------
# Step 3 — Biggest goal
# ---------------------------------------------------------------------------

@app.route("/onboarding/goal", methods=["GET"])
@login_required
def onboarding_goal():
    return render_template("onboarding/goal.html")


@app.route("/onboarding/goal", methods=["POST"])
@login_required
def onboarding_goal_post():
    user_id = get_current_user()
    goals = request.form.getlist("goals")
    context = (request.form.get("context") or "").strip()

    if not goals:
        return render_template("onboarding/goal.html",
                               error=t("onboarding.goal.error_no_selection"))
    if len(goals) > 5:
        return render_template("onboarding/goal.html",
                               error=t("onboarding.goal.error_max_selection"))

    try:
        db = _db()
        db.table("profiles").update({
            "biggest_goal": json.dumps(goals),
            "biggest_insecurity": context,
            "onboarding_step": 3,
        }).eq("id", user_id).execute()
    except Exception as exc:
        return render_template("onboarding/goal.html", error=str(exc))

    return redirect(url_for("onboarding_lifestyle"))


# ---------------------------------------------------------------------------
# Step 4 — Lifestyle check
# ---------------------------------------------------------------------------

@app.route("/onboarding/lifestyle", methods=["GET"])
@login_required
def onboarding_lifestyle():
    return render_template("onboarding/lifestyle.html")


@app.route("/onboarding/lifestyle", methods=["POST"])
@login_required
def onboarding_lifestyle_post():
    user_id = get_current_user()

    daily_pattern = request.form.get("daily_pattern", "")
    activity_level = request.form.get("activity_level", "")
    upcoming_context = (request.form.get("upcoming_context") or "").strip()

    valid_patterns = {"mostly_sitting", "mostly_active", "mixed"}
    valid_activity = {"sedentary", "occasional", "regular", "athletic"}

    if daily_pattern not in valid_patterns or activity_level not in valid_activity:
        return render_template("onboarding/lifestyle.html",
                               error=t("onboarding.lifestyle.error_required"))

    try:
        admin = get_admin_supabase()
        admin.table("profiles").update({
            "daily_pattern": daily_pattern,
            "activity_level": activity_level,
            "upcoming_context": upcoming_context,
            "onboarding_step": 4,
        }).eq("id", user_id).execute()
    except Exception as exc:
        return render_template("onboarding/lifestyle.html", error=str(exc))

    return redirect(url_for("onboarding_photo_1"))


# ---------------------------------------------------------------------------
# Step 5 — Baseline photo upload (3-photo sequential flow)
# ---------------------------------------------------------------------------

@app.route("/onboarding/photo-1")
@login_required
def onboarding_photo_1():
    return render_template("onboarding/photo_1.html")


@app.route("/onboarding/photo-2")
@login_required
def onboarding_photo_2():
    user_id = get_current_user()
    try:
        admin = get_admin_supabase()
        existing = admin.table("photos").select("id").eq(
            "user_id", user_id
        ).eq("type", "baseline_front").execute()
        if not existing.data:
            return redirect(url_for("onboarding_photo_1"))
    except Exception:
        return redirect(url_for("onboarding_photo_1"))
    return render_template("onboarding/photo_2.html")


@app.route("/onboarding/photo-3")
@login_required
def onboarding_photo_3():
    user_id = get_current_user()
    try:
        admin = get_admin_supabase()
        existing = admin.table("photos").select("id").eq(
            "user_id", user_id
        ).eq("type", "baseline_side").execute()
        if not existing.data:
            return redirect(url_for("onboarding_photo_2"))
    except Exception:
        return redirect(url_for("onboarding_photo_2"))
    return render_template("onboarding/photo_3.html")


@app.route("/onboarding/photo-upload", methods=["POST"])
@login_required
def onboarding_photo_upload():
    user_id = get_current_user()
    photo = request.files.get("photo")
    photo_type = request.form.get("photo_type")

    valid_types = ["baseline_front", "baseline_side", "baseline_body"]
    if not photo or photo_type not in valid_types:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    if not (photo.content_type or "").startswith("image/"):
        return jsonify({"success": False,
                        "error": t("onboarding.photo.error.invalid")}), 400

    try:
        compressed = thumbnail_for_baseline(photo)
        compressed_bytes = compressed.read()
        storage_path = f"{user_id}/{photo_type}.jpg"

        admin = get_admin_supabase()

        # Remove existing file for this type (retake support)
        try:
            admin.storage.from_("progress-photos").remove([storage_path])
        except Exception:
            pass

        admin.storage.from_("progress-photos").upload(
            storage_path,
            compressed_bytes,
            {"content-type": "image/jpeg"},
        )

        # Upsert photos table row
        existing = admin.table("photos").select("id").eq(
            "user_id", user_id
        ).eq("type", photo_type).execute()

        if existing.data:
            admin.table("photos").update({
                "storage_path": storage_path,
                "bucket": "progress-photos",
                "journey_day": 0,
                "score_overall": None,
                "score_hair": None,
                "score_style": None,
                "score_fitness": None,
                "score_skin": None,
                "strength": None,
                "improvement": None,
                "observations": None,
            }).eq("user_id", user_id).eq("type", photo_type).execute()
        else:
            admin.table("photos").insert({
                "user_id": user_id,
                "type": photo_type,
                "storage_path": storage_path,
                "bucket": "progress-photos",
                "journey_day": 0,
            }).execute()

        # Update onboarding_step
        step_map = {
            "baseline_front": 4,
            "baseline_side": 4,
            "baseline_body": 5,
        }
        admin.table("profiles").update({
            "onboarding_step": step_map[photo_type]
        }).eq("id", user_id).execute()

        next_url_map = {
            "baseline_front": url_for("onboarding_photo_2"),
            "baseline_side": url_for("onboarding_photo_3"),
            "baseline_body": url_for("onboarding_analyzing"),
        }

        return jsonify({"success": True, "next": next_url_map[photo_type]})

    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    return redirect(url_for("onboarding_analyzing"))


# ---------------------------------------------------------------------------
# Step 6 — Analyzing (loading screen + AI call)
# ---------------------------------------------------------------------------

@app.route("/onboarding/analyzing", methods=["GET"])
@login_required
def onboarding_analyzing():
    user_id = get_current_user()

    # Try to generate a signed URL for the front-face photo (shown on loading screen)
    photo_url = None
    try:
        admin = get_admin_supabase()
        front_result = admin.table("photos").select("storage_path").eq(
            "user_id", user_id
        ).in_("type", ["baseline_front", "baseline"]).execute()
        front_rows = front_result.data or []
        if front_rows:
            photo_path = front_rows[0]["storage_path"]
            signed = admin.storage.from_("progress-photos").create_signed_url(photo_path, 300)
            photo_url = signed.get("signedURL") or signed.get("signedUrl")
    except Exception:
        pass

    return render_template("onboarding/analyzing.html", photo_url=photo_url)


@app.route("/onboarding/analyzing", methods=["POST"])
@login_required
def onboarding_analyzing_post():
    user_id = get_current_user()

    try:
        db = _db()
        admin = get_admin_supabase()

        # Fetch profile data for the prompt
        profile_result = db.table("profiles").select(
            "preferred_language, biggest_goal, biggest_insecurity, "
            "daily_pattern, activity_level, upcoming_context"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        language = profile.get("preferred_language") or get_language()

        # biggest_goal is a JSON array string (multi-select)
        raw_goals = profile.get("biggest_goal") or "[]"
        try:
            goals_list = json.loads(raw_goals) if raw_goals else []
            if not isinstance(goals_list, list):
                goals_list = [str(goals_list)] if goals_list else []
        except (json.JSONDecodeError, TypeError):
            goals_list = [str(raw_goals)] if raw_goals else []
        biggest_goal = ", ".join(goals_list)

        biggest_insecurity = profile.get("biggest_insecurity") or ""

        # Fetch all baseline photos for this user (new 3-photo or old single-photo)
        photos_result = admin.table("photos").select(
            "type, storage_path"
        ).eq("user_id", user_id).in_(
            "type", ["baseline_front", "baseline_side", "baseline_body", "baseline"]
        ).execute()

        photo_data = {}
        front_photo_id = None
        for photo_row in (photos_result.data or []):
            try:
                photo_bytes = admin.storage.from_(
                    "progress-photos"
                ).download(photo_row["storage_path"])
                photo_data[photo_row["type"]] = base64.standard_b64encode(
                    photo_bytes
                ).decode("utf-8")
            except Exception:
                pass

        # Support both new 3-photo flow and old single-photo flow
        photo_front_b64 = photo_data.get("baseline_front") or photo_data.get("baseline")
        photo_side_b64 = photo_data.get("baseline_side")
        photo_body_b64 = photo_data.get("baseline_body")

        # Build images list for Claude Vision (only include photos that exist)
        images = []
        if photo_front_b64:
            images.append({"b64": photo_front_b64, "label": "front_face"})
        if photo_side_b64:
            images.append({"b64": photo_side_b64, "label": "side_profile"})
        if photo_body_b64:
            images.append({"b64": photo_body_b64, "label": "upper_body"})

        if not images:
            return render_template("onboarding/analyzing.html",
                                   error=t("onboarding.analyzing.error"))

        # Build and send the prompt with all available photos
        prompt = build_baseline_score_prompt(
            language,
            biggest_goal,
            biggest_insecurity,
            daily_pattern=profile.get("daily_pattern") or "",
            activity_level=profile.get("activity_level") or "",
            upcoming_context=profile.get("upcoming_context") or "",
        )
        result = ask_claude_json(
            prompt,
            max_tokens=1000,
            images=images,
        )

        scores = result.get("scores", {})
        current_archetype = result.get("current_archetype", "")
        target_archetype = result.get("target_archetype", "")
        strength = result.get("strength", "")
        improvement = result.get("improvement", "")
        observations = result.get("observations", [])

        # Clamp scores
        for k in ("hair", "style", "fitness", "skin", "overall"):
            scores[k] = max(0, min(100, int(scores.get(k, 50))))

        # Save scores to the front-face photo row (primary reference for scores)
        front_photo_result = admin.table("photos").select("id").eq(
            "user_id", user_id
        ).in_("type", ["baseline_front", "baseline"]).execute()
        front_photo_rows = front_photo_result.data or []
        if front_photo_rows:
            front_photo_id = front_photo_rows[0]["id"]
            db.table("photos").update({
                "score_overall": scores.get("overall"),
                "score_hair": scores.get("hair"),
                "score_style": scores.get("style"),
                "score_fitness": scores.get("fitness"),
                "score_skin": scores.get("skin"),
                "strength": strength,
                "improvement": improvement,
                "observations": json.dumps(observations),
            }).eq("id", front_photo_id).execute()

        # Save archetype + baseline_score to profiles
        db.table("profiles").update({
            "archetype": current_archetype,
            "target_archetype": target_archetype,
            "baseline_score": scores.get("overall"),
            "onboarding_step": 6,
        }).eq("id", user_id).execute()

        # Clear any legacy session keys from old single-photo flow
        session.pop("baseline_photo_path", None)
        session.pop("baseline_photo_id", None)

    except ValueError as exc:
        return render_template("onboarding/analyzing.html",
                               error=t("onboarding.analyzing.error") + f" ({exc})")
    except Exception as exc:
        return render_template("onboarding/analyzing.html",
                               error=t("onboarding.analyzing.error") + f" ({exc})")

    return redirect(url_for("onboarding_reveal"))


# ---------------------------------------------------------------------------
# Step 6b — Archetype reveal
# ---------------------------------------------------------------------------

@app.route("/onboarding/reveal", methods=["GET"])
@login_required
def onboarding_reveal():
    user_id = get_current_user()
    try:
        db = _db()

        profile_result = db.table("profiles").select(
            "archetype, target_archetype, baseline_score"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        # Fetch scores + observations — try baseline_front first (3-photo flow),
        # fall back to baseline for legacy single-photo users
        admin = get_admin_supabase()
        photo_result = admin.table("photos").select(
            "score_hair, score_style, score_fitness, score_skin, score_overall, "
            "strength, improvement, observations"
        ).eq("user_id", user_id).eq("type", "baseline_front").order("created_at", desc=True).limit(1).execute()
        if not photo_result.data:
            photo_result = admin.table("photos").select(
                "score_hair, score_style, score_fitness, score_skin, score_overall, "
                "strength, improvement, observations"
            ).eq("user_id", user_id).eq("type", "baseline").order("created_at", desc=True).limit(1).execute()
        photo = (photo_result.data or [{}])[0]

        observations_raw = photo.get("observations")
        if isinstance(observations_raw, str):
            try:
                observations = json.loads(observations_raw)
            except (json.JSONDecodeError, TypeError):
                observations = []
        elif isinstance(observations_raw, list):
            observations = observations_raw
        else:
            observations = []

        scores = {
            "hair": _safe_int(photo.get("score_hair")),
            "style": _safe_int(photo.get("score_style")),
            "fitness": _safe_int(photo.get("score_fitness")),
            "skin": _safe_int(photo.get("score_skin")),
            "overall": _safe_int(
                photo.get("score_overall") or profile.get("baseline_score")
            ),
        }

    except Exception:
        profile = {}
        scores = {"hair": 0, "style": 0, "fitness": 0, "skin": 0, "overall": 0}
        observations = []
        photo = {}

    return render_template("onboarding/reveal.html",
                           profile=profile,
                           scores=scores,
                           observations=observations,
                           strength=photo.get("strength", ""),
                           improvement=photo.get("improvement", ""))


# ---------------------------------------------------------------------------
# Step 7 — Plan generation
# ---------------------------------------------------------------------------

@app.route("/onboarding/plan", methods=["GET"])
@login_required
def onboarding_plan():
    return render_template("onboarding/plan.html")


@app.route("/onboarding/plan", methods=["POST"])
@login_required
def onboarding_plan_post():
    user_id = get_current_user()
    try:
        db = _db()

        # Fetch full profile
        profile_result = db.table("profiles").select(
            "display_name, biggest_goal, biggest_insecurity, archetype, "
            "target_archetype, preferred_language, "
            "daily_pattern, activity_level, upcoming_context"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        # Fetch baseline photo observations and scores — try baseline_front first
        # (3-photo flow), fall back to baseline for legacy single-photo users
        photo_result = db.table("photos").select(
            "score_hair, score_style, score_fitness, score_skin, observations"
        ).eq("user_id", user_id).eq("type", "baseline_front").order("created_at", desc=True).limit(1).execute()
        if not photo_result.data:
            photo_result = db.table("photos").select(
                "score_hair, score_style, score_fitness, score_skin, observations"
            ).eq("user_id", user_id).eq("type", "baseline").order("created_at", desc=True).limit(1).execute()
        photo = (photo_result.data or [{}])[0]

        observations_raw = photo.get("observations")
        if isinstance(observations_raw, str):
            try:
                observations = json.loads(observations_raw)
            except (json.JSONDecodeError, TypeError):
                observations = []
        elif isinstance(observations_raw, list):
            observations = observations_raw
        else:
            observations = []

        scores = {
            "hair": _safe_int(photo.get("score_hair"), 50),
            "style": _safe_int(photo.get("score_style"), 50),
            "fitness": _safe_int(photo.get("score_fitness"), 50),
            "skin": _safe_int(photo.get("score_skin"), 50),
        }

        language = profile.get("preferred_language") or get_language()

        # biggest_goal is now a JSON array string; parse to comma-separated text
        # for the AI prompts. Falls back gracefully for old single-string format.
        raw_goals = profile.get("biggest_goal") or "[]"
        try:
            goals_list = json.loads(raw_goals) if raw_goals else []
            if not isinstance(goals_list, list):
                goals_list = [str(goals_list)] if goals_list else []
        except (json.JSONDecodeError, TypeError):
            goals_list = [str(raw_goals)] if raw_goals else []
        profile["biggest_goal"] = ", ".join(goals_list)

        # Extract lifestyle fields for prompt enrichment
        _daily_pattern = profile.get("daily_pattern") or ""
        _activity_level = profile.get("activity_level") or ""
        _upcoming_context = profile.get("upcoming_context") or ""

        # --- Generate plan in 3 chunks to avoid JSON truncation ---
        import re as _re

        def _try_generate_chunk(day_start: int, day_end: int, attempt: int) -> list:
            prompt = build_chunked_plan_prompt(
                language, profile, observations, scores, day_start, day_end,
                daily_pattern=_daily_pattern,
                activity_level=_activity_level,
                upcoming_context=_upcoming_context,
            )
            max_tokens_value = 8000
            raw = ask_claude(prompt, max_tokens=max_tokens_value)
            cleaned = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=_re.MULTILINE).strip()
            return json.loads(cleaned)

        days: list = []
        for chunk_start, chunk_end in [(1, 10), (11, 20), (21, 30)]:
            chunk = None
            for attempt in range(2):
                try:
                    chunk = _try_generate_chunk(chunk_start, chunk_end, attempt)
                    break
                except (ValueError, json.JSONDecodeError):
                    if attempt == 1:
                        raise ValueError(
                            f"Plan generation failed for days {chunk_start}–{chunk_end} after 2 attempts."
                        )
            days.extend(chunk)

        if not isinstance(days, list) or len(days) == 0:
            raise ValueError("Plan generation returned an empty or invalid result.")

        # --- Clear any existing plan data for this user ---
        # Handles retries after partial failures and prepares for future
        # "regenerate plan" feature. daily_actions has ON DELETE CASCADE on
        # daily_plans, but we delete both explicitly for clarity.
        db.table("daily_actions").delete().eq("user_id", user_id).execute()
        db.table("daily_plans").delete().eq("user_id", user_id).execute()

        # --- Insert daily_plans + daily_actions ---
        VALID_PILLARS = {"hair", "style", "fitness", "skin", "recovery"}

        PILLAR_ALIAS = {
            "posture": "fitness",
            "body": "fitness",
            "exercise": "fitness",
            "mobility": "fitness",
            "nutrition": "fitness",
            "sleep": "recovery",
            "rest": "recovery",
            "mindset": "recovery",
            "mental": "recovery",
            "wardrobe": "style",
            "clothing": "style",
            "fashion": "style",
            "outfit": "style",
            "haircut": "hair",
            "beard": "hair",
            "grooming": "skin",
            "skincare": "skin",
            "acne": "skin",
        }

        def _normalize_pillar(value: str) -> str:
            if not value:
                return "fitness"
            v = value.strip().lower()
            if v in VALID_PILLARS:
                return v
            if v in PILLAR_ALIAS:
                return PILLAR_ALIAS[v]
            return "fitness"  # final fallback

        journey_start = date.today().isoformat()
        plans_to_insert = []
        actions_to_insert = []

        for day_data in days:
            day_num = int(day_data.get("day", 0))
            if not (1 <= day_num <= 30):
                continue
            plans_to_insert.append({
                "user_id": user_id,
                "journey_day": day_num,
                "focus_pillar": _normalize_pillar(day_data.get("focus_pillar", "")),
                "summary": day_data.get("summary", ""),
                "theme": day_data.get("theme", ""),
                "is_recovery_day": bool(day_data.get("is_recovery_day", False)),
            })

        # Insert plans and collect IDs keyed by journey_day
        plan_insert_result = db.table("daily_plans").insert(plans_to_insert).execute()
        plan_id_map = {}
        for row in (plan_insert_result.data or []):
            plan_id_map[row["journey_day"]] = row["id"]

        # Build actions list now that we have plan IDs
        for day_data in days:
            day_num = int(day_data.get("day", 0))
            plan_id = plan_id_map.get(day_num)
            if not plan_id:
                continue
            for action in (day_data.get("actions") or []):
                pos = int(action.get("position", 1))
                if not (1 <= pos <= 3):
                    continue
                actions_to_insert.append({
                    "user_id": user_id,
                    "daily_plan_id": plan_id,
                    "position": pos,
                    "pillar": _normalize_pillar(action.get("pillar", "")),
                    "title": action.get("title", ""),
                    "description": action.get("description", ""),
                    "why": action.get("why", ""),
                    "minimum": action.get("minimum", ""),
                })

        if actions_to_insert:
            db.table("daily_actions").insert(actions_to_insert).execute()

        # Mark onboarding complete
        db.table("profiles").update({
            "onboarding_complete": True,
            "onboarding_step": 7,
            "journey_start_date": journey_start,
            "journey_day": 0,
        }).eq("id", user_id).execute()

    except Exception as exc:
        return render_template("onboarding/plan.html",
                               error=t("onboarding.plan.error") + f" ({exc})")

    return redirect(url_for("onboarding_plan_reveal"))


# ---------------------------------------------------------------------------
# Step 8 — Plan reveal
# ---------------------------------------------------------------------------

@app.route("/onboarding/plan-reveal", methods=["GET"])
@login_required
def onboarding_plan_reveal():
    user_id = get_current_user()
    try:
        db = _db()

        # Fetch the first 3 days with their actions
        plans_result = db.table("daily_plans").select(
            "id, journey_day, focus_pillar, summary, theme, is_recovery_day"
        ).eq("user_id", user_id).in_("journey_day", [1, 2, 3]).order("journey_day").execute()
        plans = plans_result.data or []

        # Fetch actions for days 1-3
        plan_ids = [p["id"] for p in plans]
        actions_map: dict = {}
        if plan_ids:
            actions_result = db.table("daily_actions").select(
                "daily_plan_id, position, pillar, title, description, why, minimum"
            ).in_("daily_plan_id", plan_ids).order("position").execute()
            for action in (actions_result.data or []):
                pid = action["daily_plan_id"]
                actions_map.setdefault(pid, []).append(action)

        # Attach actions to plans
        for plan in plans:
            plan["actions"] = actions_map.get(plan["id"], [])

    except Exception:
        plans = []

    return render_template("onboarding/plan_reveal.html", preview_days=plans)


@app.route("/onboarding/plan-reveal", methods=["POST"])
@login_required
def onboarding_plan_reveal_post():
    """User clicks 'Start Day 1' — set journey_day=1 and redirect to /today."""
    user_id = get_current_user()
    try:
        db = _db()
        db.table("profiles").update({"journey_day": 1}).eq("id", user_id).execute()
    except Exception:
        pass
    return redirect(url_for("today"))


@app.route("/plan-calendar")
@login_required
def plan_calendar():
    guard = require_onboarding_complete()
    if guard:
        return guard

    user_id = get_current_user()
    try:
        from collections import defaultdict

        admin = get_admin_supabase()

        # Fetch profile for journey_day and streak
        profile_result = admin.table("profiles").select(
            "journey_day, streak_current, archetype"
        ).eq("id", user_id).single().execute()
        profile = profile_result.data or {}

        journey_day = profile.get("journey_day") or 1
        streak = profile.get("streak_current") or 0
        archetype = profile.get("archetype") or ""

        # Fetch ALL daily_plans for this user (all 30 days)
        plans_result = admin.table("daily_plans").select(
            "id, journey_day, focus_pillar, theme, summary"
        ).eq("user_id", user_id).order("journey_day", desc=False).execute()
        plans = plans_result.data or []

        # Build a map: plan_id → journey_day (for joining with actions)
        plan_id_to_day = {p["id"]: p["journey_day"] for p in plans}

        # Fetch ALL daily_actions completion state
        actions_result = admin.table("daily_actions").select(
            "daily_plan_id, completed"
        ).eq("user_id", user_id).execute()
        actions = actions_result.data or []

        # Build: journey_day → list of completed booleans
        day_actions: dict = defaultdict(list)
        for action in actions:
            day_num = plan_id_to_day.get(action["daily_plan_id"])
            if day_num is not None:
                day_actions[day_num].append(action["completed"])

        # Build calendar data: list of 30 day objects
        plans_by_day = {p["journey_day"]: p for p in plans}

        calendar_days = []
        for day_num in range(1, 31):
            plan = plans_by_day.get(day_num, {})
            action_completions = day_actions.get(day_num, [])

            if day_num < journey_day:
                all_done = all(action_completions) if action_completions else False
                state = "completed" if all_done else "partial"
            elif day_num == journey_day:
                state = "current"
            else:
                state = "locked"

            calendar_days.append({
                "day": day_num,
                "state": state,
                "pillar": plan.get("focus_pillar", "") if state != "locked" else plan.get("focus_pillar", ""),
                "theme": plan.get("theme", "") if state in ("completed", "partial", "current") else "",
                "summary": plan.get("summary", "") if state in ("completed", "partial", "current") else "",
            })

        # Group into weeks
        weeks = []
        for week_num in range(4):
            start = week_num * 7
            end = start + 7
            weeks.append({
                "label": f"{t('calendar.week_label')} {week_num + 1}",
                "days": calendar_days[start:end],
            })
        # Add final days 29-30
        remaining = calendar_days[28:]
        if remaining:
            weeks.append({
                "label": t("calendar.final_days"),
                "days": remaining,
            })

    except Exception:
        journey_day = 1
        streak = 0
        archetype = ""
        weeks = []

    return render_template(
        "plan_calendar.html",
        journey_day=journey_day,
        streak=streak,
        archetype=archetype,
        weeks=weeks,
        progress_pct=round((journey_day - 1) / 30 * 100),
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
