import type { Letter, QuizItem } from "./types";

// The game layer is a skin over the real analysis: stats are the interest profile,
// XP comes only from real-world evidence the player ticks, never from time spent.

export const LETTERS: Letter[] = ["R", "I", "A", "S", "E", "C"];

export const TRAIT: Record<Letter, { name: string; stat: string; tagline: string; color: string }> = {
  R: { name: "Builder", stat: "Build", tagline: "Hands-on and practical", color: "var(--c-R)" },
  I: { name: "Scholar", stat: "Think", tagline: "Curious and analytical", color: "var(--c-I)" },
  A: { name: "Creator", stat: "Create", tagline: "Imaginative and expressive", color: "var(--c-A)" },
  S: { name: "Guide", stat: "Help", tagline: "Caring and encouraging", color: "var(--c-S)" },
  E: { name: "Leader", stat: "Lead", tagline: "Persuasive and driven", color: "var(--c-E)" },
  C: { name: "Planner", stat: "Organise", tagline: "Careful and organised", color: "var(--c-C)" },
};

export type Profile = Record<Letter, number>;

export function profileFrom(answers: Record<string, number>, items: QuizItem[]): Profile {
  const sums = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 } as Profile;
  const counts = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 } as Profile;
  for (const it of items) {
    const a = answers[it.id];
    if (a === undefined) continue;
    sums[it.type] += (Math.min(5, Math.max(1, a)) - 1) / 4;
    counts[it.type] += 1;
  }
  const out = { ...sums };
  for (const l of LETTERS) out[l] = counts[l] ? sums[l] / counts[l] : 0;
  return out;
}

export function ranked(profile: Profile): Letter[] {
  return [...LETTERS].sort((a, b) => profile[b] - profile[a] || LETTERS.indexOf(a) - LETTERS.indexOf(b));
}

export function isFlat(profile: Profile): boolean {
  const v = LETTERS.map((l) => profile[l]);
  return Math.max(...v) === Math.min(...v);
}

export function className(profile: Profile): string {
  if (isFlat(profile)) return "Newcomer";
  const [a, b] = ranked(profile);
  return `${TRAIT[a].name}-${TRAIT[b].name.toLowerCase()}`;
}

export const XP_PER_TICK = 10;
export const LEVELS = [
  { xp: 0, name: "Newcomer" },
  { xp: 30, name: "Explorer" },
  { xp: 90, name: "Apprentice" },
  { xp: 180, name: "Practitioner" },
  { xp: 300, name: "Specialist" },
  { xp: 500, name: "Expert" },
];

export function levelFor(xp: number) {
  let i = 0;
  while (i + 1 < LEVELS.length && xp >= LEVELS[i + 1].xp) i++;
  const base = LEVELS[i].xp;
  const next = LEVELS[i + 1]?.xp ?? null;
  return { level: i + 1, name: LEVELS[i].name, base, next, pct: next === null ? 100 : Math.round(((xp - base) / (next - base)) * 100) };
}

/** XP from every ticked skill and quest on this device, optionally leaving one career out. */
export function readXp(exceptSoc?: string): number {
  let ticks = 0;
  try {
    for (const key of Object.keys(localStorage)) {
      const m = key.match(/^cp\.(path|quest)\.(.+)$/);
      if (!m || m[2] === exceptSoc) continue;
      const v = JSON.parse(localStorage.getItem(key) ?? "[]");
      if (Array.isArray(v)) ticks += v.length;
    }
  } catch {
    /* storage blocked: no XP yet */
  }
  return ticks * XP_PER_TICK;
}
