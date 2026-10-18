import type { Preferences } from "./types";

export const initial: Preferences = {
  answers: {},
  step: 0,
  completed: false,
  selected: [],
  weights: { pay: 30, interest: 45, need: 25 },
  location: "Glasgow",
  nation: "Scotland",
  checked: [],
  saved: [],
  routes: {},
  notes: {},
};

const record = (v: unknown): Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : {};
const text = (v: unknown, fallback = "", max = 2000) =>
  typeof v === "string" ? v.slice(0, max) : fallback;
const strings = (v: unknown) =>
  Array.isArray(v)
    ? [
        ...new Set(
          v.filter(
            (s): s is string => typeof s === "string" && s.length <= 120,
          ),
        ),
      ].slice(0, 200)
    : [];
const discoveryNotices = (v: unknown): string[] =>
  Array.isArray(v)
    ? [
        ...new Set(
          v
            .slice(0, 20)
            .filter(
              (s): s is string =>
                typeof s === "string" &&
                s.length <= 2000 &&
                s.trim().length > 0,
            ),
        ),
      ]
    : [];
const index = (v: unknown, max: number) =>
  typeof v === "number" && Number.isInteger(v) && v >= 0 ? Math.min(max, v) : 0;
const soc = (v: string) => /^\d{4}$/.test(v);

export function normalisePreferences(raw: unknown): Preferences {
  const r = record(raw),
    weights = record(r.weights),
    draft = record(r.discovery);
  const routes: Preferences["routes"] = {},
    notes: Preferences["notes"] = {};
  for (const [key, val] of Object.entries(record(r.routes))) {
    if (soc(key) && (val === "university" || val === "apprenticeship"))
      routes[key] = val;
  }
  for (const [key, val] of Object.entries(record(r.notes))) {
    if (soc(key) && typeof val === "string") notes[key] = text(val);
  }
  const answers: Record<string, number> = {};
  for (const [key, val] of Object.entries(record(r.answers))) {
    if (typeof val === "number" && Number.isInteger(val) && val >= 0 && val < 4)
      answers[key] = val;
  }
  const result: Preferences = {
    ...structuredClone(initial),
    answers,
    routes,
    notes,
    step: index(r.step, 50),
    completed: r.completed === true,
    selected: strings(r.selected).filter(soc).slice(0, 3),
    checked: strings(r.checked).filter((s) => /^\d{4}-[0-2]$/.test(s)),
    saved: strings(r.saved),
    location: text(r.location, initial.location, 100),
    nation: ["Scotland", "England", "Wales", "Northern Ireland"].includes(
      String(r.nation),
    )
      ? String(r.nation)
      : initial.nation,
    weights: { ...initial.weights },
  };
  for (const key of ["pay", "interest", "need"] as const) {
    const v = weights[key];
    if (typeof v === "number" && Number.isFinite(v) && v >= 0 && v <= 100)
      result.weights[key] = v;
  }
  if (draft.mode === "known" || draft.mode === "explore") {
    const draftAnswers: Record<string, string> = {};
    for (const key of [
      "direction",
      "interests",
      "subjects",
      "values",
      "skills",
    ]) {
      const v = record(draft.answers)[key];
      if (typeof v === "string") draftAnswers[key] = text(v, "", 4000);
    }
    result.discovery = {
      mode: draft.mode,
      answers: draftAnswers,
      step: index(draft.step, 5),
      ...(Array.isArray(draft.tags) ? { tags: strings(draft.tags) } : {}),
      ...(typeof draft.targetSoc === "string" && soc(draft.targetSoc)
        ? { targetSoc: draft.targetSoc }
        : {}),
      ...(typeof draft.referenceSoc === "string" && soc(draft.referenceSoc)
        ? { referenceSoc: draft.referenceSoc }
        : {}),
      ...(typeof draft.summary === "string"
        ? { summary: text(draft.summary) }
        : {}),
      ...(Array.isArray(draft.notices)
        ? { notices: discoveryNotices(draft.notices) }
        : {}),
    };
  }
  return result;
}
