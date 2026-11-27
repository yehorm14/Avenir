/** How a guide reply was produced, read defensively from the `/api/guide` reply.
 * Older backends send none of these fields; that reads as a prepared guide.
 */
import type { GuideProvenanceFields } from "./types";

export type GuideProvenance = {
  mode: "llm_grounded" | "prepared_demo";
  aiWritten: boolean;
  badge: string;
  model: string | null;
  basedOn: string[];
  checks: string | null;
  checkedFigures: string[];
  validationNote: string | null;
  fallbackNote: string | null;
};

export const MODEL_BADGE = "Written by the model from this role's evidence";
export const PREPARED_BADGE = "Prepared guide (no model connected)";
export const AI_LABEL = "AI-written, check the source";
export const FALLBACK_NOTE =
  "Model reply did not pass the figure checks; prepared answer shown.";

export function guideProvenance(reply: unknown): GuideProvenance {
  const fields: GuideProvenanceFields =
    reply && typeof reply === "object" ? (reply as GuideProvenanceFields) : {};
  const mode =
    fields.mode === "llm_grounded" ? "llm_grounded" : "prepared_demo";
  const checks =
    typeof fields.checks === "string" && fields.checks.trim()
      ? fields.checks.trim()
      : null;
  const model =
    typeof fields.model === "string" && fields.model.trim()
      ? fields.model.trim()
      : null;
  return {
    mode,
    aiWritten: fields.ai_written === true || mode === "llm_grounded",
    badge: mode === "llm_grounded" ? MODEL_BADGE : PREPARED_BADGE,
    model,
    basedOn: Array.isArray(fields.based_on)
      ? fields.based_on.filter(
          (line): line is string => typeof line === "string" && !!line.trim(),
        )
      : [],
    checks,
    checkedFigures:
      mode === "llm_grounded" &&
      checks === "passed" &&
      Array.isArray(fields.claims)
        ? [
            ...new Set(
              fields.claims.flatMap((claim) =>
                typeof claim?.text === "string" && claim.text.trim()
                  ? [claim.text.trim()]
                  : [],
              ),
            ),
          ]
        : [],
    validationNote:
      mode === "llm_grounded" && typeof fields.note === "string"
        ? fields.note.trim() || null
        : null,
    fallbackNote:
      checks?.toLowerCase().startsWith("fallback") &&
      checks.toLowerCase() !== "fallback: no model configured"
        ? FALLBACK_NOTE
        : null,
  };
}
