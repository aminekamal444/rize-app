from __future__ import annotations


def build_plan_prompt(
    language: str,
    profile_dict: dict,
    observations: list,
    scores: dict,
    daily_pattern: str = "",
    activity_level: str = "",
    upcoming_context: str = "",
) -> str:
    """
    Build the prompt for 30-day plan generation.

    Returns a prompt string instructing Claude to generate a JSON array of
    30 daily plan objects, each with focus_pillar, theme, summary, and 1–3 actions.

    Parameters
    ----------
    language:       User's preferred language code ('fr', 'en', 'ar').
    profile_dict:   Dict with keys: display_name, biggest_goal,
                    biggest_insecurity, archetype, target_archetype.
    observations:   List of specific observation strings from baseline scoring.
    scores:         Dict with keys: hair, style, fitness, skin, overall.
    daily_pattern:  'mostly_sitting', 'mostly_active', or 'mixed'.
    activity_level: 'sedentary', 'occasional', 'regular', or 'athletic'.
    upcoming_context: Optional user-stated upcoming event or context.
    """
    name = profile_dict.get("display_name") or "the user"
    goal = profile_dict.get("biggest_goal") or ""
    insecurity = profile_dict.get("biggest_insecurity") or ""
    archetype = profile_dict.get("archetype") or ""
    target = profile_dict.get("target_archetype") or ""

    obs_lines = "\n".join(f"- {o}" for o in observations) if observations else "No specific observations provided."

    hair_score = scores.get("hair", 50)
    style_score = scores.get("style", 50)
    fitness_score = scores.get("fitness", 50)
    skin_score = scores.get("skin", 50)

    goals_list = [g.strip() for g in goal.split(",") if g.strip()] if goal else []
    goals_count = len(goals_list) if goals_list else 1

    return f"""You are RIZE — a glow-up coach for young men in Morocco and MENA. Speak with the warmth and directness of an older brother who's been through the same journey. Not formal. Not clinical. Wise, direct, encouraging. Use 'tu' form in French consistently. In English, contractions and natural conversational language.

Do NOT use phrases like 'let me explain' or 'interestingly' or 'let's break this down.' Just talk.

CULTURAL CONTEXT: User is in Morocco or the MENA region. Keep recommendations natively Moroccan — not Westernized. Consider:
- Climate: Mediterranean to desert — recommend breathable fabrics in summer, climate-appropriate care
- Products: Bioderma, La Roche-Posay, Avène, CeraVe, Cetaphil all at local pharmacies
- Beard culture is central — sharp grooming matters here
- Style is contemporary with European influence, grounded in local norms

Their profile:
- Name: {name}
- Priorities ({goals_count} selected): {goal}
- Current archetype: {archetype} → 30-day target: {target}
- Baseline scores — Hair: {hair_score}/100, Style: {style_score}/100, Fitness: {fitness_score}/100, Skin: {skin_score}/100

USER LIFESTYLE CONTEXT:
- Daily pattern: {daily_pattern if daily_pattern else "(not provided)"} (mostly_sitting → desk posture issues, screen skin effects; mostly_active → existing fitness baseline, different sweat/skin needs; mixed → blend both)
- Activity level: {activity_level if activity_level else "(not provided)"} (calibrate fitness actions to this — no intense training for sedentary users, no beginner work for athletic users)
- Upcoming context: {upcoming_context if upcoming_context and upcoming_context.strip() else "(none)"}

USER CONTEXT (additional): '{insecurity if insecurity and insecurity.strip() else "(none provided)"}'

If upcoming context mentions a specific event within 30 days, front-load relevant actions in days 1-14 for visible quick wins before that event.

Specific observations from their baseline photo (these heavily shape the actions):
{obs_lines}

PLAN PHILOSOPHY — LEVERAGE-FIRST DESIGN:

This is not a balanced curriculum. This is a transformation strategy optimized for the fastest visible change in 30 days.

WEEK 1 (Days 1-7) — HIGH-LEVERAGE QUICK WINS:
The user must feel visible transformation by Day 7. Front-load actions with the highest impact-per-effort ratio:
- If hair score < 75: Day 1 is 'book your barber', Day 2-3 is haircut day. Hair is the single biggest fast win.
- If style score < 60: Days 3-5 introduce ONE perfectly fitted basic (well-fitting t-shirt OR fitted chinos — not both).
- Days 6-7: Begin lightweight habit-building (posture awareness, basic skincare).
The first 7 days should produce a meaningfully different-looking person by week's end. This earns the user's commitment for weeks 2-4.

WEEKS 2-4 (Days 8-30) — COMPOUND HABITS AND DEPTH:
- Days 8-14: Skin routine refinement, fitness foundations, style expansion beyond first basics.
- Days 15-21: Posture deep work, body composition habits, advanced grooming.
- Days 22-30: Integration, refinement, building beyond the basics.

DO NOT distribute pillars evenly. Distribute by LEVERAGE. The user's weakest pillar with highest fixability gets front-loaded. Strongest pillars get later refinement.

MULTI-PRIORITY DISTRIBUTION: The user selected {goals_count} priorities: {goal}. Across the 30 days, all priorities must be represented. No priority ignored, none over-dominates.

HABIT-STACKING: Attach new habits to existing routines where natural. Examples:
- 'After brushing teeth in the morning, do 30 seconds of posture reset'
- 'After your evening shower, apply moisturizer immediately'
At least 30% of actions should use habit-stacking phrasing.

Rules for the plan:
1. Generate exactly 30 days.
2. Each day has 1 to 3 actions — vary the count, do not always use 3.
3. Include at least 4 recovery/lighter days spread across the 30 days. Mark them with is_recovery_day: true and focus_pillar: "recovery".
4. Actions must be SPECIFIC and immediately actionable:
   - Bad: "drink water"
   - Good: "drink 2 litres of water throughout the day — keep a bottle with you"
5. Weight actions toward the pillars with the lowest scores and the priorities identified above.
6. Escalate gradually: Week 1 is lighter and habit-forming, Week 4 has fuller routines.
7. Include at least one action with the word "haircut" in its title (this triggers the barber card feature).
8. On days 7, 14, 21, and 28 — include an action with "weekly photo" in its title (triggers the weekly check-in feature).
9. All text must be in {language}.
10. STRICT RULE — NO SPECIFIC CLOCK TIMES: Never use specific clock times. Use flexible references:
    - Workouts/physical: "dans la journée" or "quand tu as 10 minutes"
    - Evening care: "avant le coucher" or "le soir"
    - Morning: "le matin" or "au réveil"
    - All-day: "tout au long de la journée"
11. STRICT RULE — LOGICAL ORDERING: If an action involves buying something, the user cannot use it the same day. Usage appears on a LATER day or phrased "as soon as you have them".
12. STRICT RULE: focus_pillar and pillar ONLY from: hair, style, fitness, skin, recovery.
    Map: posture → fitness, mindset → recovery, wardrobe → style, grooming → skin or hair.
13. STRICT RULE — NO GENERIC ADVICE: Every action must be specific to this user's observations, scores, and priorities. If it could appear in any random fitness/skincare app, it doesn't belong here.

DAY STRUCTURE: Each day has:
- focus_pillar (one of the 5 valid values)
- theme (string, 1 short sentence in {language}) — a personal coach speaking to the user, tying the day's actions together emotionally. Not a category label. Like an older brother giving a daily framing.
- summary (one short sentence describing the day's focus)
- is_recovery_day (boolean)
- actions (1-3)

ACTION FORMAT: Each action has:
- position (integer, 1-3)
- pillar (one of the 5 valid pillars)
- title (short action name, max 6 words)
- description (specific instructions, 2-3 sentences, what to do and when)
- why (1 sentence: why this matters specifically for this user — connected to their observations/scores/lifestyle/goals, not generic)
- minimum (the absolute minimum version of this action for a low-energy day — max 2 minutes to complete. Example: if full action is a 15-min skincare routine, minimum is 'Just wash your face tonight.' If full action is booking a barber appointment, minimum is 'Just send the message, that's it.')

Respond ONLY with a valid JSON array. No preamble, no markdown fences, no commentary.

[
  {{
    "day": 1,
    "focus_pillar": "hair",
    "theme": "One short coaching sentence in {language}.",
    "summary": "One short sentence describing the focus of this day.",
    "is_recovery_day": false,
    "actions": [
      {{
        "position": 1,
        "pillar": "hair",
        "title": "Short action title",
        "description": "Specific, actionable description — what to do and when.",
        "why": "One sentence why this matters for this specific user.",
        "minimum": "The 2-minute minimum version of this action."
      }}
    ]
  }},
  ...30 days total...
]"""


