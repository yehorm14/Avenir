import type { HistoryPoint } from "./types";

export function historySegments(
  points: HistoryPoint[],
  key: "pay_median" | "pay_median_real" | "jobs_k",
): HistoryPoint[][] {
  const segments: HistoryPoint[][] = [];
  let current: HistoryPoint[] = [];
  for (const point of points) {
    const previous = current[current.length - 1];
    if (previous && point.year > previous.year + 1) {
      segments.push(current);
      current = [];
    }
    if (typeof point[key] !== "number" || point.year === 2021) {
      if (current.length) segments.push(current);
      current =
        key !== "jobs_k" && point.year === 2021 && current.length
          ? [current[current.length - 1]]
          : [];
    }
    if (typeof point[key] === "number") current.push(point);
  }
  if (current.length) segments.push(current);
  return segments;
}
