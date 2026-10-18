// Adapted from Max's local-only persistent store in prototypes/pathfinder-game.
import { useEffect, useState } from "react";
import type { Preferences } from "./types";
import { initial, normalisePreferences } from "./preferences";
export { initial } from "./preferences";
export function usePreferences() {
  const [value, setValue] = useState<Preferences>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem("avenir.v1") || "null");
      return normalisePreferences(raw);
    } catch {
      return structuredClone(initial);
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem("avenir.v1", JSON.stringify(value));
    } catch {
      /* Continue in memory when storage is blocked. */
    }
  }, [value]);
  return [value, setValue] as const;
}
export async function api<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const r = await fetch(`/api/${path}`, {
    signal,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    ...(body ? { method: "POST", body: JSON.stringify(body) } : {}),
  }).catch((error: unknown) => {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(
      "We couldn’t connect. Check your connection and try again.",
    );
  });
  const result = await r.json().catch(() => null);
  if (!r.ok || result?.ok === false) {
    const err = result;
    throw new Error(
      typeof err?.error?.message === "string"
        ? err.error.message
        : typeof err?.detail === "string"
          ? err.detail
          : "We couldn't load that. Try again in a moment.",
    );
  }
  return result && typeof result.ok === "boolean" && "data" in result
    ? result.data
    : result;
}
