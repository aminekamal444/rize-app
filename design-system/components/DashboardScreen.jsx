/**
 * RIZE — Daily Glow-Up Dashboard
 * "Premium Tech Dark Mode" × Calligraphic Logo — Bento Grid Layout
 *
 * Bento grid anatomy:
 *   Row 1  [Today's Routine checklist ──── 2/3] [Glow Score ring ─ 1/3]
 *   Row 2  [Streak] [Day] [Sleep] [Water] ─────────────── 4 micro-stats
 *   Row 3  [Week pillar rings ─────────── 2/3] [Progress photo ── 1/3]
 *
 * Interactive: checklist items toggle on click (local state demo).
 *
 * Stack: React 18 + Tailwind CSS (config in design-system/tailwind.config.js)
 * Fonts: loaded via <link> in index.html (see design-system/index.html)
 */
'use client';
import { useState } from 'react';
import RizeLogo from './RizeLogo';

// ─── ProgressRing ─────────────────────────────────────────────────────────────

function ProgressRing({ progress = 0, size = 88, stroke = 6, value, sublabel, label }) {
  const r      = (size - stroke) / 2;
  const circ   = 2 * Math.PI * r;
  const offset = circ - (Math.min(progress, 100) / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>

        {/* SVG ring — rotated so 0% starts at 12 o'clock */}
        <svg width={size} height={size} className="-rotate-90">
          {/* Background track */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={stroke}
          />
          {/* Filled arc */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke="#00F5D4"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{
              filter: 'drop-shadow(0 0 5px rgba(0,245,212,0.55))',
              transition: 'stroke-dashoffset 0.9s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
        </svg>

        {/* Centre label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
          <span
            className="font-bold leading-none text-white"
            style={{ fontSize: size > 80 ? '1.125rem' : '0.875rem' }}
          >
            {value}
          </span>
          {sublabel && (
            <span className="text-white/35 uppercase tracking-wider"
              style={{ fontSize: '0.55rem' }}>
              {sublabel}
            </span>
          )}
        </div>
      </div>

      {label && (
        <span className="text-white/45 uppercase tracking-widest"
          style={{ fontSize: '0.6rem' }}>
          {label}
        </span>
      )}
    </div>
  );
}

// ─── ChecklistItem ────────────────────────────────────────────────────────────

function ChecklistItem({ number, title, subtitle, completed, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-4 w-full px-4 py-3 rounded-xl
        hover:bg-white/[0.03] active:bg-white/[0.06]
        transition-all duration-150 group text-left"
    >
      {/* Checkbox */}
      <div
        className={`w-5 h-5 rounded-md flex-shrink-0 flex items-center justify-center
          transition-all duration-200
          ${completed
            ? 'bg-[#00F5D4] shadow-[0_0_10px_rgba(0,245,212,0.45)]'
            : 'border border-white/15 group-hover:border-[#00F5D4]/50'
          }`}
      >
        {completed && (
          /* Checkmark — dark onyx so it reads clearly on cyan */
          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
            <path
              d="M1 3.5 L3.8 6.5 L9 1"
              stroke="#0B0F19"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </div>

      {/* Text content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          {/* Numbered label — mono, electric, faded */}
          <span
            className="text-[#00F5D4]/50 uppercase tracking-widest shrink-0 leading-none"
            style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.6rem' }}
          >
            {number}
          </span>
          <span
            className={`text-sm font-semibold leading-snug transition-colors duration-200
              ${completed ? 'line-through text-white/25' : 'text-white/90'}`}
          >
            {title}
          </span>
        </div>
        {subtitle && (
          <p className="text-xs text-white/35 mt-0.5 truncate">{subtitle}</p>
        )}
      </div>

      {/* Status pill */}
      <span
        className={`shrink-0 px-2 py-0.5 rounded-full text-[0.6rem] font-semibold
          uppercase tracking-wider transition-all duration-200
          ${completed
            ? 'bg-[#00F5D4]/10 text-[#00F5D4]'
            : 'bg-white/[0.05] text-white/25'
          }`}
      >
        {completed ? 'Done' : 'Todo'}
      </span>
    </button>
  );
}

// ─── StatCell ─────────────────────────────────────────────────────────────────

function StatCell({ label, value, unit, accent = false }) {
  return (
    <div
      className="bg-[#161F30] rounded-[12px] p-4 flex flex-col gap-1
        border border-white/[0.04]
        shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.35)]"
    >
      <span
        className="text-white/40 font-semibold uppercase tracking-widest"
        style={{ fontSize: '0.6rem' }}
      >
        {label}
      </span>
      <div className="flex items-baseline gap-1 mt-0.5">
        <span
          className={`text-2xl font-bold leading-none
            ${accent ? 'text-[#00F5D4]' : 'text-white'}`}
          style={{ fontFamily: '"Plus Jakarta Sans", sans-serif' }}
        >
          {value}
        </span>
        {unit && (
          <span className="text-xs text-white/30 font-medium">{unit}</span>
        )}
      </div>
    </div>
  );
}

// ─── SubPillarBar ─────────────────────────────────────────────────────────────

function SubPillarBar({ label, pct }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="text-white/40 w-14 shrink-0"
        style={{ fontSize: '0.6rem' }}
      >
        {label}
      </span>
      <div className="flex-1 h-[3px] rounded-full bg-white/[0.06]">
        <div
          className="h-[3px] rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            backgroundColor: 'rgba(0,245,212,0.55)',
            boxShadow: '0 0 4px rgba(0,245,212,0.3)',
          }}
        />
      </div>
      <span
        className="text-white/30 w-5 text-right"
        style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.6rem' }}
      >
        {pct}
      </span>
    </div>
  );
}

