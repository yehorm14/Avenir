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
  });
  if (!r.ok) {
    const err = await r.json().catch(() => null);
    throw new Error(
      typeof err?.detail === "string"
        ? err.detail
        : "We couldn't load that. Try again in a moment.",
    );
  }
  return r.json();
}
