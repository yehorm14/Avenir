import type { Career, Metric, Preferences } from "./types";
import type { CareerContent, CareerOpportunity } from "./content";

export type PlanDocumentInput = {
  careers: Career[];
  preferences: Preferences;
  content: Record<string, CareerContent>;
  opportunities: CareerOpportunity[];
  sources: Record<string, { name?: string; url?: string }>;
};

export function resolvePlanRoute(
  content: Pick<CareerContent, "universities"> | undefined,
  savedRoute?: Preferences["routes"][string],
): Preferences["routes"][string] {
  return (
    savedRoute ??
    (content?.universities.length ? "university" : "apprenticeship")
  );
}

export function isRelativeDemand(metric?: Metric): boolean {
  return Object.prototype.hasOwnProperty.call(
    metric?.extra ?? {},
    "typical_occupation_trend",
  );
}

export function demandTrendLabel(metric?: Metric): string {
  return isRelativeDemand(metric)
    ? "Employment trend vs typical"
    : "Employment trend";
}

export function evidencePriceLabel(
  career?: Pick<Career, "evidence_metadata">,
): string {
  return career?.evidence_metadata?.price_label || "April 2025 prices";
}

export function planPrioritySummary(
  prefs: Pick<Preferences, "completed" | "weights">,
): string {
  if (!prefs.completed && prefs.weights.interest !== 0)
    return "No personal interest profile applied.";
  const entries = Object.entries(prefs.weights).filter(
    ([key]) => prefs.completed || key !== "interest",
  );
  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  const summary = entries
    .map(([key, value]) => {
      const label =
        key === "need"
          ? prefs.completed
            ? "Historical demand"
            : "Historical employment trend"
          : key[0].toUpperCase() + key.slice(1);
      return `${label} ${Math.round(total ? (value / total) * 100 : 100 / entries.length)}%`;
    })
    .join(" · ");
  return prefs.completed ? summary : `${summary} · No interest profile used`;
}

export function metricCaveats(metric?: Metric): string {
  if (!metric) return "";
  const notes: Record<string, string> = {
    imputed_parent: "Estimated from a wider occupation group.",
    provisional: "Provisional; may be revised.",
    mock: "Sample data, not a real observation.",
    suppressed: "Withheld because the estimate is unreliable.",
    cv_high: "Sampling error is high; treat with caution.",
    category_level: "Broad job-advert category, not this exact occupation.",
    sources_disagree: "Research sources disagree; the range is wider.",
    multi_isco:
      "Several international job codes are combined; inspect the research range.",
    bridged_low_purity:
      "The older occupation code mixed several jobs; pre-2021 estimates may not describe this job well.",
    ons_indicative_counts:
      "ONS says its job counts are indicative, not accurate estimates.",
    partial_sources: "Part of the source data is missing; confidence is lower.",
    fallback_all_employees:
      "Full-time figures were sparse; this uses all employees (full- and part-time).",
  };
  return (
    metric.flags
      ?.map((flag) => notes[flag])
      .filter(Boolean)
      .join(" ") ?? ""
  );
}

const escape = (v: unknown) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (s) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        s
      ]!,
  );
