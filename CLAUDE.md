# RIZE — Project Conventions for Claude Code

## What RIZE is

RIZE is an AI-powered men's glow-up coach for the Moroccan and broader MENA market. It is NOT a one-shot advice generator. It is a 30-day transformation journey with daily actions, weekly progress photos, AI re-scoring, and a personalized AI coach that has memory of the user's progress.

The product is the journey, not the AI output. Every feature exists to make the user transform over 30 days and to make that transformation visible and trackable.

## Target user

Young men aged 18-30 in Morocco and the broader MENA region. Trilingual interface — French, English, Arabic — user picks at signup and can change in profile. Recommendations consider local context: Moroccan retailers, local barber terminology in Darija, MENA aesthetic standards, climate considerations.

## Tech stack

- Backend: Python 3.11+, Flask
- Database, Auth, and Storage: Supabase (Postgres + Auth + Storage)
- AI: Anthropic Claude API
  - Vision tasks (photo scoring, wardrobe analysis): claude-haiku-4-5-20251001
  - Coach chat and complex reasoning: claude-haiku-4-5-20251001 for v1, may upgrade to Sonnet for coach if quality is insufficient
- Frontend: Server-rendered Jinja2 templates, vanilla CSS, minimal JavaScript
- Image processing: Pillow (PIL)
- Deployment target: Vercel (eventually — not yet, we are working locally until v1 is feature-complete)

## Project structure

```
rize/
├── app.py                  Main Flask application
├── CLAUDE.md               This file
├── README.md               Quick start for humans
├── requirements.txt
├── .env                    Local env vars, gitignored, never committed
├── .env.example            Template for env vars, committed
├── .gitignore
├── /lib                    Helper modules
│   ├── __init__.py
│   ├── supabase_client.py  Supabase connection helper
│   ├── claude_client.py    Anthropic API helper
│   ├── auth.py             Login required decorator, session helpers
│   ├── image_utils.py      Pillow compression, thumbnail generation
│   ├── i18n.py             Translation strings, language helpers
│   └── prompts/            All Claude prompts as separate files
│       ├── __init__.py
│       ├── baseline_score.py
│       ├── weekly_score.py
│       ├── plan_generator.py
│       ├── coach.py
│       ├── wardrobe_analyzer.py
│       ├── outfit_recommender.py
│       └── barber_card.py
├── /templates              Jinja2 templates
│   ├── /onboarding         Onboarding flow templates
│   ├── /today              Daily home screen
│   ├── /plan               30-day calendar
│   ├── /coach              Chat interface
│   ├── /wardrobe           Wardrobe management + outfits
│   ├── /barber             Barber translator card view
│   ├── /score              Score history and share card
│   └── /shared             Layout, nav, partials
├── /static
│   ├── style.css           Main stylesheet
│   ├── /js                 Minimal vanilla JS
│   └── /images             Static brand images, haircut reference library
└── /migrations             Supabase SQL migration files, numbered (001_*, 002_*, etc.)
```

## Critical rules — never violate these

1. **No emojis anywhere in the UI.** Use numbered labels (01 02 03 04) and text. The existing templates have legacy emojis (✂️ 👔 💪 🧴) that are being phased out — if you touch a template with emojis, remove them.

2. **Trilingual from day one.** Every user-facing string must support French, English, Arabic. Use the i18n helper, never hardcode user-facing strings in templates. Arabic UI is right-to-left — the layout flips when language is Arabic.

3. **AI outputs respect the user's language.** Every Claude prompt includes the user's preferred_language and instructs Claude to respond in that language. Never translate after the fact.

4. **Manual git commits, manual messages.** The human commits their own code with their own messages. Never run git commit, git push, or generate commit messages. If asked to "save" or "commit," tell the human what to commit and let them do it.

5. **Never run SQL directly against the Supabase project.** All schema changes go to numbered files in /migrations/ (001_initial.sql, 002_add_X.sql, etc.). The human runs the SQL manually in the Supabase SQL editor after reviewing it.

6. **No Anthropic SDK calls without the helper.** All Claude API calls go through lib/claude_client.py. No direct client.messages.create() in route handlers. This keeps prompts, token tracking, and error handling in one place.

