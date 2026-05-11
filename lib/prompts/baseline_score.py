from __future__ import annotations


def build_baseline_score_prompt(
    language: str,
    biggest_goal: str,
    biggest_insecurity: str,
) -> str:
    """
    Build the prompt for baseline photo scoring.

    Returns a prompt string instructing Claude to analyze the attached photo
    and return ONLY valid JSON with scores, archetypes, and observations.

    Parameters
    ----------
    language:           User's preferred language code ('fr', 'en', 'ar').
    biggest_goal:       The user's stated one-sentence transformation goal.
    biggest_insecurity: The user's stated biggest visual insecurity.
    """
    return f"""You are an elite men's image consultant and transformation coach.

Analyze this photo carefully and provide an honest, calibrated assessment.

Calibration guide (be realistic, not flattering):
- 50–75 is the typical range for most men
- 85+ is reserved for genuinely exceptional presentation
- Under 40 only when there are serious, obvious issues
- Do not inflate scores to be kind

User's priorities (may include multiple): {biggest_goal}
Additional context from user: {biggest_insecurity if biggest_insecurity and biggest_insecurity.strip() else "(none provided — do not invent any)"}

Score across four pillars (0–100 each):
- HAIR: cut quality, condition, suitability for their face shape, styling
- STYLE: outfit choices, fit, color harmony, overall presentation
- FITNESS: visible body composition, posture, build
- SKIN: clarity, hydration, grooming, evenness
- OVERALL: weighted average of the four pillars above

Then identify:
- current_archetype: A 2–4 word phrase describing who they are NOW based on the photo
  (examples: "Untapped Potential", "Diamond In Rough", "Quiet Powerhouse", "The Rough Cut")
- target_archetype: A 2–4 word phrase for a realistic 30-day destination
  (examples: "The Modern Gentleman", "Sharp & Grounded", "Clean Confidence")
- strength: Their single biggest visible strength visible in this photo, one specific sentence
- improvement: Their single biggest visible area for improvement, one specific sentence
- observations: 3 to 5 SPECIFIC observations this person can act on immediately.
  Be concrete and photo-specific — do NOT give generic advice.
  Good example: "The oversized fit of your shirt adds visual bulk and hides your frame — a slim-fit shirt would immediately sharpen your silhouette."
  Bad example: "Improve your style choices."

Respond in {language}.
Respond ONLY with valid JSON, no preamble, no commentary, no markdown fences:
{{
  "scores": {{
    "hair": <integer 0–100>,
    "style": <integer 0–100>,
    "fitness": <integer 0–100>,
    "skin": <integer 0–100>,
    "overall": <integer 0–100>
  }},
  "current_archetype": "<2–4 words>",
  "target_archetype": "<2–4 words>",
  "strength": "<one specific sentence>",
  "improvement": "<one specific sentence>",
  "observations": [
    "<specific actionable observation>",
    "<specific actionable observation>",
    "<specific actionable observation>"
  ]
}}"""
