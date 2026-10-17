import { useCallback, useEffect, useState } from "react";
import type { Weights } from "./types";

// Everything here lives in this browser only. Nothing is kept on a server.

export const DEFAULT_WEIGHTS: Weights = {
  interest: 0.3, demand_future: 0.2, demand_now: 0.15, pay: 0.15, ai_resilience: 0.1, head_start: 0.1,
};
export const STORAGE_KEYS = ["cp.answers", "cp.subjects", "cp.skills", "cp.weights.v2", "cp.watch", "cp.region", "cp.nation"];
export const MAX_WATCH = 5;

export interface Watched {
  soc: string;
  title: string;
  edition: string; // report edition when the user followed it
}

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* private mode or blocked storage: keep working in memory */
  }
}

export function clearAll() {
  try {
    STORAGE_KEYS.forEach((k) => localStorage.removeItem(k));
    Object.keys(localStorage).filter((k) => k.startsWith("cp.")).forEach((k) => localStorage.removeItem(k));
  } catch {
    /* nothing stored */
  }
}

export function usePersistent<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => read(key, fallback));
  useEffect(() => write(key, value), [key, value]);
  return [value, setValue] as const;
}

export function useHashRoute(): [string[], (path: string) => void] {
  const parse = () => (window.location.hash.replace(/^#\/?/, "") || "").split("/").filter(Boolean);
  const [parts, setParts] = useState<string[]>(parse);
  useEffect(() => {
    const on = () => {
      setParts(parse());
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const go = useCallback((path: string) => {
    window.location.hash = `/${path}`;
  }, []);
  return [parts, go];
}
