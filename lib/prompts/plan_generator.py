from __future__ import annotations


def build_plan_prompt(
    language: str,
    profile_dict: dict,
    observations: list,
    scores: dict,
) -> str:
    """
    Build the prompt for 30-day plan generation.

    Returns a prompt string instructing Claude to generate a JSON array of
    30 daily plan objects, each with focus_pillar, summary, and 1–3 actions.

    Parameters
    ----------
    language:       User's preferred language code ('fr', 'en', 'ar').
    profile_dict:   Dict with keys: display_name, biggest_goal,
                    biggest_insecurity, archetype, target_archetype.
    observations:   List of specific observation strings from baseline scoring.
    scores:         Dict with keys: hair, style, fitness, skin, overall.
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

    return f"""You are building a personalized 30-day transformation plan for {name}.

Their profile:
- Biggest goal: {goal}
- Biggest insecurity: {insecurity}
- Current archetype: {archetype}
- 30-day destination archetype: {target}
- Baseline scores — Hair: {hair_score}/100, Style: {style_score}/100, Fitness: {fitness_score}/100, Skin: {skin_score}/100

Specific observations from their baseline photo (these should heavily shape the actions):
{obs_lines}

Rules for the plan:
1. Generate exactly 30 days.
2. Each day has 1 to 3 actions — vary the count, do not always use 3.
3. Include at least 4 recovery/lighter days spread across the 30 days. Mark them with is_recovery_day: true and focus_pillar: "recovery".
4. Actions must be SPECIFIC and immediately actionable:
   - Bad: "drink water"
   - Good: "drink 2 litres of water before 6pm — set a reminder at 10am and 3pm"
5. Weight actions toward the pillars with the lowest scores and the insecurities identified above.
6. Respect the user's stated biggest goal — weave it throughout.
7. Escalate gradually: Week 1 is lighter and habit-forming, Week 4 has fuller routines.
8. Include at least one action with the word "haircut" in its title (this triggers the barber card feature).
9. On days 7, 14, 21, and 28 — include an action with "weekly photo" in its title (triggers the weekly check-in feature).
10. All text must be in {language}.
11. STRICT RULE: The "focus_pillar" and "pillar" fields can ONLY be one of these EXACT values:
    - hair      (haircut, beard, scalp care)
    - style     (clothing, accessories, color, fit, wardrobe, fashion, outfit)
    - fitness   (exercise, posture, body, mobility, sleep, nutrition)
    - skin      (skincare, grooming, acne, hydration)
    - recovery  (rest day, mental reset, lighter routine, mindset)
    DO NOT use any other value. DO NOT invent categories like "posture", "mindset", "wardrobe", "grooming".
    Map them to the 5 valid values above. Examples: posture → fitness, mindset → recovery, wardrobe → style, grooming → skin or hair.

Respond ONLY with a valid JSON array. No preamble, no markdown fences, no commentary.

[
  {{
    "day": 1,
    "focus_pillar": "hair",
    "summary": "One short sentence describing the focus of this day.",
    "is_recovery_day": false,
    "actions": [
      {{
        "position": 1,
        "pillar": "hair",
        "title": "Short action title",
        "description": "Specific, actionable description — what exactly to do, when, and why."
      }},
      {{
        "position": 2,
        "pillar": "skin",
        "title": "Short action title",
        "description": "Specific, actionable description."
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

    haircut_note = "- Include at least one action with the word \"haircut\" in its title (this triggers the barber card feature)." if day_start == 1 else ""
    photo_days = [d for d in [7, 14, 21, 28] if day_start <= d <= day_end]
    photo_note = ""
    if photo_days:
        days_str = ", ".join(str(d) for d in photo_days)
        photo_note = f"- On days {days_str} — include an action with \"weekly photo\" in its title (triggers the weekly check-in feature)."

    return f"""You are building part of a personalized 30-day transformation plan for {name}.

Their profile:
- Biggest goal: {goal}
- Biggest insecurity: {insecurity}
- Current archetype: {archetype}
- 30-day destination archetype: {target}
- Baseline scores — Hair: {hair_score}/100, Style: {style_score}/100, Fitness: {fitness_score}/100, Skin: {skin_score}/100

Specific observations from their baseline photo:
{obs_lines}

Rules:
1. Generate exactly the days {day_start} to {day_end}, no fewer, no more.
2. Each day has 1 to 3 actions — vary the count, do not always use 3.
3. Include at least one recovery/lighter day in this chunk. Mark it with is_recovery_day: true and focus_pillar: "recovery".
4. Actions must be SPECIFIC and immediately actionable (not "drink water" — "drink 2L of water before 6pm").
5. Weight actions toward the pillars with the lowest scores and the insecurities identified above.
6. All text must be in {language}.
7. STRICT RULE: The "focus_pillar" and "pillar" fields can ONLY be one of these EXACT values:
    - hair      (haircut, beard, scalp care)
    - style     (clothing, accessories, color, fit, wardrobe, fashion, outfit)
    - fitness   (exercise, posture, body, mobility, sleep, nutrition)
    - skin      (skincare, grooming, acne, hydration)
    - recovery  (rest day, mental reset, lighter routine, mindset)
    DO NOT use any other value. DO NOT invent categories like "posture", "mindset", "wardrobe", "grooming".
    Map them to the 5 valid values above. Examples: posture → fitness, mindset → recovery, wardrobe → style, grooming → skin or hair.
{haircut_note}
{photo_note}

Generate exactly the days {day_start} to {day_end}, no fewer, no more. Each day has 1 to 3 actions. Respond ONLY with a valid JSON array, no preamble, no markdown fences.

[
  {{
    "day": {day_start},
    "focus_pillar": "hair",
    "summary": "One short sentence describing the focus of this day.",
    "is_recovery_day": false,
    "actions": [
      {{
        "position": 1,
        "pillar": "hair",
        "title": "Short action title",
        "description": "Specific, actionable description — what exactly to do, when, and why."
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

    return f"""Build a 30-day transformation plan for {name}.

Goal: {goal}
Insecurity: {insecurity}
Current: {archetype} → Target: {target}
Scores: Hair {hair_score}, Style {style_score}, Fitness {fitness_score}, Skin {skin_score}

Rules:
- 30 days, 1–3 actions each, at least 4 recovery days
- Actions must be specific (not "drink water" — "drink 2L water before 6pm")
- Weight toward lowest-scoring pillars
- Week 1 lighter, Week 4 fuller
- Day 7, 14, 21, 28 must include action with "weekly photo" in title
- Include one action with "haircut" in title
- All text in {language}
- STRICT RULE: focus_pillar and pillar ONLY from: hair, style, fitness, skin, recovery
  Map anything else: posture→fitness, mindset→recovery, wardrobe→style, grooming→skin

Return ONLY a JSON array, no markdown:
[{{"day":1,"focus_pillar":"hair","summary":"...","is_recovery_day":false,"actions":[{{"position":1,"pillar":"hair","title":"...","description":"..."}}]}},...30 days]"""
