import type { CareerSummary, ComponentKey, Confidence, Letter } from "../types";

export const COLOR: Record<ComponentKey, string> = {
  interest: "var(--c-interest)",
  demand_future: "var(--c-future)",
  demand_now: "var(--c-now)",
  pay: "var(--c-pay)",
  ai_resilience: "var(--c-ai)",
  head_start: "var(--c-head)",
};

export const SIGNALS: { key: ComponentKey; label: string; short: string }[] = [
  { key: "interest", label: "Fits your interests", short: "Fit" },
  { key: "demand_future", label: "UK need by 2035", short: "Demand 2035" },
  { key: "demand_now", label: "UK need now", short: "Demand now" },
  { key: "pay", label: "Pay", short: "Pay" },
  { key: "ai_resilience", label: "AI resilience", short: "AI resilience" },
  { key: "head_start", label: "Your head start", short: "Head start" },
];

export const LETTER_NAME: Record<Letter, string> = {
  R: "Realistic",
  I: "Investigative",
  A: "Artistic",
  S: "Social",
  E: "Enterprising",
  C: "Conventional",
};

export const LETTER_HINT: Record<Letter, string> = {
  R: "Hands-on, practical",
  I: "Curious, analytical",
  A: "Creative, expressive",
  S: "Helping, teaching",
  E: "Leading, persuading",
  C: "Organised, precise",
};

export function ScoreRing({ score, size = 72 }: { score: number; size?: number }) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div className="ring" style={{ width: size, height: size }} aria-label={`Score ${Math.round(score)} out of 100`}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth="6" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--accent)" strokeWidth="6" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)}
          style={{ transition: "stroke-dashoffset .7s cubic-bezier(.2,.8,.2,1)" }}
        />
      </svg>
      <div className="num">
        <div>
          {Math.round(score)}
          <small>of 100</small>
        </div>
      </div>
    </div>
  );
}

export function ScoreStack({ career }: { career: CareerSummary }) {
  return (
    <div className="stack" role="img" aria-label="How the score is made up">
      {career.components.map((c) =>
        c.contribution > 0 ? <div key={c.key} style={{ width: `${c.contribution}%`, background: COLOR[c.key] }} /> : null,
      )}
    </div>
  );
}

export function Breakdown({ career }: { career: CareerSummary }) {
  return (
    <ul className="breakdown">
      {career.components.map((c) => (
        <li key={c.key}>
          <span className="sw" style={{ background: c.value === null ? "var(--line)" : COLOR[c.key] }} />
          <span>
            <span className="lbl">{c.label}</span>
            <span className={`det ${c.value === null ? "nodata" : ""}`}>{c.value === null ? `No data. ${c.detail}` : c.detail}</span>
          </span>
          <span className="pts">{c.value === null ? "—" : `+${c.contribution.toFixed(0)}`}</span>
        </li>
      ))}
    </ul>
  );
}

export function ConfidenceBadge({ c }: { c: Confidence }) {
  const n = c.level === "High" ? 3 : c.level === "Medium" ? 2 : 1;
  return (
    <span className={`conf ${c.level}`} title={c.reasons.join(" · ")}>
      <span className="bars" aria-hidden>
        {[6, 9, 12].map((h, i) => <i key={h} className={i < n ? "on" : ""} style={{ height: h }} />)}
      </span>
      {c.level} confidence
    </span>
  );
}

export function ProfileBars({ profile }: { profile: Record<Letter, number> }) {
  const letters = (Object.keys(LETTER_NAME) as Letter[]).sort((a, b) => profile[b] - profile[a]);
  return (
    <div className="profile">
      {letters.map((l) => (
        <div className="pbar" key={l} title={LETTER_HINT[l]}>
          <span>{LETTER_NAME[l]}</span>
          <span className="track">
            <span className="fill" style={{ width: `${Math.round(profile[l] * 100)}%`, display: "block" }} />
          </span>
          <span className="v">{Math.round(profile[l] * 100)}</span>
        </div>
      ))}
    </div>
  );
}

export function SyntheticBanner({ children }: { children?: React.ReactNode }) {
  return (
    <div className="banner" role="note">
      <b>Synthetic</b>
      <span>{children ?? "This track record runs on generated demo data. It shows how the self-grade works, not how good the signal is."}</span>
    </div>
  );
}

export function Spinner() {
  return <div className="spinner" role="status" aria-label="Loading" />;
}

export function Check() {
  return (
    <svg width="14" height="14" viewBox="0 0 32 32" aria-hidden>
      <path d="M8 22 L14 14 L19 18 L25 9" stroke="white" strokeWidth="3.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function money(n: number) {
  return `£${Math.round(n).toLocaleString("en-GB")}`;
}

export function moneyK(n: number | null) {
  return n === null ? "No data" : `£${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}k`;
}

export function signed(n: number) {
  return `${n > 0 ? "+" : ""}${n}`;
}

export function nationOf(region: string) {
  return ["Scotland", "Wales", "Northern Ireland"].includes(region) ? region : "England";
}
