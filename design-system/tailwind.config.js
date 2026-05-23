/**
 * RIZE — Tailwind CSS Configuration
 * "Premium Tech Dark Mode" palette
 *
 * Design tokens:
 *   Base background  : Deep Onyx   #0B0F19
 *   Card surface     : Slate night #161F30
 *   Interactive accent: Electric Cyan #00F5D4
 *   Primary text     : Warm ink    #F0EDE8
 *
 * Usage in components:
 *   bg-onyx          → #0B0F19  (page background)
 *   bg-surface       → #161F30  (card background)
 *   bg-surface-hover → #1C2840  (card hover)
 *   text-electric    → #00F5D4  (progress rings, checkboxes, active states)
 *   text-ink         → #F0EDE8  (primary text)
 *   text-ink-muted   → #8A96A8  (secondary text)
 *   font-script      → Pinyon Script (logo / wordmark only)
 *   font-sans        → Plus Jakarta Sans (all UI text)
 *   font-mono        → JetBrains Mono (numbered labels, metrics)
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],

  theme: {
    extend: {

      // ── Color Tokens ───────────────────────────────────────────────────────
      colors: {
        // Page backgrounds
        onyx: {
          DEFAULT: '#0B0F19',
          900:     '#080C14',   // deeper — under modals
          800:     '#0F1420',   // slightly lighter — section dividers
        },

        // Card & surface layers
        surface: {
          DEFAULT: '#161F30',
          hover:   '#1C2840',
          nested:  '#1F2D42',
          border:  'rgba(255,255,255,0.05)',
        },

        // Electric Cyan — the ONE accent color.
        // Use it only on: progress rings, checkboxes, active nav dots,
        // primary CTA buttons. Overusing it kills the premium feel.
        electric: {
          DEFAULT: '#00F5D4',
          60:      'rgba(0,245,212,0.60)',
          30:      'rgba(0,245,212,0.30)',
          10:      'rgba(0,245,212,0.10)',
          '05':    'rgba(0,245,212,0.05)',
        },

        // Neutral ink tones — warm, not cool-grey
        ink: {
          DEFAULT: '#F0EDE8',   // primary text
          muted:   '#8A96A8',   // secondary / metadata
          dim:     '#4A5568',   // placeholder / disabled
          faint:   '#2A3348',   // ghost / hint
        },

        // Semantic feedback
        success: '#22C55E',
        danger:  '#EF4444',
        warning: '#F59E0B',
      },

      // ── Typography ─────────────────────────────────────────────────────────
      fontFamily: {
        // LOGO ONLY — Spencerian/Copperplate script.
        // Never use for headings or body copy.
        script: ['"Pinyon Script"', '"Monsieur La Doulaise"', 'cursive'],

        // All dashboard text, labels, metrics
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],

        // Numbered item labels (01 / 02 / 03) and small data figures
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },

      // ── Type Scale Additions ───────────────────────────────────────────────
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem', letterSpacing: '0.05em' }], // 10px
      },

      // ── Shadows & Glows ────────────────────────────────────────────────────
      boxShadow: {
        // Standard card elevation
        'card':       '0 1px 0 rgba(255,255,255,0.04), 0 4px 20px rgba(0,0,0,0.35)',
        'card-hover': '0 1px 0 rgba(255,255,255,0.06), 0 8px 32px rgba(0,0,0,0.50)',

        // Cyan glow — for active rings, checked boxes, primary CTA
        'glow-sm': '0 0 10px rgba(0,245,212,0.30)',
        'glow-md': '0 0 20px rgba(0,245,212,0.20), 0 0 40px rgba(0,245,212,0.08)',
        'glow-lg': '0 0 30px rgba(0,245,212,0.35)',
      },

      // ── Border Radius ──────────────────────────────────────────────────────
      borderRadius: {
        'bento':    '16px',   // large bento cells
        'bento-sm': '12px',   // small stat cells
        'pill':     '9999px', // tags and badges
      },

      // ── Background Gradients ───────────────────────────────────────────────
      backgroundImage: {
        // Subtle top-to-bottom gradient for the page — prevents flat "black box" look
        'page-gradient': 'linear-gradient(180deg, #0F1420 0%, #0B0F19 100%)',

        // Electric button gradient
        'electric-gradient': 'linear-gradient(135deg, #00F5D4 0%, #00C4B4 100%)',
      },

      // ── Animations ─────────────────────────────────────────────────────────
      animation: {
        'pulse-glow': 'pulseGlow 2.5s ease-in-out infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { filter: 'drop-shadow(0 0 4px rgba(0,245,212,0.25))' },
          '50%':      { filter: 'drop-shadow(0 0 12px rgba(0,245,212,0.55))' },
        },
      },
    },
  },

  plugins: [],
};
