import type { Page, Preferences } from "./types";

/** Amira, 17, S6 in Glasgow: sample quiz answers, no personal details. Used by the guided example. */
export const amiraAnswers: Record<string, string> = {
  direction: "Architect",
  interests: "Making or designing something; Solving a tricky problem",
  subjects: "Maths; Art and design",
  values: "Long-term demand; Making a useful impact",
  skills: "Maths and data; Drawing or design",
};

/** True while the saved plan came from Amira's prepared answers (unchanged by the visitor's own quiz). */
export function isExampleProfile(
  prefs: Pick<Preferences, "completed" | "discovery">,
): boolean {
  const answers = prefs.discovery?.answers;
  return (
    prefs.completed &&
    prefs.discovery?.mode === "known" &&
    !!answers &&
    Object.entries(amiraAnswers).every(([key, value]) => answers[key] === value)
  );
}

/** The guided journey: answers, then matches, then the evidence, then the plan. */
export const exampleSteps: { page: Page; label: string }[] = [
  { page: "matches", label: "Quiz answers and matches" },
  { page: "evidence", label: "Compare the evidence" },
  { page: "overview", label: "Your plan" },
];
