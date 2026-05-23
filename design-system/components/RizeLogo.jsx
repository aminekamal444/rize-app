/**
 * RizeLogo — Calligraphic SVG Wordmark
 *
 * Renders "Rize" in Pinyon Script (Spencerian/Copperplate family) with three
 * hand-drafted flourish layers: a pre-entry curl over the R, a fine hairline
 * crossbar accent, and a sweeping exit underline with a terminal pen-lift dot.
 *
 * Size is controlled entirely via `className` (Tailwind w-*/h-* or arbitrary).
 * The internal viewBox is fixed at 185×80; the browser scales it proportionally.
 *
 * PREREQUISITE: Pinyon Script must be loaded at document level (index.html):
 *   <link href="https://fonts.googleapis.com/css2?family=Pinyon+Script&display=swap" rel="stylesheet">
 */
export default function RizeLogo({ className = 'w-28 h-10', color = '#F0EDE8' }) {
  return (
    <svg
      viewBox="0 0 185 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Rize"
      role="img"
    >
      <defs>
        {/*
         * Soft luminance glow — adds the "lit from within" quality of a
         * freshly inked nib without the harsh neon look.
         */}
        <filter id="rz-glow" x="-8%" y="-20%" width="116%" height="140%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.3" result="blurred" />
          <feMerge>
            <feMergeNode in="blurred" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/*
         * Fade gradient for the exit underline flourish —
         * fades in from the left and out on the right, like ink thinning at
         * the start and end of a calligraphic stroke.
         */}
        <linearGradient id="rz-flourish-fade" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%"   stopColor={color} stopOpacity="0"    />
          <stop offset="12%"  stopColor={color} stopOpacity="0.65" />
          <stop offset="86%"  stopColor={color} stopOpacity="0.65" />
          <stop offset="100%" stopColor={color} stopOpacity="0"    />
        </linearGradient>
      </defs>

      {/*
       * ── FLOURISH 1: Pre-entry calligraphic curl ─────────────────────────
       * Sweeps up from just below the mid-line on the left side, arcs up to
       * the top of the R's ascender loop, then curls gently back right —
       * exactly how a dip-pen enters a capital letter from a resting stroke.
       *
       * Adjust the end point (23, 16) if the R in your rendered font has a
       * taller or shorter ascender loop.
       */}
      <path
        d="M 4,56 C 2,40 5,22 13,12 C 18,5 26,7 23,16"
        stroke={color}
        strokeWidth="0.65"
        strokeLinecap="round"
        opacity="0.52"
      />

      {/*
       * ── FLOURISH 2: Hairline crossbar accent ─────────────────────────────
       * A fine horizontal rule sitting just above the R's top loop — mimics
       * the overline flourish common in 19th-century copperplate engravings.
       * strokeWidth 0.45 produces the characteristic "hairline" weight.
       */}
      <path
        d="M 9,8 C 16,4.5 26,4 35,7.5"
        stroke={color}
        strokeWidth="0.45"
        strokeLinecap="round"
        opacity="0.36"
      />

      {/*
       * ── WORDMARK ─────────────────────────────────────────────────────────
       * Pinyon Script at 60px. The baseline (y="62") is tuned so ascenders
       * sit at ~y=10 and descenders clear the 80px viewBox bottom.
       * filter="url(#rz-glow)" adds the subtle luminance halo.
       */}
      <text
        x="8"
        y="62"
        fontFamily="'Pinyon Script', 'Monsieur La Doulaise', cursive"
        fontSize="60"
        fill={color}
        filter="url(#rz-glow)"
        letterSpacing="-0.5"
      >
        Rize
      </text>

      {/*
       * ── FLOURISH 3: Exit sweep underline ─────────────────────────────────
       * A long sweeping baseline rule that fades in under the R and tapers
       * out past the terminal 'e'. The cubic bezier dips then rises, creating
       * the elastic spring tension of a fast calligraphic exit stroke.
       * The terminal circle marks the pen-lift moment.
       */}
      <path
        d="M 7,70 C 42,75 86,73 130,71 C 156,70 170,72 180,70"
        stroke="url(#rz-flourish-fade)"
        strokeWidth="0.75"
        strokeLinecap="round"
      />
      <circle cx="179" cy="70" r="1.3" fill={color} opacity="0.42" />
    </svg>
  );
}