7. **All photos compressed before storage.** Wardrobe items: 200×200 thumbnail at 60% JPEG quality. Progress photos: 800×800 at 70%. Baseline photos: 1200×1200 at 80%. Coach-attached photos: never stored, processed in memory then discarded. Wardrobe original photos: sent to Claude in memory, then discarded — only the thumbnail is stored.

8. **Row Level Security on every table.** Every Supabase table has an RLS policy that says users can only read or write rows where user_id = auth.uid(). Never disable RLS. Never use the service role key from the Flask backend except in admin-only contexts (none planned for v1).

9. **No global Supabase client creation inside route handlers.** Use the helper in lib/supabase_client.py.

10. **Sessions are mandatory.** Flask sessions store the authenticated user. Use the @login_required decorator from lib/auth.py on every protected route. Never trust user_id from request data.

11. **Prompts live in their own files.** Never inline a multi-line Claude prompt inside a route handler. Every prompt has its own file in lib/prompts/ with a builder function that takes parameters and returns the formatted prompt string.

12. **Never put real secrets in CLAUDE.md, README, or any committed file.** Real keys live only in .env (gitignored). .env.example contains placeholder values only.

## The user journey (build phases, in order)

This is the v1 build order. Don't skip ahead — each phase depends on the previous one being solid.

- Phase 1: Foundation — folder structure, env files, helpers, i18n, session auth, SQL schema migration, design system audit. No new user-facing features yet.
- Phase 2: Onboarding flow — language picker, profile setup, baseline photo, AI baseline scoring, archetype reveal, 30-day plan generation.
- Phase 3: Today screen + streak loop — daily 3 actions, mark-as-done, streak counter, recovery day.
- Phase 4: Plan tab — 30-day calendar view with past/today/future states.
- Phase 5: Weekly check-in — progress photo, AI re-scoring, comparison view, score deltas.
- Phase 6: Coach chat — persistent chat with Claude, photo attachments, conversation history.
- Phase 7: Wardrobe + outfit builder — upload flow with AI metadata extraction, wardrobe grid, daily outfit recommendation.
- Phase 8: Barber translator card — generated when haircut action appears, trilingual instructions, shareable card.

## Database tables (full schema lives in /migrations, summary here)

- profiles — extends auth.users, holds archetype, journey state, streak, language preference
- photos — every photo uploaded, with type and AI scores
- daily_plans — one row per journey day per user, defines focus pillar
- daily_actions — 1 to 3 actions per day, completion state, related resources
- coach_messages — persistent chat history with the AI coach
- wardrobe_items — user's clothes (thumbnail + AI metadata, original photo discarded)
- outfit_recommendations — daily outfit suggestions
- barber_cards — generated cards with trilingual haircut info
- weekly_check_ins — weekly progress photo, score deltas, adherence rate

When in doubt, read the migration files for the exact schema.

## Storage buckets (Supabase Storage)

- profile-photos — private, RLS: user reads own only
- progress-photos — private, RLS: user reads own only
- wardrobe-thumbnails — private, RLS: user reads own only
- barber-card-references — public read, admin-only write (shared library of haircut reference images)

## Coding conventions

### Python and Flask
- Type hints on all helper functions
- Route handlers stay short — heavy logic goes in lib/ modules
- Use request.form.get() not request.form[] (returns None instead of raising)
- Always validate inputs before passing to Supabase
- Wrap Supabase calls in try/except — they raise on network errors
- Wrap Claude calls in try/except — handle JSON parse errors gracefully

### Templates
- Every page extends templates/shared/layout.html
- Use Jinja blocks: {% block title %}, {% block content %}, {% block scripts %}
- Translation strings via {{ t('key.path') }} helper
- Numbered labels: <span class="card-number">01</span> not emojis
- Forms POST to a route, never use JavaScript fetch unless absolutely necessary

### CSS
- Existing CSS variables stay (--bg, --gold, --text, etc.) — read them from style.css
- Add new component styles to style.css, don't create new files yet
- Mobile breakpoint: 768px, small mobile: 480px
- RTL support: when lang="ar", layout flips via [dir="rtl"] selectors

