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
      const last = current[current.length - 1];
      if (current.length) segments.push(current);
      // Seed the post-2021 segment with 2020 so the line stays continuous.
      current =
        point.year === 2021 &&
        typeof point[key] === "number" &&
        last &&
        last.year === 2020
          ? [last]
          : [];
    }
    if (typeof point[key] === "number") current.push(point);
  }
  if (current.length) segments.push(current);
  return segments;
}
