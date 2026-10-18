/** The `/api/guide` request body and the view-model for a reply's links and path.
 * No imports beyond types, so the node tests can load this file on its own.
 */
import type { GuideLink, GuidePath, GuideProfile, Weights } from "./types";

export type GuideHistoryTurn = { role: "user" | "assistant"; content: string };
export type QuizState = {
  tags: string[];
  weights: Weights;
  selected: string[];
  freeText?: string | null;
  /** From `/api/health` or the bootstrap: the backend knows the `profile` field. */
  acceptsProfile?: boolean;
};
export type GuideRequestBody = {
  soc: string;
  message: string;
  history: GuideHistoryTurn[];
  profile?: GuideProfile;
};
export type GuideReplyExtras = {
  links: GuideLink[];
  path: GuidePath | null;
  profileUsed: boolean;
};

const SOC = /^\d{4}$/;
const TAG_LIMIT = 32;
const SELECTED_LIMIT = 5;
const FREE_TEXT_LIMIT = 500;

const clampWeight = (value: unknown) =>
  typeof value === "number" && Number.isFinite(value)
    ? Math.min(100, Math.max(0, Math.round(value)))
    : 0;
const uniqueStrings = (
  values: unknown,
  limit: number,
  keep = (_: string) => true,
) =>
  Array.isArray(values)
    ? [
        ...new Set(
          values.filter(
            (s): s is string => typeof s === "string" && !!s.trim() && keep(s),
          ),
        ),
      ].slice(0, limit)
    : [];

/** The body for `/api/guide`; `profile` is added only when the backend accepts it and the quiz gave something. */
export function buildGuideRequest(
  soc: string,
  message: string,
  history: GuideHistoryTurn[],
  quizState?: QuizState | null,
): GuideRequestBody {
  const body: GuideRequestBody = { soc, message, history };
  if (!quizState || quizState.acceptsProfile !== true) return body;
  const tags = uniqueStrings(quizState.tags, TAG_LIMIT, (s) => s.length <= 64);
  const selected = uniqueStrings(quizState.selected, SELECTED_LIMIT, (s) =>
    SOC.test(s),
  );
  if (!tags.length && !selected.length) return body;
  const freeText =
    typeof quizState.freeText === "string" && quizState.freeText.trim()
      ? quizState.freeText.trim().slice(0, FREE_TEXT_LIMIT)
      : null;
  return {
    ...body,
    profile: {
      tags,
      weights: {
        pay: clampWeight(quizState.weights?.pay),
        interest: clampWeight(quizState.weights?.interest),
        need: clampWeight(quizState.weights?.need),
      },
      selected,
      free_text: freeText,
    },
  };
}

/** Quiz tag ids as words for the chip: "computers_coding" reads "computers coding". */
export function tagWords(tags: string[]): string {
  return tags.map((tag) => tag.replace(/_/g, " ")).join(", ");
}

/** True for an in-app hash route or an http(s) URL; anything else is dropped. */
export function safeHref(href: unknown): href is string {
  if (typeof href !== "string") return false;
  if (/^#\/[\w/-]*$/.test(href)) return true;
  try {
    const url = new URL(href);
    return (
      ["https:", "http:"].includes(url.protocol) &&
      !url.username &&
      !url.password
    );
  } catch {
    return false;
  }
}

const str = (value: unknown) =>
  typeof value === "string" && value.trim() ? value.trim() : "";

/** Links and path from a reply, read defensively; older backends send neither. */
export function guideReplyExtras(reply: unknown): GuideReplyExtras {
  const fields =
    reply && typeof reply === "object"
      ? (reply as Record<string, unknown>)
      : {};
  const seen = new Set<string>();
  const links: GuideLink[] = [];
  for (const item of Array.isArray(fields.links) ? fields.links : []) {
    const link = item as Record<string, unknown>;
    const href = link?.href;
    if (!link || !safeHref(href) || seen.has(href)) continue;
    seen.add(href);
    links.push({ label: str(link.label) || href, href });
  }
  const raw =
    fields.path && typeof fields.path === "object"
      ? (fields.path as Record<string, unknown>)
      : null;
  let path: GuidePath | null = null;
  if (raw) {
    const routes = (Array.isArray(raw.routes) ? raw.routes : [])
      .map((r) => r as Record<string, unknown>)
      .filter((r) => r && str(r.label))
      .map((r) => ({ label: str(r.label), summary: str(r.summary) }));
    const courses = (Array.isArray(raw.courses) ? raw.courses : [])
      .map((c) => c as Record<string, unknown>)
      .filter((c) => c && str(c.label))
      .map((c) =>
        safeHref(c.href)
          ? { label: str(c.label), href: c.href }
          : { label: str(c.label) },
      );
    const skills = uniqueStrings(raw.skills, 12);
    const grades_note = str(raw.grades_note);
    const first_step = str(raw.first_step);
    if (
      routes.length ||
      courses.length ||
      skills.length ||
      grades_note ||
      first_step
    )
      path = { routes, courses, skills, grades_note, first_step };
  }
  return { links, path, profileUsed: fields.profile_used === true };
}