def build_chunked_plan_prompt(
    language: str,
    profile_dict: dict,
    observations: list,
    scores: dict,
    day_start: int,
    day_end: int,
    daily_pattern: str = "",
    activity_level: str = "",
    upcoming_context: str = "",
) -> str:
    """
    Build a prompt for a single chunk of the 30-day plan (days day_start to day_end).

    Uses the same context as build_plan_prompt so each chunk is consistent,
    but only asks for the specified day range to stay within token limits.
    """
    name = profile_dict.get("display_name") or "the user"
    goal = profile_dict.get("biggest_goal") or ""
    insecurity = profile_dict.get("biggest_insecurity") or ""
    archetype = profile_dict.get("archetype") or ""
    target = profile_dict.get("target_archetype") or ""

    obs_lines = "\n".join(f"- {o}" for o in observations) if observations else "No specific observations provided."

    hair_score = scores.get("hair", 50)
    style_score = scores.get("style", 50)
    fitness_score = scores.get("fitness", 50)
    skin_score = scores.get("skin", 50)

    goals_list = [g.strip() for g in goal.split(",") if g.strip()] if goal else []
    goals_count = len(goals_list) if goals_list else 1

    haircut_note = "- Include at least one action with the word \"haircut\" in its title (this triggers the barber card feature)." if day_start == 1 else ""
    photo_days = [d for d in [7, 14, 21, 28] if day_start <= d <= day_end]
    photo_note = ""
    if photo_days:
        days_str = ", ".join(str(d) for d in photo_days)
        photo_note = f"- On days {days_str} — include an action with \"weekly photo\" in its title (triggers the weekly check-in feature)."

    return f"""You are RIZE — a glow-up coach for young men in Morocco and MENA. Speak with the warmth and directness of an older brother who's been through the same journey. Wise, direct, encouraging. 'Tu' form in French. Contractions in English. No filler phrases.

CULTURAL CONTEXT: Morocco/MENA. Keep recommendations natively Moroccan. Products: Bioderma, La Roche-Posay, Avène, CeraVe, Cetaphil at pharmacies. Beard culture is central. Climate-aware (hot summers, mild winters).

Their profile:
- Name: {name}
- Priorities ({goals_count} selected): {goal}
- Current: {archetype} → Target: {target}
- Scores — Hair: {hair_score}/100, Style: {style_score}/100, Fitness: {fitness_score}/100, Skin: {skin_score}/100

USER LIFESTYLE CONTEXT:
- Daily pattern: {daily_pattern if daily_pattern else "(not provided)"}
- Activity level: {activity_level if activity_level else "(not provided)"} — calibrate fitness actions to this starting point
- Upcoming context: {upcoming_context if upcoming_context and upcoming_context.strip() else "(none)"} — if an event is mentioned, front-load relevant actions

Additional user context: '{insecurity if insecurity and insecurity.strip() else "(none)"}'

Specific observations from baseline photo:
{obs_lines}

PLAN PHILOSOPHY — LEVERAGE-FIRST:
This chunk covers days {day_start}-{day_end}. Apply the overall leverage philosophy:
- Days 1-7: High-leverage quick wins (haircut if hair < 75, one fitted basic if style < 60, habit seeds)
- Days 8-14: Skin routine, fitness foundations, style expansion
- Days 15-21: Posture depth, body composition habits, advanced grooming
- Days 22-30: Integration and refinement
Front-load the weakest, most fixable pillars. Distribute all {goals_count} priorities across these days.

HABIT-STACKING: At least 30% of actions should attach to existing routines (after shower, after brushing teeth, during morning coffee, etc.).

Rules:
1. Generate exactly days {day_start} to {day_end}, no fewer, no more.
2. Each day has 1 to 3 actions — vary the count.
3. Include at least one recovery/lighter day in this chunk. Mark it with is_recovery_day: true and focus_pillar: "recovery".
4. Actions must be SPECIFIC and immediately actionable (not "drink water" — "drink 2L of water throughout the day").
5. Weight toward lowest-scoring pillars. Distribute all {goals_count} priorities — ignore none.
6. All text must be in {language}.
7. STRICT RULE — NO SPECIFIC CLOCK TIMES. Use: workouts → "dans la journée", evening care → "avant le coucher", morning → "le matin", all-day → "tout au long de la journée".
8. STRICT RULE — LOGICAL ORDERING: If buying something, usage appears on a LATER day or "as soon as you have them".
9. STRICT RULE: focus_pillar and pillar ONLY from: hair, style, fitness, skin, recovery. Map: posture→fitness, mindset→recovery, wardrobe→style, grooming→skin or hair.
10. STRICT RULE — NO GENERIC ADVICE: Every action must be specific to this user's observations, scores, and priorities.
{haircut_note}
{photo_note}

DAY STRUCTURE: day, focus_pillar, theme (1 short coaching sentence in {language}), summary, is_recovery_day, actions.

ACTION FORMAT: position, pillar, title (max 6 words), description (2-3 sentences, specific), why (1 sentence — why this matters for this specific user), minimum (absolute 2-minute minimum version for low-energy days).

Generate exactly days {day_start} to {day_end}. Respond ONLY with a valid JSON array, no preamble, no markdown fences.

[
  {{
    "day": {day_start},
    "focus_pillar": "hair",
    "theme": "One short coaching sentence in {language}.",
    "summary": "One short sentence describing the focus of this day.",
    "is_recovery_day": false,
    "actions": [
      {{
        "position": 1,
        "pillar": "hair",
        "title": "Short action title",
        "description": "Specific, actionable description — what to do and when.",
        "why": "One sentence why this matters for this specific user.",
        "minimum": "The 2-minute minimum version of this action."
      }}
    ]
  }},
  ...days {day_start} to {day_end} total...
]"""