// ─── Seed data ────────────────────────────────────────────────────────────────

const CHECKLIST_SEED = [
  {
    id: 1,
    number: '01',
    title: 'Morning Skincare Ritual',
    subtitle: 'Cleanser → toner → moisturiser SPF 30',
    completed: true,
  },
  {
    id: 2,
    number: '02',
    title: 'Outfit Upgrade',
    subtitle: 'Try the fitted navy tee with dark slim chinos',
    completed: false,
  },
  {
    id: 3,
    number: '03',
    title: '30-Min Fitness Circuit',
    subtitle: 'Push / Pull / Squat — bodyweight, no equipment',
    completed: false,
  },
];

const PILLAR_DATA = [
  { label: 'Style',    value: '5/6', progress: 83 },
  { label: 'Fitness',  value: '4/6', progress: 67 },
  { label: 'Grooming', value: '6/6', progress: 100 },
];

const SCORE_BARS = [
  { label: 'Style',    pct: 78 },
  { label: 'Fitness',  pct: 65 },
  { label: 'Grooming', pct: 80 },
];

// ─── DashboardScreen ──────────────────────────────────────────────────────────

export default function DashboardScreen() {
  const [items, setItems] = useState(CHECKLIST_SEED);

  const toggle = (id) =>
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, completed: !item.completed } : item))
    );

  const doneCount   = items.filter((i) => i.completed).length;
  const progressPct = Math.round((doneCount / items.length) * 100);

  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: 'linear-gradient(180deg, #0F1420 0%, #0B0F19 100%)',
        fontFamily: '"Plus Jakarta Sans", Inter, sans-serif',
      }}
    >

      {/* ══════════════════════════════════════════════════════════════════════
          NAVIGATION HEADER
          Script logo left | Day indicator + avatar right
          Frosted glass effect keeps it legible over any content below.
      ══════════════════════════════════════════════════════════════════════ */}
      <header
        className="sticky top-0 z-20 flex items-center justify-between px-5 py-3
          border-b border-white/[0.05]"
        style={{
          backgroundColor: 'rgba(11,15,25,0.82)',
          backdropFilter:  'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
        }}
      >
        {/* Wordmark — ivory on dark, Pinyon Script via SVG */}
        <RizeLogo className="w-24 h-9" />

        <div className="flex items-center gap-3">
          {/* Live day indicator — the cyan pulse dot signals "active journey" */}
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full
              border border-white/[0.08] bg-white/[0.03]"
          >
            <div
              className="w-1.5 h-1.5 rounded-full bg-[#00F5D4] animate-pulse"
              style={{ boxShadow: '0 0 6px rgba(0,245,212,0.9)' }}
            />
            <span className="text-xs font-semibold text-white/65 tracking-wider">
              Day 12 / 30
            </span>
          </div>

          {/* User avatar */}
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center
              border border-white/10 bg-[#161F30]"
          >
            <span className="text-xs font-bold text-white/55">Y</span>
          </div>
        </div>
      </header>

      {/* ══════════════════════════════════════════════════════════════════════
          BENTO GRID
          Max-width 680px keeps it phone-sized even on desktop preview.
          3-column outer grid with a nested 4-column row for the stats strip.
      ══════════════════════════════════════════════════════════════════════ */}
      <main className="p-4 max-w-[680px] mx-auto space-y-3">

        {/* ── Row 1: Checklist (2/3) + Score ring (1/3) ─────────────────── */}
        <div className="grid grid-cols-3 gap-3">

          {/* ┌─────────────────────────────────────┐ */}
          {/* │  CELL A — Today's Routine Checklist │ */}
          {/* └─────────────────────────────────────┘ */}
          <div
            className="col-span-2 bg-[#161F30] rounded-[16px] overflow-hidden
              border border-white/[0.04]
              shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.35)]"
          >
            {/* Card header */}
            <div className="flex items-center justify-between px-4 pt-4 pb-3">
              <div>
                <p
                  className="text-white/40 font-semibold uppercase tracking-widest"
                  style={{ fontSize: '0.6rem' }}
                >
                  Today's Routine
                </p>
                <h2 className="text-sm font-bold text-white mt-0.5">
                  {doneCount} / {items.length} actions complete
                </h2>
              </div>

              {/* Mini progress readout */}
              <div className="flex flex-col items-end gap-1.5">
                <span
                  className="font-bold text-[#00F5D4] tabular-nums"
                  style={{ fontSize: '0.75rem' }}
                >
                  {progressPct}%
                </span>
                <div className="w-16 h-[3px] rounded-full bg-white/[0.08]">
                  <div
                    className="h-[3px] rounded-full transition-all duration-500"
                    style={{
                      width: `${progressPct}%`,
                      backgroundColor: '#00F5D4',
                      boxShadow: '0 0 6px rgba(0,245,212,0.5)',
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Hairline divider */}
            <div className="mx-4 h-px bg-white/[0.05]" />

            {/* Checklist items */}
            <div className="py-2">
              {items.map((item) => (
                <ChecklistItem
                  key={item.id}
                  {...item}
                  onToggle={() => toggle(item.id)}
                />
              ))}
            </div>
          </div>

          {/* ┌──────────────────┐ */}
          {/* │  CELL B — Score  │ */}
          {/* └──────────────────┘ */}
          <div
            className="col-span-1 bg-[#161F30] rounded-[16px]
              border border-white/[0.04]
              shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.35)]
              flex flex-col items-center justify-start p-4 gap-4"
          >
            <p
              className="text-white/40 font-semibold uppercase tracking-widest self-start"
              style={{ fontSize: '0.6rem' }}
            >
              Glow Score
            </p>

            <ProgressRing
              progress={72}
              size={90}
              stroke={6}
              value="72"
              sublabel="/ 100"
            />

            <div className="w-full h-px bg-white/[0.05]" />

            {/* Sub-pillar bars */}
            <div className="w-full flex flex-col gap-2">
              {SCORE_BARS.map((bar) => (
                <SubPillarBar key={bar.label} {...bar} />
              ))}
            </div>
          </div>
        </div>

        {/* ── Row 2: 4 Micro-stat cells ────────────────────────────────────── */}
        <div className="grid grid-cols-4 gap-3">
          <StatCell label="Streak" value="14"  unit="days" accent />
          <StatCell label="Day"    value="12"  unit="/ 30" />
          <StatCell label="Sleep"  value="7.5" unit="hrs"  />
          <StatCell label="Water"  value="2.1" unit="L"    />
        </div>

        {/* ── Row 3: Pillar rings (2/3) + Progress photo (1/3) ─────────────── */}
        <div className="grid grid-cols-3 gap-3">

          {/* ┌───────────────────────────────┐ */}
          {/* │  CELL C — Weekly Pillar Rings │ */}
          {/* └───────────────────────────────┘ */}
          <div
            className="col-span-2 bg-[#161F30] rounded-[16px] p-5
              border border-white/[0.04]
              shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.35)]"
          >
            <p
              className="text-white/40 font-semibold uppercase tracking-widest mb-5"
              style={{ fontSize: '0.6rem' }}
            >
              Week 2 — Pillar Progress
            </p>

            <div className="flex items-center justify-around">
              {PILLAR_DATA.map(({ label, value, progress }) => (
                <ProgressRing
                  key={label}
                  progress={progress}
                  size={72}
                  stroke={5}
                  value={value}
                  sublabel="days"
                  label={label}
                />
              ))}
            </div>
          </div>

          {/* ┌────────────────────────┐ */}
          {/* │  CELL D — Photo Check  │ */}
          {/* └────────────────────────┘ */}
          <div
            className="col-span-1 bg-[#161F30] rounded-[16px] p-4
              border border-white/[0.04]
              shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_20px_rgba(0,0,0,0.35)]
              flex flex-col gap-3"
          >
            <p
              className="text-white/40 font-semibold uppercase tracking-widest"
              style={{ fontSize: '0.6rem' }}
            >
              Week 2 Photo
            </p>

            {/* Photo placeholder */}
            <div
              className="flex-1 min-h-[90px] rounded-xl bg-[#1F2D42]
                border border-dashed border-white/10
                flex flex-col items-center justify-center gap-2"
            >
              <div className="w-8 h-8 rounded-full bg-white/[0.05] flex items-center justify-center">
                {/* Camera icon */}
                <svg width="15" height="13" viewBox="0 0 15 13" fill="none">
                  <rect x="1" y="3.5" width="13" height="9" rx="1.5"
                    stroke="rgba(255,255,255,0.25)" strokeWidth="1.1"/>
                  <circle cx="7.5" cy="8" r="2.2"
                    stroke="rgba(255,255,255,0.25)" strokeWidth="1.1"/>
                  <path d="M5.5 3.5 L6.2 1.5 H8.8 L9.5 3.5"
                    stroke="rgba(255,255,255,0.25)" strokeWidth="1.1"
                    strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span
                className="text-white/20 text-center leading-snug"
                style={{ fontSize: '0.6rem' }}
              >
                Check-in<br />Sunday
              </span>
            </div>

            {/* Primary CTA — the one electric button on screen */}
            <button
              className="w-full py-2.5 rounded-xl font-bold uppercase tracking-widest
                text-[#0B0F19] text-[0.6rem] transition-all duration-150
                hover:opacity-90 active:scale-[0.97]"
              style={{
                backgroundColor: '#00F5D4',
                boxShadow: '0 0 18px rgba(0,245,212,0.22)',
              }}
            >
              Add Photo
            </button>
          </div>

        </div>{/* end Row 3 */}
      </main>
    </div>
  );
}
