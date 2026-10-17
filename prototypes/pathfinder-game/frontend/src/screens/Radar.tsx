import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";
import type { Opportunity, Radar as RadarData, Trend } from "../types";
import { Spinner } from "../components/ui";
import { XP_PER_TICK } from "../game";
import { usePersistent } from "../store";

interface Props {
  partyFields: string[];
  nation: string;
  onNation: (n: string) => void;
  onPath: (soc: string) => void;
  onCharacter: () => void;
}

const STAGES = [
  { id: "school", label: "School" },
  { id: "college", label: "College" },
  { id: "university", label: "University" },
];
const NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"];

const KIND: Record<string, { label: string; tone: string }> = {
  "work-experience": { label: "Work experience", tone: "green" },
  "open-day": { label: "Open day", tone: "blue" },
  hackathon: { label: "Hackathon", tone: "orange" },
  programme: { label: "Programme", tone: "blue" },
  competition: { label: "Competition", tone: "orange" },
  community: { label: "Community", tone: "green" },
  course: { label: "Course", tone: "" },
  event: { label: "Event", tone: "blue" },
  resource: { label: "Guide", tone: "" },
  mentoring: { label: "Mentoring", tone: "green" },
};

const GROUPS: { id: Opportunity["status"]; title: string; hint: string }[] = [
  { id: "open", title: "In their usual opening window now", hint: "Check the organiser: these often close earlier than you expect." },
  { id: "soon", title: "Opening next month", hint: "Get ready: note the dates and prepare your application." },
  { id: "rolling", title: "Open all year", hint: "You can start any of these today." },
  { id: "later", title: "Later in the year", hint: "Put these in your diary." },
];