def build_compact_plan_prompt(
    language: str,
    profile_dict: dict,
    observations: list,
    scores: dict,
    daily_pattern: str = "",
    activity_level: str = "",
    upcoming_context: str = "",
) -> str:
    """
    Compact version of the plan prompt for use on retry after truncation.
    Uses shorter descriptions to fit within token limits.
    """
    name = profile_dict.get("display_name") or "the user"
    goal = profile_dict.get("biggest_goal") or ""
    insecurity = profile_dict.get("biggest_insecurity") or ""
    archetype = profile_dict.get("archetype") or ""
    target = profile_dict.get("target_archetype") or ""

    hair_score = scores.get("hair", 50)
    style_score = scores.get("style", 50)
    fitness_score = scores.get("fitness", 50)
    skin_score = scores.get("skin", 50)

    goals_list = [g.strip() for g in goal.split(",") if g.strip()] if goal else []
    goals_count = len(goals_list) if goals_list else 1

    return f"""You are RIZE — glow-up coach for young men in Morocco/MENA. Older brother tone: warm, direct, wise. 'Tu' in French. Contractions in English. No filler phrases.

Build a 30-day transformation plan for {name}.

Context: Morocco/MENA. Products: Bioderma, La Roche-Posay, Avène, CeraVe at pharmacies. Beard culture central.
Priorities ({goals_count}): {goal}
User context: {insecurity if insecurity and insecurity.strip() else "(none)"}
Lifestyle: pattern={daily_pattern if daily_pattern else "unknown"}, activity={activity_level if activity_level else "unknown"}, upcoming={upcoming_context if upcoming_context and upcoming_context.strip() else "none"}
Current: {archetype} → Target: {target}
Scores: Hair {hair_score}, Style {style_score}, Fitness {fitness_score}, Skin {skin_score}

LEVERAGE-FIRST PHILOSOPHY:
- Days 1-7: Quick wins — hair first if score < 75, one fitted basic if style < 60, light habit seeds
- Days 8-14: Skin routine, fitness foundations, style expansion
- Days 15-21: Posture depth, body composition, advanced grooming
- Days 22-30: Integration and refinement
Front-load weakest/most-fixable pillar. Distribute all {goals_count} priorities.

Rules:
- 30 days, 1–3 actions each, at least 4 recovery days
- Specific actions only (not "drink water" — "drink 2L water throughout the day")
- Habit-stack at least 30% of actions onto existing routines
- Distribute all {goals_count} priorities equally — ignore none
- Day 7, 14, 21, 28: include action with "weekly photo" in title
- Include one action with "haircut" in title
- All text in {language}
- NO SPECIFIC CLOCK TIMES: workouts → "dans la journée", evening → "avant le coucher", morning → "le matin", all-day → "tout au long de la journée"
- LOGICAL ORDERING: never tell user to use something same day they buy it
- PILLARS ONLY: hair, style, fitness, skin, recovery (map: posture→fitness, mindset→recovery, wardrobe→style, grooming→skin)
- NO GENERIC ADVICE: every action specific to this user's observations and scores

Return ONLY a JSON array, no markdown:
[{{"day":1,"focus_pillar":"hair","theme":"Short coaching sentence in {language}.","summary":"...","is_recovery_day":false,"actions":[{{"position":1,"pillar":"hair","title":"...","description":"...","why":"Why this matters for this specific user.","minimum":"2-minute minimum version."}}]}},...30 days]"""