const link = (label: string, url?: string) => {
  if (!url || !/^https?:\/\//i.test(url)) return escape(label);
  return `<a href="${escape(url)}">${escape(label)}</a>`;
};

export function buildPlanDocument(plan: PlanDocumentInput): string {
  const { preferences: prefs } = plan;
  const priorities = planPrioritySummary(prefs);
  const careers = plan.careers
    .map((c, i) => {
      const content = plan.content[c.soc];
      const metrics = (
        [
          ["pay_median", "Median annual pay"],
          ["demand_trend", demandTrendLabel(c.metrics.demand_trend)],
          ["exposure", "Automation task exposure"],
        ] as const
      )
        .map(([key, label]) => {
          const m = c.metrics[key];
          const missing =
            !m ||
            m.value == null ||
            m.status === "pending" ||
            m.flags?.includes("suppressed");
          const format = (value: number) =>
            key === "pay_median"
              ? `£${Math.round(value).toLocaleString("en-GB")}`
              : key === "demand_trend"
                ? `${(value * 100).toFixed(1)}% / year`
                : `${(value * 100).toFixed(0)} / 100`;
          const number = missing ? "Not available" : format(m.value!);
          const range =
            !missing && m.low != null && m.high != null
              ? `<br>Supplied range: ${escape(format(m.low))} to ${escape(format(m.high))}.`
              : "";
          const relative =
            key === "demand_trend" && isRelativeDemand(m)
              ? " Change relative to the typical occupation; not absolute job growth."
              : "";
          const source = m ? plan.sources[m.source] : undefined;
          return `<li><strong>${escape(label)}: ${escape(number)}</strong>${m ? `<br><small>${link(source?.name ?? m.source, source?.url)} · ${escape(m.as_of)} · ${escape(m.status)}${m.confidence ? ` · ${escape(m.confidence)} confidence` : ""}${range}<br>${escape(m.note)}${escape(relative)} ${escape(metricCaveats(m))}</small>` : ""}</li>`;
        })
        .join("");
      const steps = (content?.firstSteps ?? [])
        .map(
          (s, n) =>
            `<li>${prefs.checked.includes(`${c.soc}-${n}`) ? "<strong>Completed</strong>" : "Next action"}: ${escape(s)}</li>`,
        )
        .join("");
      const route =
        resolvePlanRoute(content, prefs.routes[c.soc]) === "apprenticeship"
          ? "Earn and learn"
          : "University";
      const courses = (content?.universities ?? [])
        .map((u) => `<li>${link(`${u.name}: ${u.course}`, u.url)}</li>`)
        .join("");
      return `<section><p class="rank">${i === 0 ? "First choice" : `Alternative ${i}`}</p><h2>${escape(c.title)}</h2><p>${escape(content?.intro ?? c.summary)}</p><p><strong>Route to explore:</strong> ${route}. Check entry requirements and availability in ${escape(prefs.nation)}.</p>${prefs.notes[c.soc] ? `<h3>Why I am exploring this</h3><p class="personal-note">${escape(prefs.notes[c.soc])}</p>` : ""}<ul class="evidence">${metrics}</ul><h3>My next actions</h3><ul>${steps}</ul>${courses ? `<details><summary>Course examples to check</summary><ul>${courses}</ul></details>` : ""}</section>`;
    })
    .join("");
  const saved = plan.opportunities
    .filter((o) => prefs.saved.includes(o.id))
    .map((o) => `<li>${link(o.title, o.url)} · ${escape(o.location)}</li>`)
    .join("");
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Avenir career plan</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#18212d;background:#fff;max-width:800px;margin:48px auto;padding:0 24px}h1{font-size:36px;line-height:1.15}h2{font-size:27px;margin:4px 0 12px}h3{font-size:18px;margin:24px 0 8px}p{margin:10px 0}a{color:#1857a7;overflow-wrap:anywhere}section{padding:28px 0;border-top:1px solid #c5cbd3;break-inside:avoid}.rank,small,footer{color:#4b596a}.rank{font-weight:600}.evidence{padding-left:20px}.evidence li{margin-bottom:12px}.personal-note{white-space:pre-wrap}footer{margin-top:36px;padding-top:20px;border-top:1px solid #c5cbd3;font-size:13px}@media print{body{margin:0;max-width:none;font-size:11pt}details{display:block}details ul{display:block}a{color:inherit}section{break-inside:auto}}@page{margin:18mm}</style></head><body><header><p>Avenir</p><h1>My career plan</h1><p>${escape(priorities)}</p><p>Compare the evidence, try the work, then revisit the choice. This is my current direction, not a prediction of my future.</p></header>${careers}${saved ? `<section><h2>Saved opportunities</h2><ul>${saved}</ul><p>These are organiser links, not confirmed vacancies or event bookings. Check current dates, eligibility, costs and accessibility.</p></section>` : ""}<footer><p>Pay is a workforce median, not a starting salary. Employment trends are historical. Automation exposure measures tasks, not the probability of losing a job. Interest and balance are preliminary comparison indices, not a validated assessment. Missing evidence stays missing.</p><p>Pathways and projects are curated exploration examples. Personal priorities and the final decision remain mine. Prepared guidance works without a live AI provider.</p><p>This exported file contains the personal notes I chose to include. Open it in a browser to print or save as PDF. My editable plan stays on the browser where I created it.</p></footer></body></html>`;
}
