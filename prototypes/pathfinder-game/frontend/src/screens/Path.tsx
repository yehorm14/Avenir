import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { CareerSummary, DegreeOption, MatchRequest, PathPlan, SafePath, SkillItem } from "../types";
import { Spinner, money } from "../components/ui";
import { Avatar, XpBar } from "../components/Character";
import { Events } from "../components/Events";
import { XP_PER_TICK, className, readXp, type Profile } from "../game";
import { usePersistent } from "../store";

interface Props {
  soc: string;
  nation: string;
  onNation: (n: string) => void;
  onBack: () => void;
  backLabel: string;
  onAnalysis: (soc: string) => void;
  onOpen: (soc: string) => void;
  onCharacter: () => void;
  request: MatchRequest | null;
  profile: Profile;
}

const NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"];
const short = (n: string) => (n === "Northern Ireland" ? "NI" : n);

function Checklist({ items, done, toggle }: { items: SkillItem[]; done: string[]; toggle: (k: string) => void }) {
  return (
    <div className="list">
      {items.map((s) => {
        const on = done.includes(s.skill);
        return (
          <label className={`check ${on ? "done" : ""}`} key={s.skill}>
            <input type="checkbox" checked={on} onChange={() => toggle(s.skill)} />
            <span>
              <span className="name">{s.skill}</span>
              <p className="how">{s.how}</p>
              <p className="proof">Evidence to show: {s.proof}</p>
            </span>
          </label>
        );
      })}
    </div>
  );
}

function SafePathCard({ sp }: { sp: SafePath }) {
  const n = (d: string[]) => `${d.length} ${d.length === 1 ? "career" : "careers"}`;
  return (
    <div className="card safe" style={{ display: "grid", gap: 14, marginBottom: 16 }}>
      <div>
        <span className="tag green">Safe path</span>
        <h3 className="h3" style={{ marginTop: 8 }}>{sp.headline}</h3>
      </div>
      <div className="two">
        <div className="panel">
          <h4>Most direct</h4>
          <b>{sp.most_direct.subject}</b> <span className="tag">opens {n(sp.most_direct.doors)}</span>
          <div className="tiny" style={{ marginTop: 4 }}>{sp.most_direct.doors.join(" · ")}</div>
        </div>
        <div className="panel" style={{ outline: "2px solid var(--green)" }}>
          <h4>Keeps the most doors open</h4>
          <b>{sp.most_doors.subject}</b> <span className="tag green">opens {n(sp.most_doors.doors)}</span>
          <div className="tiny" style={{ marginTop: 4 }}>{sp.most_doors.doors.join(" · ")}</div>
        </div>
      </div>
      <div>
        <div className="small muted" style={{ marginBottom: 6 }}>Specialise later, without closing doors</div>
        <ol className="small" style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>{sp.how_to_specialise.map((h) => <li key={h}>{h}</li>)}</ol>
      </div>
      <p className="tiny" style={{ margin: 0 }}>{sp.note}</p>
    </div>
  );
}

