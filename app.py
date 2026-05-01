from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import anthropic
import os

load_dotenv()

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def clean(value):
    return value.replace("_", " ").title() if value else ""

def ask_ai(prompt):
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error generating plan: {str(e)}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_post():
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    email = request.form.get("email")
    password = request.form.get("password")
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        return redirect(url_for("dashboard"))
    except Exception as e:
        return render_template("signup.html", error=str(e))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    email = request.form.get("email")
    password = request.form.get("password")
    try:
        supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return redirect(url_for("dashboard"))
    except Exception as e:
        return render_template("login.html", error="Invalid email or password")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/plan/hair")
def plan_hair():
    return render_template("form_hair.html")

@app.route("/plan/hair", methods=["POST"])
def plan_hair_post():
    face_shape = clean(request.form.get("face_shape"))
    hair_texture = clean(request.form.get("hair_texture"))
    hair_thickness = clean(request.form.get("hair_thickness"))
    maintenance = clean(request.form.get("maintenance"))
    lifestyle = clean(request.form.get("lifestyle"))
    beard_density = clean(request.form.get("beard_density"))
    beard_style = clean(request.form.get("beard_style"))

    prompt = f"""
    You are a master barber and men's grooming expert with 20 years of experience.
    
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
    Use the emoji headers exactly as shown above.
    """

    result = ask_ai(prompt)
    return render_template("results.html", result=result, title="Your Hair & Beard Plan", emoji="✂️")

@app.route("/plan/style")
def plan_style():
    return render_template("form_style.html")

@app.route("/plan/style", methods=["POST"])
def plan_style_post():
    body_type = clean(request.form.get("body_type"))
    height = clean(request.form.get("height"))
    skin_tone = clean(request.form.get("skin_tone"))
    style_pref = clean(request.form.get("style_pref"))
    occasion = clean(request.form.get("occasion"))
    budget = clean(request.form.get("budget"))

    prompt = f"""
    You are a professional men's fashion stylist with 15 years of experience dressing men of all body types.
    
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
    Use the emoji headers exactly as shown above.
    """

    result = ask_ai(prompt)
    return render_template("results.html", result=result, title="Your Style Plan", emoji="👔")

@app.route("/plan/fitness")
def plan_fitness():
    return render_template("form_fitness.html")

@app.route("/plan/fitness", methods=["POST"])
def plan_fitness_post():
    body_type = clean(request.form.get("body_type"))
    goal = clean(request.form.get("goal"))
    activity = clean(request.form.get("activity"))
    days = clean(request.form.get("days"))
    equipment = clean(request.form.get("equipment"))

    prompt = f"""
    You are an elite personal trainer and fitness coach who has trained hundreds of men.
    
    You follow these strict professional rules:
    - Always match workout intensity to current activity level
    - Never recommend advanced exercises to beginners
    - Always include specific sets and reps
    - Always include nutrition advice specific to their goal
    - Always explain the reasoning behind the program
    
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
    Use the emoji headers exactly as shown above.
    """

    result = ask_ai(prompt)
    return render_template("results.html", result=result, title="Your Fitness Plan", emoji="💪")

@app.route("/plan/skin")
def plan_skin():
    return render_template("form_skin.html")

@app.route("/plan/skin", methods=["POST"])
def plan_skin_post():
    skin_type = clean(request.form.get("skin_type"))
    concern = clean(request.form.get("concern"))
    routine = clean(request.form.get("routine"))
    age = clean(request.form.get("age"))

    prompt = f"""
    You are a professional skincare consultant with deep knowledge of men's skin.
    
    You follow these strict professional rules:
    - Always match routine complexity to current routine level
    - Never recommend too many products at once
    - Always explain why each product type is needed
    - Always remind to consult a dermatologist for serious concerns
    - Focus on simple, effective, affordable routines
    
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
    
    ⚠️ IMPORTANT: Always remind them that for serious skin concerns they should consult a dermatologist.
    
    Be specific, practical and clear.
    Do not use markdown formatting like ** or ##.
    Use the emoji headers exactly as shown above.
    """

    result = ask_ai(prompt)
    return render_template("results.html", result=result, title="Your Skincare Plan", emoji="🧴")

if __name__ == "__main__":
    app.run(debug=True)