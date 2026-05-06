from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import base64
import os

from lib.claude_client import get_claude, ask_claude, ask_claude_vision, ask_claude_json
from lib.supabase_client import get_supabase
from lib.auth import login_required, set_user_session, clear_user_session
from lib.i18n import get_language, t, is_rtl

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Expose i18n helpers to all templates
@app.context_processor
def inject_i18n():
    return {"t": t, "get_language": get_language, "is_rtl": is_rtl}


def clean(value):
    return value.replace("_", " ").title() if value else ""


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
    email = request.form.get("email")
    password = request.form.get("password")
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        user = response.user
        if user:
            set_user_session(user.id)
        return redirect(url_for("dashboard"))
    except Exception as e:
        return render_template("signup.html", error=str(e))


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
            set_user_session(user.id)
        return redirect(url_for("dashboard"))
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
    return render_template("dashboard.html")


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


if __name__ == "__main__":
    app.run(debug=True)
