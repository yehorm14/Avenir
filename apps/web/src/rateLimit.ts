/** Friendly text for HTTP 429 from the rate-limited `/api/guide` and `/api/tts` routes. */

export const GUIDE_RATE_LIMITED =
  "The guide is getting a lot of questions. Try again in a minute.";
export const VOICE_RATE_LIMITED =
  "The voice is resting. Read the text instead, or try again in a minute.";

/** The message for a 429 on this API path, or null when the status or path is not rate limited. */
export function rateLimitMessage(status: number, path: string): string | null {
  if (status !== 429) return null;
  if (path === "tts" || path.startsWith("tts?")) return VOICE_RATE_LIMITED;
  if (path === "guide" || path.startsWith("guide?")) return GUIDE_RATE_LIMITED;
  return "Too many requests. Try again in a minute.";
}