### Claude prompts
- Each prompt is a function in lib/prompts/
- Prompt functions take typed parameters, return a string
- Always include the user's preferred_language in the prompt
- Always instruct Claude to respond in that language
- For JSON outputs, instruct: respond ONLY with valid JSON, no preamble, no markdown fences
- Always parse JSON in a try/except with a graceful fallback

## Environment variables

Required in .env (real values), and listed with placeholders in .env.example:

```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://....supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
FLASK_SECRET_KEY=<random 32+ chars>
FLASK_ENV=development
```

Generate FLASK_SECRET_KEY with: `python -c "import secrets; print(secrets.token_hex(32))"`

## What is NOT in v1 (don't build these even if asked, unless the human explicitly approves)

- Affiliate commerce links and product database
- Future-you AI-generated photos
- Friends, leaderboards, social features
- Push notifications
- Native mobile app (web only for v1)
- Google OAuth (email/password only — Google button stays disabled)
- Vercel deployment (working locally until v1 is feature-complete)

## How to work with me (Claude Code, read this carefully)

1. **One feature at a time.** When given a feature prompt, complete that feature fully — backend route, template, styles, integration — before moving on. Don't half-build five things.

2. **Ask before assuming.** If something in the spec is ambiguous, ask. Don't make architectural decisions silently. Examples worth asking about: should the coach chat be persistent across sessions or per-day, should the streak reset at midnight in the user's timezone or UTC.

3. **Show diffs before applying.** When editing existing files, show what changed. Don't rewrite a 200-line file when you only need to change 5 lines.

4. **Test as you go.** After building a feature, give a 5-line test plan: how to manually verify it works. The human tests it, reports back, you fix issues.

5. **Don't auto-fix unrelated things.** If you spot a bug or smell while working on feature X, mention it but don't fix it in the same change. Fixes go in separate commits.

6. **Respect what's already there.** The existing dark luxury design system works. Don't redesign it. Don't introduce new fonts, new color schemes, or new component libraries.

7. **No new dependencies without asking.** If you want to add a Python package or a JS library, ask first with a one-line justification.

8. **Never run destructive commands without explicit human approval.** This includes git push, git reset --hard, rm -rf, dropping database tables, force migrations. When in doubt, stop and ask.

## What "done" means for a feature

A feature is done when:
- The route works end-to-end (no 500s, no broken redirects)
- The template renders correctly in French, English, and Arabic
- The mobile layout works (test at 375px width)
- The data is saving to and reading from Supabase correctly
- The human can manually walk through the flow and it feels right
- A 5-line test plan has been provided
- The human has tested and confirmed

Then the next feature starts. Not before.

## Things the human does, not Claude Code

- Runs git commit and git push
- Writes commit messages
- Manages Supabase project settings, API keys, billing
- Runs SQL migrations in the Supabase dashboard manually
- Tests in the browser and reports bugs
- Makes scope and design decisions
- Deploys when ready

Things Claude Code does:
- Writes the actual code
- Generates SQL migration files (the human applies them)
- Generates Claude prompts in lib/prompts/
- Builds templates and styles
- Refactors when asked
- Explains how something works when the human is confused

## Current state of the project

As of this CLAUDE.md being written, the existing codebase has:
- Working email/password auth via Supabase (no session management yet — must be fixed in Phase 1)
- Landing page, signup, login, dashboard
- Old form-based category flows (hair, style, fitness, skin) — these will be deprecated and removed during v1 build
- Old photo scan flow at /scan/<category> — has a bug where templates/scan.html posts to /scan instead of /scan/<category>; will be deprecated anyway
- Old results page that renders walls of text — will be deprecated
- Score and score_card pages from a previous iteration — will be deprecated, replaced by the journey-based scoring
- Dark luxury design system in static/style.css — KEEP THIS

We are doing a structured rebuild. Old routes stay temporarily during the rebuild for reference, then get removed at the end of v1.

## Final note

This file is the source of truth. If anything is unclear, re-read the relevant section. If something is missing that you need to know, ask the human to add it before proceeding. Update CLAUDE.md whenever a major decision is made.