function Degrees({ plan, nation, selected, onSelect }: { plan: PathPlan; nation: string; selected: DegreeOption | null; onSelect: (s: string) => void }) {
  const [filter, setFilter] = useState<"home" | "all">("home");
  if (!selected) return null;
  const homeCount = selected.universities.filter((u) => u.home).length;
  const mode = filter === "home" && homeCount > 0 ? "home" : "all";
  const unis = selected.universities.filter((u) => mode === "all" || u.home);
  return (
    <>
      <div className="degree-grid">
        {plan.degrees.map((d) => (
          <button key={d.subject} className={`degree ${d.subject === selected.subject ? "on" : ""}`} onClick={() => onSelect(d.subject)} aria-pressed={d.subject === selected.subject}>
            <div>
              <h3 className="h3">{d.subject}</h3>
              <div className="q">{d.qualification}</div>
            </div>
            <p className="small muted" style={{ margin: 0 }}>{d.about}</p>
            <div className="pills">{d.builds.map((b) => <span className="tag" key={b}>{b}</span>)}</div>
            <div className="pills"><span className={`tag ${d.doors.length > 1 ? "green" : ""}`}>Opens {d.doors.length} {d.doors.length === 1 ? "career" : "careers"}</span></div>
          </button>
        ))}
      </div>

      <div className="card" style={{ marginTop: 16, display: "grid", gap: 14 }}>
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap", alignItems: "flex-start" }}>
          <div style={{ minWidth: 0 }}>
            <h3 className="h3">{selected.subject}</h3>
            <p className="small muted" style={{ margin: "4px 0 0" }}><b style={{ color: "var(--text)" }}>Best if:</b> {selected.best_if}</p>
          </div>
          {selected.median_earnings_15m !== null && (
            <div style={{ textAlign: "right", flex: "none" }}>
              <div style={{ fontWeight: 700, fontSize: 19 }}>{money(selected.median_earnings_15m)}</div>
              <div className="tiny">median, 15 months after</div>
            </div>
          )}
        </div>

        <div className="row" style={{ justifyContent: "space-between" }}>
          <h4 className="small" style={{ margin: 0, fontWeight: 600 }}>Where you could study it</h4>
          <div className="seg" role="tablist">
            <button className={mode === "home" ? "on" : ""} onClick={() => setFilter("home")} disabled={homeCount === 0}>{short(nation)} ({homeCount})</button>
            <button className={mode === "all" ? "on" : ""} onClick={() => setFilter("all")}>All UK ({selected.universities.length})</button>
          </div>
        </div>
        <div className="unis">
          {unis.map((u) => (
            <span className={`uni ${u.home ? "home" : ""}`} key={u.name}>
              {u.name}
              <small>{u.kind === "college" ? "College · " : ""}{short(u.nation)}</small>
            </span>
          ))}
        </div>
        <p className="tiny" style={{ margin: 0 }}>
          Examples, not a ranking. Course names and content differ, so compare modules, placements and entry requirements for each. Search “{selected.search}” on{" "}
          {plan.tools.map((t, i) => (
            <span key={t.url}>{i > 0 && " and "}<a href={t.url} target="_blank" rel="noreferrer">{t.name}</a></span>
          ))}
          . Funding: <a href={plan.funding.url} target="_blank" rel="noreferrer">{plan.funding.name}</a>.
        </p>
      </div>
    </>
  );
}