function OppCard({ o, done, onDone, fresh }: { o: Opportunity; done: boolean; onDone: () => void; fresh: boolean }) {
  const k = KIND[o.kind] ?? { label: o.kind, tone: "" };
  return (
    <article className="card opp">
      <div className="row" style={{ gap: 8 }}>
        <span className={`tag ${k.tone}`}>{k.label}</span>
        {fresh && <span className="tag blue">New</span>}
        {o.deadline && <span className={`tag ${o.closing_soon ? "orange" : ""}`}>{o.closing_soon ? "Closing soon · " : "Closes "}{new Date(o.deadline + "T12:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</span>}
        <span className="tiny">{o.format} · {o.cost}</span>
      </div>
      <h3 className="h3">{o.title}</h3>
      <div className="small muted" style={{ marginTop: -4 }}>{o.org}</div>
      <p className="small" style={{ margin: 0 }}>{o.why}</p>
      <p className="tiny" style={{ margin: 0 }}><b>Timing:</b> {o.when}</p>
      <div className="pills">{o.matches.map((m) => <span className="tag" key={m}>{m}</span>)}</div>
      <div className="row opp-actions" style={{ justifyContent: "space-between" }}>
        {o.url ? <a className="btn soft small" href={o.url} target="_blank" rel="noreferrer">Organiser site ›</a> : <span />}
        <label className="small row" style={{ gap: 8, cursor: "pointer" }}>
          <input type="checkbox" checked={done} onChange={onDone} style={{ width: 18, height: 18, accentColor: "var(--accent)" }} />
          I've done this {done && <span className="xp-chip">+{XP_PER_TICK} XP</span>}
        </label>
      </div>
    </article>
  );
}

function TrendCard({ t, onPath }: { t: Trend; onPath: (soc: string) => void }) {
  return (
    <details className="card trend-card">
      <summary>
        <div>
          <b style={{ fontSize: 19, letterSpacing: "-0.015em" }}>{t.name}</b>
          <span className="tag orange" style={{ marginLeft: 10 }}>{t.heat}</span>
          <div className="small muted" style={{ marginTop: 4 }}>{t.buzz}</div>
        </div>
      </summary>
      <div style={{ display: "grid", gap: 14, marginTop: 14 }}>
        <p className="small" style={{ margin: 0 }}><b>The reality:</b> {t.reality}</p>
        <div className="two">
          <div className="panel">
            <h4>Specialist route</h4>
            <b>{t.specialist_name}</b>
            <div className="small muted">{t.specialist_level}</div>
            <div className="small" style={{ marginTop: 6, color: "var(--orange)" }}>{t.specialist_doors}</div>
          </div>
          <div className="panel">
            <h4>Keeps more doors open</h4>
            <div style={{ display: "grid", gap: 8 }}>
              {t.safer.map((s) => (
                <div key={s.subject}>
                  <b>{s.subject}</b> <span className="tag green">opens {s.doors.length} {s.doors.length === 1 ? "career" : "careers"}</span>
                  <div className="tiny">{s.why}</div>
                  <div className="tiny" title={s.doors.join(", ")}>{s.doors.slice(0, 4).join(" · ")}{s.doors.length > 4 ? " …" : ""}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="panel">
          <h4>If the trend fades</h4>
          <div className="small">{t.fade}</div>
        </div>
        <div>
          <div className="small muted" style={{ marginBottom: 6 }}>How to specialise later, step by step</div>
          <ol className="small" style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>{t.how.map((h) => <li key={h}>{h}</li>)}</ol>
        </div>
        {t.related.length > 0 && (
          <div className="pills">
            {t.related.map((r) => <button key={r.soc} className="chip" style={{ fontSize: 13, padding: "5px 12px" }} onClick={() => onPath(r.soc)}>{r.title} ›</button>)}
          </div>
        )}
        <p className="tiny" style={{ margin: 0 }}>{t.evidence_note}</p>
      </div>
    </details>
  );
}

export function RadarScreen({ partyFields, nation, onNation, onPath, onCharacter }: Props) {
  const [chosen, setChosen] = usePersistent<string[] | null>("cp.radar.fields", null);
  const [stage, setStage] = usePersistent<string>("cp.radar.stage", "school");
  const [done, setDone] = usePersistent<string[]>("cp.quest.opps", []);
  const [seen, setSeen] = usePersistent<{ date: string; ids: string[] }>("cp.radar.seen", { date: "", ids: [] });
  const [kind, setKind] = useState("all");
  const [data, setData] = useState<RadarData | null>(null);
  const [trends, setTrends] = useState<Trend[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const fresh = useRef<Set<string> | null>(null);
  const lastChecked = useRef(seen.date);

  const fields = chosen ?? partyFields;

  useEffect(() => {
    setErr(null);
    api.radar(fields, stage, nation).then(setData, (e) => setErr(String(e.message ?? e)));
  }, [fields.join(","), stage, nation]);

  useEffect(() => {
    api.trends().then(setTrends, () => setTrends([]));
  }, []);

  useEffect(() => {
    if (!data) return;
    if (fresh.current === null) fresh.current = new Set(seen.ids.length ? data.items.map((i) => i.id).filter((id) => !seen.ids.includes(id)) : []);
    const ids = Array.from(new Set([...seen.ids, ...data.items.map((i) => i.id)]));
    if (ids.length !== seen.ids.length || seen.date !== data.today) setSeen({ date: data.today, ids });
  }, [data]);

  const visible = useMemo(() => (data ? data.items.filter((i) => kind === "all" || i.kind === kind) : []), [data, kind]);
  const kinds = useMemo(() => Array.from(new Set((data?.items ?? []).map((i) => i.kind))), [data]);
  const toggleDone = (id: string) => setDone((d) => (d.includes(id) ? d.filter((x) => x !== id) : [...d, id]));
  const addable = (data?.all_fields ?? []).filter((f) => !fields.includes(f.id));
  const dateText = data ? new Date(data.today + "T12:00:00").toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" }) : "";
  const newCount = fresh.current ? data?.items.filter((i) => fresh.current!.has(i.id)).length ?? 0 : 0;

  return (
    <main className="page">
      <p className="eyebrow">Radar</p>
      <h1 className="title">What's open in your fields.</h1>
      <p className="lede">
        Know what you want to try but not where? Here are programmes, open days, hackathons, work experience and communities
        for your fields, many of them for people who aren't at university yet.
      </p>

      <div className="card" style={{ marginTop: 28, display: "grid", gap: 14 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 className="h3">Your fields</h2>
          {chosen !== null && <button className="btn ghost small" onClick={() => setChosen(null)}>Use my party's fields</button>}
        </div>
        <div className="pills">
          {fields.length === 0 && <span className="small muted">Pick a field to begin, or create your character and use your party's fields.</span>}
          {(data?.fields ?? []).map((f) => (
            <button key={f.id} className="chip on" onClick={() => setChosen(fields.filter((x) => x !== f.id))} aria-label={`Remove ${f.label}`}>
              {f.label} ✕
            </button>
          ))}
          <select className="mini-sel" value="" onChange={(e) => e.target.value && setChosen([...fields, e.target.value])} aria-label="Add a field">
            <option value="">Add a field…</option>
            {addable.map((f) => <option key={f.id} value={f.id}>{f.label}</option>)}
          </select>
        </div>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="seg" role="tablist" aria-label="Your stage">
            {STAGES.map((s) => (
              <button key={s.id} role="tab" aria-selected={stage === s.id} className={stage === s.id ? "on" : ""} onClick={() => setStage(s.id)}>{s.label}</button>
            ))}
          </div>
          <label className="small row" style={{ gap: 8 }}>
            I live in
            <select className="mini-sel" value={nation} onChange={(e) => onNation(e.target.value)} aria-label="Where you live">
              {NATIONS.map((n) => <option key={n}>{n}</option>)}
            </select>
          </label>
        </div>
        {fields.length === 0 && <button className="btn soft small" style={{ justifySelf: "start" }} onClick={onCharacter}>Create your character</button>}
      </div>

      {err && !data && <div className="notice warn" style={{ marginTop: 16 }}>Couldn't load the radar ({err}).</div>}
      {!data && !err && <Spinner />}

      {data && (
        <>
          <div className="card digest" style={{ marginTop: 16 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="eyebrow" style={{ margin: 0 }}>Today · {dateText}</span>
              <span className="tiny">
                {lastChecked.current ? `Last checked ${new Date(lastChecked.current + "T12:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short" })}` : "First visit"}
                {newCount > 0 && ` · ${newCount} new since then`}
              </span>
            </div>
            <div className="digest-nums">
              <div><b>{data.digest.open}</b><span>open now</span></div>
              <div><b>{data.digest.soon}</b><span>opening next month</span></div>
              <div><b>{data.digest.rolling}</b><span>open all year</span></div>
            </div>
            <p style={{ margin: 0 }}>{data.digest.headline}</p>
            {data.digest.highlights.length > 0 && (
              <ul className="small" style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 3 }}>
                {data.digest.highlights.map((h) => <li key={h}>{h}</li>)}
              </ul>
            )}
            <p className="tiny" style={{ margin: 0 }}>{data.note}</p>
          </div>

          <div className="chips no-print" style={{ marginTop: 20 }}>
            <button className={`chip ${kind === "all" ? "on" : ""}`} onClick={() => setKind("all")}>All</button>
            {kinds.map((k) => (
              <button key={k} className={`chip ${kind === k ? "on" : ""}`} onClick={() => setKind(k)}>{KIND[k]?.label ?? k}</button>
            ))}
          </div>

          {GROUPS.map((g) => {
            const list = visible.filter((i) => i.status === g.id);
            if (list.length === 0) return null;
            return (
              <section className="sec" key={g.id} style={{ marginTop: 40 }}>
                <h2 className="h2">{g.title} <span className="muted" style={{ fontWeight: 500 }}>· {list.length}</span></h2>
                <p className="muted small" style={{ marginTop: 4, marginBottom: 14 }}>{g.hint}</p>
                <div className="opp-grid">
                  {list.map((o) => <OppCard key={o.id} o={o} done={done.includes(o.id)} onDone={() => toggleDone(o.id)} fresh={!!fresh.current?.has(o.id)} />)}
                </div>
              </section>
            );
          })}
          {visible.length === 0 && <div className="notice" style={{ marginTop: 20 }}>Nothing matches these filters. Try another field, stage or type.</div>}
        </>
      )}

      <section className="sec" style={{ marginTop: 72 }}>
        <h2 className="h2">Trend check</h2>
        <p className="muted small" style={{ marginTop: 4, marginBottom: 16 }}>
          A field is hot, but hot fields cool. For each one, here's the specialist route and a broader degree that gets you
          there while keeping more doors open if the trend fades.
        </p>
        {!trends ? <Spinner /> : <div style={{ display: "grid", gap: 12 }}>{trends.map((t) => <TrendCard key={t.id} t={t} onPath={onPath} />)}</div>}
      </section>
    </main>
  );
}