export function Path({ soc, nation, onNation, onBack, backLabel, onAnalysis, onOpen, onCharacter, request, profile }: Props) {
  const [plan, setPlan] = useState<PathPlan | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [route, setRoute] = useState<"university" | "apprenticeship" | null>(null);
  const [degree, setDegree] = useState<string | null>(null);
  const [done, setDone] = usePersistent<string[]>(`cp.path.${soc}`, []);
  const [quest, setQuest] = usePersistent<string[]>(`cp.quest.${soc}`, []);
  const [analysis, setAnalysis] = useState<CareerSummary | null>(null);
  const [field, setField] = useState("");
  const [person, setPerson] = useState("");
  const [uniName, setUniName] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setErr(null);
    api.path(soc, nation).then(
      (p) => {
        setPlan(p);
        setRoute((r) => r ?? p.default_route);
        setDegree((d) => d ?? p.degrees[0]?.subject ?? null);
        setField((f) => f || p.field);
      },
      (e) => setErr(String(e.message ?? e)),
    );
  }, [soc, nation]);

  useEffect(() => {
    setAnalysis(null);
    if (request) api.analyse({ ...request, soc }).then(setAnalysis, () => setAnalysis(null));
  }, [soc, request]);

  const selected = useMemo(() => plan?.degrees.find((d) => d.subject === degree) ?? plan?.degrees[0] ?? null, [plan, degree]);

  const [qIdx, setQIdx] = useState(0);
  const template = useMemo(() => {
    if (!plan) return "";
    const uni = uniName || selected?.universities.find((u) => u.home)?.name || selected?.universities[0]?.name || "[your university]";
    const base = route === "apprenticeship" ? plan.alumni.template_apprenticeship : plan.alumni.template;
    return base
      .replaceAll("{their_name}", person.trim() || "[their first name]")
      .replaceAll("{degree}", selected?.subject ?? "[your degree]")
      .replaceAll("{uni}", uni)
      .replaceAll("{field}", field || plan.field)
      .replaceAll("{question}", plan.alumni.questions[qIdx] ?? plan.alumni.questions[0]);
  }, [plan, selected, uniName, person, field, route, qIdx]);

  const [editedTpl, setEditedTpl] = useState<string | null>(null);
  useEffect(() => setEditedTpl(null), [template]);
  const text = editedTpl ?? template;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch { /* clipboard blocked: the text is selectable */ }
  };

  if (err && !plan) return <main className="page narrow"><div className="notice warn">Couldn't load this path ({err}).</div></main>;
  if (!plan || !route) return <Spinner />;

  const toggle = (k: string) => setDone((d) => (d.includes(k) ? d.filter((x) => x !== k) : [...d, k]));
  const toggleQuest = (k: string) => setQuest((d) => (d.includes(k) ? d.filter((x) => x !== k) : [...d, k]));
  const xp = readXp(soc) + (done.length + quest.length) * XP_PER_TICK;
  const all = [...plan.hard_skills, ...plan.soft_skills];
  const started = all.filter((s) => done.includes(s.skill)).length;
  const timeline = plan.timelines[route];
  const stageDone = timeline.map((t, si) => t.items.every((_, ii) => quest.includes(`${route}:${si}:${ii}`)));
  const activeStage = stageDone.indexOf(false);
  const questTotal = timeline.reduce((n, t) => n + t.items.length, 0);
  const questDone = timeline.reduce((n, t, si) => n + t.items.filter((_, ii) => quest.includes(`${route}:${si}:${ii}`)).length, 0);
  const uniLabel = route === "university";
  const unisForTemplate = selected?.universities ?? [];

  return (
    <main className="page narrow">
      <button className="back no-print" onClick={onBack}>‹ {backLabel}</button>
      <p className="eyebrow">Quest map</p>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <h1 className="title">To {plan.title.toLowerCase()}.</h1>
        <button className="btn soft small no-print" onClick={() => window.print()} style={{ marginTop: 8 }}>Print my plan</button>
      </div>
      <p className="lede">{plan.summary}</p>

      <div className="card hero-strip" style={{ marginTop: 24 }}>
        <Avatar profile={profile} size={52} />
        <div style={{ display: "grid", gap: 6 }}>
          <b>{request ? className(profile) : "No character yet"}</b>
          <XpBar xp={xp} />
        </div>
        <button className="btn soft small no-print" onClick={onCharacter}>{request ? "Character" : "Create yours"}</button>
      </div>

      <div className="card role" style={{ marginTop: 28 }}>
        <span className={`tag ${plan.degree_role.tone}`}>{plan.degree_role.label}</span>
        <p className="small" style={{ margin: 0 }}>{plan.degree_role.note}</p>
      </div>

      <div className="row no-print" style={{ marginTop: 20, justifyContent: "space-between" }}>
        <div className="seg" role="tablist" aria-label="Route">
          {plan.routes.map((r) => (
            <button key={r.id} role="tab" aria-selected={route === r.id} className={route === r.id ? "on" : ""} disabled={!r.available} onClick={() => setRoute(r.id)}>
              {r.label}
            </button>
          ))}
        </div>
        <label className="small row" style={{ gap: 8 }}>
          I live in
          <select className="mini-sel" value={nation} onChange={(e) => onNation(e.target.value)} aria-label="Where you live">
            {NATIONS.map((n) => <option key={n}>{n}</option>)}
          </select>
        </label>
      </div>
      <p className="small muted" style={{ margin: "10px 0 0" }}>{plan.routes.find((r) => r.id === route)?.summary}</p>

      {uniLabel && selected && (
        <section className="sec">
          <h2 className="h2">Choose a degree</h2>
          <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>
            Several subjects lead here. Pick the one that fits how you like to learn, then use it to build the skills below.
          </p>
          {plan.safe_path && <SafePathCard sp={plan.safe_path} />}
          <Degrees plan={plan} nation={nation} selected={selected} onSelect={setDegree} />
        </section>
      )}

      {!uniLabel && plan.apprenticeship && (
        <section className="sec">
          <h2 className="h2">Apprenticeships and college</h2>
          <div className="card" style={{ display: "grid", gap: 14 }}>
            <div>
              <div className="small muted" style={{ marginBottom: 6 }}>Who hires</div>
              <div className="pills">{plan.apprenticeship.employers.map((e) => <span className="tag" key={e}>{e}</span>)}</div>
            </div>
          </div>
          <div className="list" style={{ marginTop: 14 }}>
            {plan.apprenticeship.routes.map((r) => (
              <div className="list-row" key={r.nation + r.type + r.name}>
                <span><span className="tag green">{r.type}</span></span>
                <span>
                  <span style={{ fontWeight: 500 }}>{r.name}</span>
                  <span className="tiny" style={{ display: "block" }}>{r.nation}</span>
                </span>
                <span className="small muted">{r.level}</span>
              </div>
            ))}
          </div>
          <p className="small" style={{ marginTop: 14 }}>
            Find vacancies:{" "}
            {plan.apprenticeship.finders.map((f, i) => (
              <span key={f.url}>{i > 0 && " · "}<a href={f.url} target="_blank" rel="noreferrer">{f.nation === nation ? <b>{f.name}</b> : f.name}</a></span>
            ))}
          </p>
        </section>
      )}

      <section className="sec">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
          <h2 className="h2">Skills matter more than the degree</h2>
          <span className="progress-pill">{started} of {all.length} started · +{XP_PER_TICK} XP each</span>
        </div>
        <p className="muted small" style={{ marginTop: 0, marginBottom: 18 }}>
          {uniLabel ? "Use your degree as a place to build these, not as the thing that gets you hired." : "These are what employers notice, alongside your qualification."}{" "}
          Tick them as you start. Your list stays on this device.
        </p>
        <div className="two" style={{ gridTemplateColumns: "1fr" }}>
          <div>
            <h3 className="h3" style={{ marginBottom: 10 }}>Hard skills</h3>
            <Checklist items={plan.hard_skills} done={done} toggle={toggle} />
          </div>
          <div>
            <h3 className="h3" style={{ margin: "20px 0 10px" }}>Soft skills</h3>
            <Checklist items={plan.soft_skills} done={done} toggle={toggle} />
          </div>
        </div>
      </section>

      <section className="sec">
        <h2 className="h2">Guilds to join</h2>
        <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>{uniLabel ? "Societies and clubs." : "Communities and clubs."} Pick one to start, and one that surprises you.</p>
        <div className="two">
          {plan.societies.map((s) => (
            <div className="card" key={s.name} style={{ padding: 22, display: "grid", gap: 8 }}>
              <h3 className="h3" style={{ fontSize: 18 }}>{s.name}</h3>
              <p className="small muted" style={{ margin: 0 }}>{s.what}</p>
              <div className="pills">{s.builds.map((b) => <span className="tag blue" key={b}>{b}</span>)}</div>
            </div>
          ))}
        </div>
        <p className="tiny" style={{ marginTop: 10 }}>Names differ by {uniLabel ? "university" : "college and region"}: check the {uniLabel ? "students' union" : "college and local employers"} for what exists.</p>
      </section>

      <section className="sec">
        <h2 className="h2">Boss battles</h2>
        <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>Competitions and challenges that put your skills to the test.</p>
        <div className="list">
          {plan.competitions.map((c) => (
            <div className="list-row" key={c.name} style={{ gridTemplateColumns: "1fr" }}>
              <span>
                <span style={{ fontWeight: 600 }}>{c.name}</span>
                <span className="small muted" style={{ display: "block" }}>{c.what}</span>
              </span>
            </div>
          ))}
        </div>
        <p className="tiny" style={{ marginTop: 10 }}>Competitions change every year: check each organiser's website for dates and eligibility.</p>
      </section>

      <section className="sec">
        <h2 className="h2">Side quest: real experience</h2>
        <div className="card">
          <p style={{ margin: 0, fontWeight: 600 }}>{plan.experience[0].toUpperCase() + plan.experience.slice(1)}</p>
          <p className="small muted" style={{ margin: "6px 0 0" }}>{plan.experience_detail}</p>
        </div>
      </section>

      <section className="sec">
        <h2 className="h2">Events</h2>
        <p className="muted small" style={{ marginTop: -8, marginBottom: 16 }}>Things go wrong. See how this career and your backup cope, and split your effort to build a sturdier party.</p>
        {!request ? (
          <div className="notice">Create your character first: events use your own stats.</div>
        ) : !analysis ? (
          <Spinner />
        ) : (
          <Events a={analysis} onOpen={onOpen} />
        )}
      </section>

      <section className="sec">
        <h2 className="h2">Mentors: talk to people who've done it</h2>
        <div className="card" style={{ display: "grid", gap: 18 }}>
          <p style={{ margin: 0 }}>{plan.alumni.why}</p>
          <div className="two">
            <div className="panel">
              <h4>How to find them</h4>
              <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }}>{plan.alumni.find.map((f) => <li key={f}>{f}</li>)}</ul>
            </div>
            <div className="panel">
              <h4>Who to look for</h4>
              <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }}>{plan.alumni.who.map((f) => <li key={f}>{f}</li>)}</ul>
            </div>
          </div>
          <div className="panel">
            <h4>Questions to ask</h4>
            <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }}>{plan.alumni.questions.map((f) => <li key={f}>{f}</li>)}</ul>
          </div>

          <div className="no-print" style={{ display: "grid", gap: 10 }}>
            <h3 className="h3">A message you can send</h3>
            <div className="row">
              <input className="mini-sel" placeholder="Their first name" value={person} onChange={(e) => setPerson(e.target.value)} aria-label="Their first name" style={{ width: 160 }} />
              {uniLabel && unisForTemplate.length > 0 && (
                <select className="mini-sel" value={uniName || unisForTemplate.find((u) => u.home)?.name || unisForTemplate[0].name} onChange={(e) => setUniName(e.target.value)} aria-label="University">
                  {unisForTemplate.map((u) => <option key={u.name}>{u.name}</option>)}
                </select>
              )}
              <input className="mini-sel" value={field} onChange={(e) => setField(e.target.value)} aria-label="Field" style={{ width: 200 }} />
              <select className="mini-sel" value={qIdx} onChange={(e) => setQIdx(Number(e.target.value))} aria-label="Question to ask">
                {plan.alumni.questions.map((q, i) => <option key={q} value={i}>{q.length > 48 ? q.slice(0, 46) + "…" : q}</option>)}
              </select>
            </div>
            <textarea className="tpl" value={text} onChange={(e) => setEditedTpl(e.target.value)} aria-label="Message to an alum" />
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="tiny">Edit it so it sounds like you. Nothing here leaves your device.</span>
              <button className="btn small" onClick={copy}>{copied ? "Copied" : "Copy message"}</button>
            </div>
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }} className="small muted">
            {plan.alumni.tips.map((t) => <li key={t}>{t}</li>)}
          </ul>
        </div>
      </section>

      <section className="sec">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
          <h2 className="h2">Quest log</h2>
          <span className="progress-pill">{questDone} of {questTotal} done · +{XP_PER_TICK} XP each</span>
        </div>
        <p className="muted small" style={{ marginTop: 0, marginBottom: 18 }}>
          Tick a step when you've really done it. XP comes from evidence, never from time spent here.
        </p>
        <ol className="quest">
          {timeline.map((t, si) => {
            const keys = t.items.map((_, ii) => `${route}:${si}:${ii}`);
            const n = keys.filter((k) => quest.includes(k)).length;
            const complete = n === keys.length;
            const active = si === activeStage;
            const C = 2 * Math.PI * 21;
            return (
              <li key={t.stage}>
                <div className={`node ${complete ? "done" : active ? "active" : ""}`} aria-label={`${t.stage}: ${n} of ${keys.length} done`}>
                  {!complete && (
                    <svg viewBox="0 0 48 48" aria-hidden>
                      <circle cx="24" cy="24" r="21" fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - n / keys.length)} opacity={n ? 1 : 0} />
                    </svg>
                  )}
                  {complete ? "✓" : si + 1}
                </div>
                <div className={`quest-body ${active ? "active" : ""}`}>
                  <div className="when">{t.stage}</div>
                  <h4>{t.title}</h4>
                  {t.items.map((item, ii) => {
                    const k = keys[ii];
                    const on = quest.includes(k);
                    return (
                      <label className={`quest-item ${on ? "done" : ""}`} key={k}>
                        <input type="checkbox" checked={on} onChange={() => toggleQuest(k)} />
                        <span>{item}{on && <span className="xp-chip"> +{XP_PER_TICK} XP</span>}</span>
                      </label>
                    );
                  })}
                </div>
              </li>
            );
          })}
        </ol>
      </section>

      <div className="row no-print" style={{ marginTop: 20, justifyContent: "space-between" }}>
        <button className="btn soft" onClick={() => onAnalysis(soc)}>See the full analysis ›</button>
        <span className="tiny" style={{ maxWidth: 420 }}>{plan.demo_note}</span>
      </div>
    </main>
  );
}
