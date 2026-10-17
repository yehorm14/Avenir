import { useEffect, useRef, useState } from "react";
import type { Bootstrap, Career, Page, Preferences } from "./types";
import { api, initial, usePreferences } from "./store";
import { questions, tagsFromAnswers } from "./quiz";
import { Icon, careerIcon } from "./icons";
import { SalaryChart, money, percent } from "./Charts";
import { getCareerContent } from "./content";
import Landing from "./Landing";
import Discovery, { type DiscoveryResult } from "./Discovery";

const pageNames: Record<Page, string> = {
  discover: "Discover",
  conversation: "Your conversation",
  quiz: "Your discovery",
  matches: "Your matches",
  overview: "Overview",
  path: "Your pathway",
  opportunities: "Opportunities",
  guides: "Career guides",
  evidence: "The evidence",
};
const nav: { id: Page; icon: string }[] = [
  { id: "overview", icon: "home" },
  { id: "matches", icon: "compass" },
  { id: "path", icon: "path" },
  { id: "opportunities", icon: "calendar" },
  { id: "guides", icon: "chat" },
];
const route = (): Page => {
  const p = window.location.hash.replace("#/", "").split("/")[0];
  return Object.prototype.hasOwnProperty.call(pageNames, p)
    ? (p as Page)
    : "discover";
};
const value = (c: Career, key: string) => {
  const m = c.metrics[key];
  return !m || m.status === "pending" || m.flags?.includes("suppressed")
    ? null
    : m.value;
};
const guideNames: Record<string, { name: string; role: string }> = {
  building: { name: "Alex", role: "Engineering & the built world" },
  engineering: { name: "Alex", role: "Engineering & the built world" },
  technology: { name: "Sam", role: "Technology & digital careers" },
  finance: { name: "Jamie", role: "Finance & business" },
  health: { name: "Maya", role: "Healthcare & people" },
};
const specialistNames: Record<string, string> = {
  "2134": "Sam",
  "3544": "Nora",
  "2133": "Taylor",
  "2135": "Kai",
  "2141": "Ada",
  "2142": "Riley",
  "2451": "Alex",
  "2452": "Morgan",
  "3120": "Theo",
  "2121": "Alex",
  "2123": "Ellis",
  "3113": "Max",
  "2453": "Jordan",
  "2454": "Casey",
  "2433": "Robin",
  "2422": "Jamie",
  "2421": "Charlie",
  "2254": "Maya",
  "5241": "Eli",
  "2313": "Sophie",
};
function guideFor(c: Career) {
  const icon = careerIcon(c.soc);
  const group =
    guideNames[
      ["building", "bolt", "compass"].includes(icon)
        ? "building"
        : ["money", "chart"].includes(icon)
          ? "finance"
          : icon === "heart" || icon === "book"
            ? "health"
            : "technology"
    ];
  return { ...group, name: specialistNames[c.soc] ?? group.name };
}
function CareerMark({
  career,
  large = false,
}: {
  career: Career;
  large?: boolean;
}) {
  return (
    <span
      className={`career-mark ${large ? "large" : ""} tone-${careerIcon(career.soc)}`}
    >
      <Icon name={careerIcon(career.soc)} size={large ? 30 : 23} />
    </span>
  );
}
function External({
  href,
  children,
  className = "",
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <a className={className} href={href} target="_blank" rel="noreferrer">
      {children}
      <Icon name="external" size={14} />
    </a>
  );
}

export default function App() {
  const [prefs, setPrefs] = usePreferences();
  const [page, setPage] = useState<Page>(route);
  const [data, setData] = useState<Bootstrap | null>(null);
  const [loadError, setLoadError] = useState("");
  const [reload, setReload] = useState(0);
  const [matches, setMatches] = useState<Career[]>([]);
  const [ranking, setRanking] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [settings, setSettings] = useState(false);
  const [toast, setToast] = useState("");
  const [inspect, setInspect] = useState<Career | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const go = (p: Page) => {
    setPage(p);
    window.location.hash = `/${p}`;
    window.scrollTo(0, 0);
    setTimeout(() => mainRef.current?.focus({ preventScroll: true }), 0);
  };
  useEffect(() => {
    const fn = () => {
      setPage(route());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", fn);
    return () => window.removeEventListener("hashchange", fn);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoadError("");
    api<Bootstrap>("bootstrap", undefined, controller.signal)
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") setLoadError(e.message);
      });
    return () => controller.abort();
  }, [reload]);
  useEffect(() => {
    if (!prefs.completed || !data) return;
    const controller = new AbortController();
    setRanking(true);
    setMatchError("");
    const id = setTimeout(
      () =>
        api<{ results: Career[] }>(
          "matches",
          {
            tags: prefs.discovery?.tags ?? tagsFromAnswers(prefs.answers),
            weights: prefs.weights,
          },
          controller.signal,
        )
          .then((r) => {
            const reference =
              prefs.discovery?.referenceSoc ?? prefs.discovery?.targetSoc;
            const ordered = reference
              ? [
                  ...r.results.filter((c) => c.soc === reference),
                  ...r.results.filter((c) => c.soc !== reference),
                ]
              : r.results;
            setMatches(ordered);
            setRanking(false);
          })
          .catch((e) => {
            if (e.name !== "AbortError") {
              setMatchError(e.message);
              setRanking(false);
            }
          }),
      130,
    );
    return () => {
      clearTimeout(id);
      controller.abort();
    };
  }, [
    prefs.completed,
    prefs.answers,
    prefs.discovery?.tags,
    prefs.discovery?.targetSoc,
    prefs.discovery?.referenceSoc,
    prefs.weights,
    data,
    reload,
  ]);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(id);
  }, [toast]);
  const update = (change: Partial<Preferences>) =>
    setPrefs((p) => ({ ...p, ...change }));
  const careers = data?.careers ?? [];
  const selected = prefs.selected
    .map(
      (id) =>
        matches.find((c) => c.soc === id) ?? careers.find((c) => c.soc === id),
    )
    .filter((c): c is Career => !!c);
  const primary = selected[0];
  const topCareers = matches.slice(0, 3);
  const choose = (c: Career) => {
    if (prefs.selected.includes(c.soc)) {
      update({ selected: prefs.selected.filter((id) => id !== c.soc) });
      return;
    }
    if (prefs.selected.length >= 3) {
      setToast("Your three choices are full. Remove one to choose another.");
      return;
    }
    update({ selected: [...prefs.selected, c.soc] });
    setToast(`${c.title} added as choice ${prefs.selected.length + 1}.`);
  };
  const start = (mode: "known" | "explore" = "explore") => {
    const existing = prefs.discovery;
    update({
      discovery:
        existing?.mode === mode ? existing : { mode, answers: {}, step: 0 },
    });
    go("conversation");
  };
  const finish = () => {
    update({ completed: true, step: questions.length });
    go("matches");
  };
  const retake = () => {
    update({ discovery: { mode: "explore", answers: {}, step: 0 } });
    go("conversation");
    setSettings(false);
  };
  const completeDiscovery = (result: DiscoveryResult) => {
    setPrefs((p) => ({
      ...p,
      completed: true,
      selected: [],
      answers: {},
      weights: result.weights,
      discovery: {
        mode: p.discovery?.mode ?? "explore",
        answers: p.discovery?.answers ?? {},
        step: p.discovery?.step ?? 0,
        tags: result.tags,
        targetSoc: result.target_soc,
        referenceSoc: result.reference_soc,
        summary: result.profile_summary,
        notices: result.notices,
      },
    }));
    setMatches(result.results);
    go("matches");
  };
  const showShell =
    prefs.completed && !["discover", "quiz", "conversation"].includes(page);
  const exportPlan = () => {
    if (!primary) return;
    const content = getCareerContent(primary.soc, primary.family);
    const body = `# My Aventier career plan\n\n${selected.map((c, i) => `${i + 1}. ${c.title}`).join("\n")}\n\n## First choice: ${primary.title}\n\n${content.intro}\n\n## Route to explore\n${content.broadDegree}\n${content.whyBroad}\n\n## First steps\n${content.firstSteps.map((s) => `- ${s}`).join("\n")}\n\n## Universities to explore\n${content.universities.map((u) => `- ${u.name}: ${u.course} — ${u.url}`).join("\n")}\n\n## Opportunity organisers\n${content.opportunities.map((o) => `- ${o.title}: ${o.url}`).join("\n")}\n\n## Evidence\n2025 median full-time employee pay: ${money(value(primary, "pay_median"))}. ONS ASHE; preliminary. Pay is not a starting salary. Preliminary interest matching; guidance is exploratory, not a validated psychological test. Course and event availability must be checked at source.\n`;
    const url = URL.createObjectURL(
      new Blob([body], { type: "text/markdown" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "my-aventier-plan.md";
    a.click();
    URL.revokeObjectURL(url);
    setToast("Your career plan has been downloaded.");
  };
  const empty = (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon name="compass" size={38} />
      </span>
      <h2>A little discovery comes first.</h2>
      <p>
        Tell us what draws you in. We'll help you find careers worth exploring.
      </p>
      <button className="button primary" onClick={() => start()}>
        Start your discovery <Icon name="arrow" />
      </button>
    </div>
  );
  return (
    <div className={showShell ? "app with-top-nav" : "app"}>
      <a
        href="#main"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          mainRef.current?.focus({ preventScroll: true });
        }}
      >
        Skip to content
      </a>
      <header className="topbar">
        {showShell ? (
          <nav className="workspace-nav" aria-label="Main navigation">
            <button onClick={() => go("discover")}>Home</button>
            {[...nav, { id: "evidence" as const, icon: "chart" }].map((n) => (
              <button
                key={n.id}
                onClick={() => go(n.id)}
                aria-current={page === n.id ? "page" : undefined}
                className={page === n.id ? "active" : ""}
              >
                <Icon name={n.icon} size={17} />
                {pageNames[n.id]}
                {n.id === "matches" && <span className="nav-count">3</span>}
              </button>
            ))}
          </nav>
        ) : (
          <nav className="top-links" aria-label="Main navigation">
            <button onClick={() => go("discover")}>Home</button>
          </nav>
        )}
        <div className="top-actions">
          <span className="private-note">
            <Icon name="lock" size={13} /> Private to this device
          </span>
          <button
            className="profile-button"
            aria-label="Your preferences"
            aria-expanded={settings}
            onClick={() => setSettings(!settings)}
          >
            You
          </button>
        </div>
        {settings && (
          <div className="settings-popover">
            <b>Your preferences</b>
            <label>
              Home city
              <input
                value={prefs.location}
                maxLength={60}
                onChange={(e) => update({ location: e.target.value })}
              />
            </label>
            <label>
              Home nation
              <select
                value={prefs.nation}
                onChange={(e) => update({ nation: e.target.value })}
              >
                {["Scotland", "England", "Wales", "Northern Ireland"].map(
                  (n) => (
                    <option key={n}>{n}</option>
                  ),
                )}
              </select>
            </label>
            <p>Progress is saved in this browser. No account needed.</p>
            <button onClick={retake}>Start a new conversation</button>
            <button
              onClick={() => {
                setPrefs(initial);
                setMatches([]);
                setSettings(false);
                go("discover");
                setToast("Your local progress has been cleared.");
              }}
            >
              Clear my local progress
            </button>
            <button className="text-button" onClick={() => setSettings(false)}>
              Close preferences
            </button>
          </div>
        )}
      </header>
      <main
        id="main"
        ref={mainRef}
        tabIndex={-1}
        className={`main-content ${showShell ? "workspace" : ""}`}
      >
        {loadError ? (
          <div className="empty-state" role="alert">
            <Icon name="info" size={36} />
            <h2>Let's reconnect.</h2>
            <p>{loadError}</p>
            <button
              className="button primary"
              onClick={() => setReload((r) => r + 1)}
            >
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="loading-state">
            <span className="spinner" />
            <p>Getting your workspace ready…</p>
          </div>
        ) : (
          <>
            {page === "discover" && <Landing onChoose={start} />}
            {page === "conversation" && (
              <Discovery
                mode={prefs.discovery?.mode ?? "explore"}
                careers={careers}
                draft={{
                  answers: prefs.discovery?.answers ?? {},
                  step: prefs.discovery?.step ?? 0,
                }}
                onDraft={(draft) =>
                  update({
                    discovery: {
                      ...prefs.discovery,
                      mode: prefs.discovery?.mode ?? "explore",
                      ...draft,
                    },
                  })
                }
                onComplete={completeDiscovery}
                onBack={() => go("discover")}
              />
            )}
            {page === "quiz" && (
              <Quiz prefs={prefs} update={update} finish={finish} go={go} />
            )}
            {page === "matches" &&
              (prefs.completed ? (
                <>
                  <PageHeading
                    label="Your matches"
                    title="Three careers to explore."
                    description="Three careers connected to what you shared. Explore the work, compare your priorities, and choose your first, second, and third."
                  />
                  {prefs.discovery?.summary && (
                    <section className="discovery-result-summary">
                      <Icon name="chat" size={22} />
                      <div>
                        <h2>A starting point from our conversation.</h2>
                        <p>{prefs.discovery.summary}</p>
                        {prefs.discovery.notices?.map((n) => (
                          <p className="fine-print" key={n}>
                            {n.startsWith("Development split")
                              ? "Interest matching is preliminary. Treat these as starting points to explore, not a verdict about you."
                              : n}
                          </p>
                        ))}
                      </div>
                      <button
                        className="text-button"
                        onClick={() => go("conversation")}
                      >
                        Edit your answers
                      </button>
                    </section>
                  )}
                  <div className="results-layout">
                    <section className="match-list" aria-busy={ranking}>
                      <div className="list-toolbar">
                        <span>
                          {ranking
                            ? "Balancing your priorities…"
                            : "Your three careers"}
                        </span>
                        <span className="subtle-badge">
                          {data.data_status.fit === "mock"
                            ? "Sample interest matching"
                            : "Preliminary interest model"}
                        </span>
                      </div>
                      {matchError && (
                        <div className="inline-error" role="alert">
                          {matchError}
                          <button onClick={() => setReload((r) => r + 1)}>
                            Try again
                          </button>
                        </div>
                      )}
                      {!matches.length && ranking ? (
                        <div className="loading-state">
                          <span className="spinner" />
                          Finding your directions…
                        </div>
                      ) : (
                        topCareers.map((c, i) => (
                          <article
                            key={c.soc}
                            className={`match-row ${prefs.selected.includes(c.soc) ? "chosen" : ""}`}
                          >
                            <div className="match-row-heading">
                              <CareerMark career={c} />
                              <div className="match-title">
                                <span className="tiny">
                                  {c.sector || "Career to explore"}
                                </span>
                                <button onClick={() => setInspect(c)}>
                                  <h3>{c.title}</h3>
                                </button>
                              </div>
                              <span className="fit-score">
                                {Math.round(c.fit ?? 0)}
                                <small>interest index</small>
                              </span>
                            </div>
                            <p className="match-summary">
                              {getCareerContent(c.soc, c.family).intro}
                            </p>
                            <div className="match-stats">
                              <div>
                                <span>Median annual pay</span>
                                <b>{money(value(c, "pay_median"))}</b>
                              </div>
                              <div>
                                <span>Employment trend</span>
                                <b
                                  className={
                                    (value(c, "demand_trend") ?? 0) >= 0
                                      ? "green"
                                      : ""
                                  }
                                >
                                  {percent(value(c, "demand_trend"))}
                                  <small> / year</small>
                                </b>
                              </div>
                              <div>
                                <span>Your balance</span>
                                <div className="score-bar">
                                  <i
                                    style={{
                                      width: `${Math.max(0, Math.min(100, c.score ?? 0))}%`,
                                    }}
                                  />
                                </div>
                                <b>
                                  {Math.round(c.score ?? 0)}
                                  <small> / 100</small>
                                </b>
                              </div>
                            </div>
                            <div className="match-row-footer">
                              <button
                                className="text-button"
                                onClick={() => setInspect(c)}
                              >
                                Why this could fit{" "}
                                <Icon name="chevron" size={14} />
                              </button>
                              <button
                                className={`button ${prefs.selected.includes(c.soc) ? "selected-button" : "secondary"}`}
                                aria-label={`${prefs.selected.includes(c.soc) ? "Remove" : "Choose"} ${c.title}`}
                                aria-pressed={prefs.selected.includes(c.soc)}
                                onClick={() => choose(c)}
                                disabled={
                                  !prefs.selected.includes(c.soc) &&
                                  prefs.selected.length >= 3
                                }
                              >
                                {prefs.selected.includes(c.soc) ? (
                                  <>
                                    <Icon name="check" size={16} /> Choice{" "}
                                    {prefs.selected.indexOf(c.soc) + 1}
                                  </>
                                ) : (
                                  <>
                                    Choose <Icon name="plus" size={16} />
                                  </>
                                )}
                              </button>
                            </div>
                            {i === 0 && (
                              <span className="sr-only">
                                Highest overall score for your current
                                priorities.
                              </span>
                            )}
                          </article>
                        ))
                      )}
                      <p className="fine-print">
                        Pay and employment: ONS ASHE, UK, 2025 / 2021–2025.
                        Preliminary, full-time employees only. The pay range and
                        all evidence are available under “Why this could fit”.
                        Scores are comparison indices, not probabilities.
                      </p>
                    </section>
                    <aside className="priorities-panel">
                      <section className="priorities">
                        <div className="section-title">
                          <h3>What matters to you?</h3>
                          <Icon name="compass" size={20} />
                        </div>
                        <p>There isn't one right balance.</p>
                        {(
                          [
                            {
                              key: "pay",
                              label: "Pay",
                              detail: "The earning potential of the career",
                              icon: "money",
                            },
                            {
                              key: "interest",
                              label: "Interest",
                              detail: "How closely it fits your answers",
                              icon: "heart",
                            },
                            {
                              key: "need",
                              label: "Expected need",
                              detail: "A signal from recent employment trends",
                              icon: "chart",
                            },
                          ] as const
                        ).map((w) => (
                          <label className="weight-control" key={w.key}>
                            <span>
                              <Icon name={w.icon} size={17} />
                              <b>{w.label}</b>
                              <output>
                                {Object.values(prefs.weights).every(
                                  (v) => v === 0,
                                )
                                  ? 33
                                  : Math.round(
                                      (prefs.weights[w.key] /
                                        Object.values(prefs.weights).reduce(
                                          (a, b) => a + b,
                                          0,
                                        )) *
                                        100,
                                    )}
                                %
                              </output>
                            </span>
                            <input
                              aria-label={`${w.label} weight`}
                              type="range"
                              min="0"
                              max="100"
                              step="5"
                              value={prefs.weights[w.key]}
                              onChange={(e) =>
                                update({
                                  weights: {
                                    ...prefs.weights,
                                    [w.key]: Number(e.target.value),
                                  },
                                })
                              }
                              style={
                                {
                                  "--range": `${prefs.weights[w.key]}%`,
                                } as React.CSSProperties
                              }
                            />
                            <small>{w.detail}</small>
                          </label>
                        ))}
                        <p className="fine-print">
                          Need reflects a historical research signal, not an LLM
                          prediction or a guarantee of future jobs. Weights are
                          normalised; all zero uses equal weights.
                        </p>
                        <button
                          className="text-button muted"
                          onClick={() => update({ weights: initial.weights })}
                        >
                          <Icon name="refresh" size={14} /> Reset balance
                        </button>
                      </section>
                      <section className="shortlist">
                        <h3>Your three directions</h3>
                        <p>The first choice becomes your main plan.</p>
                        {[0, 1, 2].map((i) => (
                          <div
                            className={`shortlist-slot ${selected[i] ? "filled" : ""}`}
                            key={i}
                          >
                            <span className="rank-number">{i + 1}</span>
                            {selected[i] ? (
                              <>
                                <span>{selected[i].title}</span>
                                <div className="rank-controls">
                                  {i > 0 && (
                                    <button
                                      aria-label={`Move ${selected[i].title} up`}
                                      onClick={() => {
                                        const next = [...prefs.selected];
                                        [next[i], next[i - 1]] = [
                                          next[i - 1],
                                          next[i],
                                        ];
                                        update({ selected: next });
                                      }}
                                    >
                                      <Icon name="up" size={14} />
                                    </button>
                                  )}
                                  <button
                                    aria-label={`Remove ${selected[i].title} from shortlist`}
                                    onClick={() => choose(selected[i])}
                                  >
                                    <Icon name="close" size={14} />
                                  </button>
                                </div>
                              </>
                            ) : (
                              <span className="muted">
                                {
                                  [
                                    "Your first choice",
                                    "A second possibility",
                                    "Keep a third door open",
                                  ][i]
                                }
                              </span>
                            )}
                          </div>
                        ))}
                        <button
                          className="button primary full-width"
                          disabled={selected.length !== 3 || ranking}
                          onClick={() => go("path")}
                        >
                          Build my pathway <Icon name="arrow" size={17} />
                        </button>
                        <small className="shortlist-note">
                          {selected.length === 3
                            ? "Your choices can change. Your plan grows with you."
                            : `Choose ${3 - selected.length} more ${selected.length === 2 ? "career" : "careers"} to continue.`}
                        </small>
                      </section>
                    </aside>
                  </div>
                </>
              ) : (
                empty
              ))}
            {page === "overview" &&
              (primary ? (
                <>
                  <PageHeading
                    label="Your workspace"
                    title="Your career plan."
                    description="Your interests are a starting point. A little action will tell you much more."
                  />
                  <div className="overview-grid">
                    <section className="main-pick">
                      <div className="eyebrow-line">
                        <span>
                          <span className="status-dot" /> Your first choice
                        </span>
                        <span className="subtle-badge">Personal plan</span>
                      </div>
                      <CareerMark career={primary} large />
                      <h2>{primary.title}</h2>
                      <p>
                        {getCareerContent(primary.soc, primary.family).intro}
                      </p>
                      <button
                        className="button primary"
                        onClick={() => go("path")}
                      >
                        Explore your pathway <Icon name="arrow" size={17} />
                      </button>
                      <div className="pick-stat">
                        <span>UK median annual pay</span>
                        <b>{money(value(primary, "pay_median"))}</b>
                        <small>
                          ONS ASHE 2025 · Preliminary · Full-time employees
                        </small>
                      </div>
                    </section>
                    <section className="next-step-card">
                      <span className="round-icon">
                        <Icon name="leaf" size={22} />
                      </span>
                      <h3>
                        Big futures.
                        <br />
                        Small next steps.
                      </h3>
                      <p>Start with something you can actually do this week.</p>
                      {getCareerContent(primary.soc, primary.family)
                        .firstSteps.slice(0, 3)
                        .map((s, i) => (
                          <label className="task-check" key={s}>
                            <input
                              type="checkbox"
                              checked={prefs.checked.includes(
                                `${primary.soc}-${i}`,
                              )}
                              onChange={() =>
                                update({
                                  checked: prefs.checked.includes(
                                    `${primary.soc}-${i}`,
                                  )
                                    ? prefs.checked.filter(
                                        (k) => k !== `${primary.soc}-${i}`,
                                      )
                                    : [...prefs.checked, `${primary.soc}-${i}`],
                                })
                              }
                            />
                            <span>{s}</span>
                          </label>
                        ))}
                      <span className="tiny green">
                        {
                          prefs.checked.filter((k) =>
                            k.startsWith(`${primary.soc}-`),
                          ).length
                        }{" "}
                        of 3 steps explored
                      </span>
                    </section>
                  </div>
                  <section className="alternatives">
                    <div className="section-header">
                      <h3>Keep your other doors open.</h3>
                      <button
                        className="text-button"
                        onClick={() => go("matches")}
                      >
                        Revisit your choices <Icon name="chevron" size={15} />
                      </button>
                    </div>
                    <div className="alternative-list">
                      {selected.slice(1).map((c, i) => (
                        <button key={c.soc} onClick={() => setInspect(c)}>
                          <span className="tiny">Choice {i + 2}</span>
                          <CareerMark career={c} />
                          <div>
                            <b>{c.title}</b>
                            <span>
                              {money(value(c, "pay_median"))} median annual pay
                            </span>
                          </div>
                          <Icon name="chevron" size={17} />
                        </button>
                      ))}
                    </div>
                  </section>
                  <SalaryChart careers={selected} />
                </>
              ) : prefs.completed ? (
                <>
                  <NeedChoices go={go} />
                </>
              ) : (
                empty
              ))}
            {page === "path" &&
              (primary ? (
                <Pathway
                  career={primary}
                  nation={prefs.nation}
                  onExport={exportPlan}
                  onOpportunities={() => go("opportunities")}
                  onGuide={() => go("guides")}
                />
              ) : (
                <NeedChoices go={go} />
              ))}
            {page === "opportunities" &&
              (primary ? (
                <Opportunities
                  careers={selected}
                  prefs={prefs}
                  update={update}
                  notify={setToast}
                />
              ) : (
                <NeedChoices go={go} />
              ))}
            {page === "guides" &&
              (primary ? (
                <Guides careers={selected} />
              ) : (
                <NeedChoices go={go} />
              ))}
            {page === "evidence" && (
              <Evidence
                data={data}
                selected={
                  selected.length
                    ? selected
                    : careers.filter((c) =>
                        ["2134", "2121", "2451"].includes(c.soc),
                      )
                }
              />
            )}
          </>
        )}
      </main>
      {!showShell && (
        <footer className="site-footer">
          <button onClick={() => go("evidence")}>
            Research <Icon name="external" size={12} />
          </button>
          <span>© 2026 Aventier</span>
        </footer>
      )}
      {toast && (
        <div role="status" className="toast">
          <Icon name="check" size={17} />
          {toast}
        </div>
      )}
      {inspect && (
        <div className="modal-backdrop" onClick={() => setInspect(null)}>
          <section
            className="detail-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="career-title"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Escape") setInspect(null);
              if (e.key === "Tab") {
                const all = e.currentTarget.querySelectorAll<HTMLElement>(
                  'button:not([disabled]),a[href],input,summary,[tabindex="0"]',
                );
                const first = all[0],
                  last = all[all.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                  e.preventDefault();
                  last?.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                  e.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <button
              autoFocus
              className="icon-button modal-close"
              onClick={() => setInspect(null)}
              aria-label="Close career details"
            >
              <Icon name="close" />
            </button>
            <CareerMark career={inspect} large />
            <h2 id="career-title">{inspect.title}</h2>
            <p>{getCareerContent(inspect.soc, inspect.family).intro}</p>
            <h3>Why it is worth exploring</h3>
            <ul className="plain-list">
              {(inspect.reasons?.length
                ? inspect.reasons
                : getCareerContent(inspect.soc, inspect.family).dayToDay
              ).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
            <div className="evidence-metrics">
              <MetricDetail
                career={inspect}
                metricKey="pay_median"
                label="Annual pay, middle 50%"
              />
              <MetricDetail
                career={inspect}
                metricKey="demand_trend"
                label="Employment trend, 2021–2025"
              />
              <MetricDetail
                career={inspect}
                metricKey="exposure"
                label="Automation exposure (research estimate)"
              />
            </div>
            <SalaryChart careers={[inspect]} compact />
            <button
              className="button primary"
              disabled={
                !prefs.selected.includes(inspect.soc) &&
                prefs.selected.length >= 3
              }
              onClick={() => {
                choose(inspect);
                setInspect(null);
              }}
            >
              {prefs.selected.includes(inspect.soc)
                ? "Remove from my choices"
                : "Add to my choices"}
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

function PageHeading({
  label,
  title,
  description,
  action,
}: {
  label: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="page-context">{label}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action}
    </header>
  );
}
function NeedChoices({ go }: { go: (p: Page) => void }) {
  return (
    <div className="empty-state">
      <Icon name="path" size={40} />
      <h2>Give your future a starting point.</h2>
      <p>
        Rank three career matches to build your pathway, meet your guide, and
        discover relevant opportunities.
      </p>
      <button className="button primary" onClick={() => go("matches")}>
        Choose your careers <Icon name="arrow" />
      </button>
    </div>
  );
}

function Quiz({
  prefs,
  update,
  finish,
  go,
}: {
  prefs: Preferences;
  update: (p: Partial<Preferences>) => void;
  finish: () => void;
  go: (p: Page) => void;
}) {
  const step = Math.min(prefs.step, questions.length),
    q = questions[step];
  const answered = q ? prefs.answers[q.id] : undefined;
  if (!q)
    return (
      <section className="quiz-container quiz-location">
        <div className="quiz-progress">
          <span>One last thing</span>
          <span>8 of 8 answered</span>
        </div>
        <div className="progress-track">
          <i style={{ width: "100%" }} />
        </div>
        <span className="quiz-theme">Make it relevant to you</span>
        <h1>
          Where does your
          <br />
          next chapter begin?
        </h1>
        <p className="quiz-hint">
          We'll use your home nation for study routes and local opportunities.
          Your matches stay UK-wide.
        </p>
        <label className="form-label">
          Home city
          <input
            value={prefs.location}
            placeholder="e.g. Glasgow"
            maxLength={60}
            onChange={(e) => update({ location: e.target.value })}
          />
        </label>
        <label className="form-label">
          Home nation
          <select
            value={prefs.nation}
            onChange={(e) => update({ nation: e.target.value })}
          >
            {["Scotland", "England", "Wales", "Northern Ireland"].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <div className="quiz-footer">
          <button
            className="text-button"
            onClick={() => update({ step: questions.length - 1 })}
          >
            <Icon name="back" size={17} /> Back
          </button>
          <button className="button primary" onClick={finish}>
            Find my three directions <Icon name="arrow" size={17} />
          </button>
        </div>
        <p className="fine-print">
          Your answers stay in this browser. The quiz draws on work-interest
          psychology; it is an exploration tool, not a validated psychological
          assessment.
        </p>
      </section>
    );
  return (
    <section className="quiz-container" key={q.id}>
      <div className="quiz-progress">
        <button
          className="text-button"
          onClick={() => (step ? update({ step: step - 1 }) : go("discover"))}
        >
          <Icon name="back" size={16} />{" "}
          {step ? "Previous question" : "Back to discovery"}
        </button>
        <span>
          Question {step + 1} of {questions.length}
        </span>
      </div>
      <div className="progress-track">
        <i style={{ width: `${((step + 1) / questions.length) * 100}%` }} />
      </div>
      <span className="quiz-theme">{q.theme}</span>
      <h1>{q.title}</h1>
      <p className="quiz-hint">{q.hint}</p>
      <div className="quiz-options" role="radiogroup" aria-label={q.title}>
        {q.options.map((o, i) => (
          <button
            role="radio"
            aria-checked={answered === i}
            key={o.text}
            className={`quiz-option ${answered === i ? "is-selected" : ""}`}
            onClick={() => update({ answers: { ...prefs.answers, [q.id]: i } })}
            onKeyDown={(e) => {
              if (
                ["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(
                  e.key,
                )
              ) {
                e.preventDefault();
                const next =
                  (i +
                    (e.key === "ArrowUp" || e.key === "ArrowLeft" ? -1 : 1) +
                    4) %
                  4;
                update({ answers: { ...prefs.answers, [q.id]: next } });
                (
                  e.currentTarget.parentElement?.children[next] as HTMLElement
                )?.focus();
              }
            }}
          >
            <span className="option-letter">{String.fromCharCode(65 + i)}</span>
            <span>
              <b>{o.text}</b>
              <small>{o.detail}</small>
            </span>
            <span className="radio-circle">
              {answered === i && <Icon name="check" size={14} />}
            </span>
          </button>
        ))}
      </div>
      <div className="quiz-footer">
        <span className="muted">
          <Icon name="lock" size={14} /> No right or wrong answers
        </span>
        <button
          className="button primary"
          disabled={answered === undefined}
          onClick={() => update({ step: step + 1 })}
        >
          {step === questions.length - 1 ? "A final detail" : "Continue"}
          <Icon name="arrow" size={18} />
        </button>
      </div>
    </section>
  );
}

function RelatedCareers({ career }: { career: Career }) {
  const related = career.hedges?.slice(0, 2) ?? [];
  if (!related.length) return null;
  return (
    <section className="related-careers">
      <h3>Skills that open another door.</h3>
      <p>Related careers can give you another way forward.</p>
      {related.map((h) => (
        <article key={h.soc2020}>
          <Icon name="path" size={18} />
          <div>
            <b>{h.title}</b>
            <p>
              {h.shared_skills.length
                ? `Shared skills: ${h.shared_skills.slice(0, 3).join(", ")}.`
                : "Skill detail is not available in this snapshot."}
            </p>
            <small>
              {h.status} skill-overlap evidence
              {h.evidence === "estimate"
                ? " · estimated occupation mapping"
                : ""}
            </small>
          </div>
        </article>
      ))}
      <small>Skill overlap is not a guarantee of lower career risk.</small>
    </section>
  );
}

function MetricDetail({
  career,
  metricKey,
  label,
}: {
  career: Career;
  metricKey: string;
  label: string;
}) {
  const m = career.metrics[metricKey],
    v = value(career, metricKey);
  return (
    <div className="metric-detail">
      <span>{label}</span>
      <b>
        {v === null
          ? "Not available"
          : metricKey === "pay_median"
            ? m.low != null && m.high != null
              ? `${money(m.low)} – ${money(m.high)}`
              : money(v)
            : metricKey === "exposure"
              ? `${(v * 100).toFixed(0)} / 100`
              : percent(v)}
      </b>
      <small>
        {m
          ? `${m.source} · ${m.as_of} · ${m.status} · ${m.confidence} confidence`
          : "Not included in this snapshot"}
      </small>
      {metricKey === "pay_median" && (
        <p>
          Middle half of full-time employees; excludes self-employed workers.
          This is not a starting salary. 2025 figures are provisional.
        </p>
      )}
      {metricKey === "exposure" && (
        <p>
          Task exposure is not a probability of job loss.
          {m?.flags?.includes("multi_isco")
            ? " Multiple international occupation codes are mapped to this UK group."
            : ""}
          {m?.low != null && m.high != null
            ? ` Research range: ${Math.round(m.low * 100)}–${Math.round(m.high * 100)} / 100.`
            : ""}
          {m?.flags?.includes("sources_disagree")
            ? " Research sources disagree; treat the estimate cautiously."
            : ""}
        </p>
      )}
      {metricKey === "demand_trend" && (
        <p>
          Historical annual employee-job growth.{" "}
          {m?.low != null && m.high != null
            ? `Range: ${percent(m.low)} to ${percent(m.high)}. `
            : ""}
          Full-time employees only. Not a forecast of vacancies.
        </p>
      )}
    </div>
  );
}

type Plan = {
  timelines?: Record<
    string,
    { stage: string; title: string; items: string[] }[]
  >;
  safe_path?: { headline: string; how_to_specialise: string[] };
  related_pathway_soc?: string;
  alumni?: {
    why: string;
    find: string[];
    who: string[];
    tips: string[];
    questions: string[];
    template: string;
    template_apprenticeship: string;
  };
  degree_role?: { note: string };
  demo_note?: string;
};
function Pathway({
  career,
  nation,
  onExport,
  onOpportunities,
  onGuide,
}: {
  career: Career;
  nation: string;
  onExport: () => void;
  onOpportunities: () => void;
  onGuide: () => void;
}) {
  const content = getCareerContent(career.soc, career.family);
  const [tab, setTab] = useState("plan");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [routeType, setRouteType] = useState("university");
  const [planError, setPlanError] = useState("");
  useEffect(() => {
    const c = new AbortController();
    setPlan(null);
    setPlanError("");
    api<Plan>(
      `path/${career.soc}?nation=${encodeURIComponent(nation)}`,
      undefined,
      c.signal,
    )
      .then(setPlan)
      .catch((e) => {
        if (e.name !== "AbortError") setPlanError(e.message);
      });
    return () => c.abort();
  }, [career.soc, nation]);
  const timelines = plan?.related_pathway_soc
    ? []
    : (plan?.timelines?.[routeType] ?? []);
  return (
    <>
      <PageHeading
        label="Your first choice, brought to life"
        title={`Your ${career.title.toLowerCase()} pathway.`}
        description="The big picture, a few open doors, and practical steps to make it yours."
        action={
          <button className="button secondary" onClick={onExport}>
            <Icon name="download" size={16} /> Save my plan
          </button>
        }
      />
      <div className="path-hero">
        <CareerMark career={career} large />
        <div>
          <span className="tiny">Your first choice</span>
          <h2>{career.title}</h2>
          <p>{content.intro}</p>
        </div>
        <div className="path-pay">
          <b>{money(value(career, "pay_median"))}</b>
          <span>UK median annual pay</span>
          <small>ONS ASHE 2025 · Preliminary</small>
        </div>
      </div>
      <nav className="content-tabs" aria-label="Pathway sections">
        {[
          ["plan", "Your route"],
          ["skills", "Skills to build"],
          ["study", "Universities & study"],
          ["reality", "The real picture"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={tab === id ? "active" : ""}
            aria-current={tab === id ? "page" : undefined}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>
      {tab === "plan" && (
        <>
          <div className="path-layout">
            <section>
              <div className="section-header">
                <h2>Make space for possibility.</h2>
              </div>
              <div className="broad-degree">
                <Icon name="book" size={24} />
                <div>
                  <span className="tiny">A route worth exploring</span>
                  <h3>{content.broadDegree}</h3>
                  <p>{content.whyBroad}</p>
                </div>
              </div>
              <div className="route-switch">
                <span>Explore a route</span>
                <div className="segmented">
                  <button
                    aria-pressed={routeType === "university"}
                    onClick={() => setRouteType("university")}
                  >
                    University
                  </button>
                  <button
                    aria-pressed={routeType === "apprenticeship"}
                    onClick={() => setRouteType("apprenticeship")}
                  >
                    Earn & learn
                  </button>
                </div>
              </div>
              {routeType === "apprenticeship" && (
                <div className="route-note">
                  <p>
                    Apprenticeships combine paid work with study. Availability
                    and professional eligibility vary by career and nation; some
                    careers require an approved degree or further training.
                  </p>
                  <External
                    href={
                      nation === "Scotland"
                        ? "https://www.apprenticeships.scot/"
                        : nation === "Wales"
                          ? "https://careerswales.gov.wales/apprenticeships"
                          : nation === "Northern Ireland"
                            ? "https://www.nidirect.gov.uk/campaigns/apprenticeships"
                            : "https://www.gov.uk/apply-apprenticeship"
                    }
                  >
                    Explore official {nation} routes
                  </External>
                </div>
              )}
              <div className="path-timeline">
                {(timelines.length
                  ? timelines
                  : [
                      {
                        stage: "This week",
                        title: "Try the work, in a small way",
                        items: content.firstSteps.slice(0, 1),
                      },
                      {
                        stage: "Next",
                        title: "Build a foundation",
                        items: [content.whyBroad],
                      },
                      {
                        stage: "As you grow",
                        title: "Find experience and specialise",
                        items: [
                          content.firstSteps[1] ??
                            "Join a community and build a small portfolio.",
                        ],
                      },
                    ]
                ).map((t, i) => (
                  <article key={t.stage}>
                    <div className="timeline-marker">{i + 1}</div>
                    <span className="tiny">{t.stage}</span>
                    <h3>{t.title}</h3>
                    <ul>
                      {t.items.map((s) => (
                        <li key={s}>{s}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
              <RelatedCareers career={career} />
              {plan?.alumni && (
                <details className="alumni-kit">
                  <summary>Make a first connection</summary>
                  <p>{plan.alumni.why}</p>
                  <h3>Questions worth asking</h3>
                  <ul>
                    {plan.alumni.questions.map((q) => (
                      <li key={q}>{q}</li>
                    ))}
                  </ul>
                  <h3>A message to get you started</h3>
                  <p className="message-template">
                    {routeType === "apprenticeship"
                      ? plan.alumni.template_apprenticeship
                      : plan.alumni.template}
                  </p>
                  <p>
                    Personalise this with your own interests. Send it yourself
                    when you feel ready.
                  </p>
                </details>
              )}
              {planError && (
                <p role="status" className="fine-print">
                  The detailed plan is unavailable. The route above is still
                  ready to explore.{" "}
                  <button onClick={() => setTab("study")}>
                    Explore study routes
                  </button>
                </p>
              )}
              <p className="fine-print">
                Example roadmap. Check current entry requirements, funding,
                accreditation, and course details before applying.
              </p>
            </section>
            <aside className="path-aside">
              <section className="everyday">
                <h3>A day in this world</h3>
                {content.dayToDay.map((s) => (
                  <p key={s}>
                    <Icon name="check" size={16} />
                    {s}
                  </p>
                ))}
              </section>
              <section className="guide-invite">
                <span className="guide-avatar">
                  {guideFor(career).name.slice(0, 1)}
                </span>
                <h3>Talk it through with {guideFor(career).name}.</h3>
                <p>
                  Ask about the work, the route, or the things you're still
                  unsure about.
                </p>
                <button
                  className="button secondary full-width"
                  onClick={onGuide}
                >
                  Meet your career guide <Icon name="chat" size={16} />
                </button>
                <small>Prepared demo guidance</small>
              </section>
              <button className="opportunity-nudge" onClick={onOpportunities}>
                <Icon name="calendar" size={22} />
                <b>Start with an opportunity</b>
                <span>Communities, events, and experience.</span>
                <Icon name="arrow" size={18} />
              </button>
            </aside>
          </div>
        </>
      )}
      {tab === "skills" && (
        <section className="skills-section">
          <h2>Build skills. Keep the doors open.</h2>
          <p>
            Explore these through a project, a class, or a small piece of real
            experience.
          </p>
          <div className="skills-columns">
            <div>
              <Icon name="code" size={25} />
              <h3>Hard skills</h3>
              <p>The practical tools of the work.</p>
              {content.hardSkills.map((s, i) => (
                <div className="skill-row" key={s}>
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <b>{s}</b>
                  <Icon name="plus" size={15} />
                </div>
              ))}
            </div>
            <div>
              <Icon name="chat" size={25} />
              <h3>Human skills</h3>
              <p>Useful here, and wherever you go next.</p>
              {content.softSkills.map((s, i) => (
                <div className="skill-row" key={s}>
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <b>{s}</b>
                  <Icon name="plus" size={15} />
                </div>
              ))}
            </div>
          </div>
          <div className="quiet-callout">
            <Icon name="leaf" />
            <p>
              One small project can build several skills at once. Start with:{" "}
              <b>{content.firstSteps[0]}</b>
            </p>
          </div>
        </section>
      )}
      {tab === "study" && (
        <section className="study-section">
          <h2>Find a place to grow.</h2>
          <p>
            Established universities and course routes to explore. These are
            examples, not a league table or a statement of eligibility.
          </p>
          {content.universities.length === 0 && (
            <div className="route-note">
              <h3>Start with a practical training route.</h3>
              <p>
                A university degree is not the standard first step for this
                career. Explore an apprenticeship, accredited training, and your
                nation’s entry requirements.
              </p>
              <External
                href={
                  nation === "Scotland"
                    ? "https://www.apprenticeships.scot/"
                    : "https://www.gov.uk/apply-apprenticeship"
                }
              >
                Explore official apprenticeship routes
              </External>
            </div>
          )}
          <div className="university-list">
            {content.universities.map((u) => (
              <article key={u.name}>
                <span className="university-icon">
                  <Icon name="building" size={25} />
                </span>
                <div>
                  <span className="tiny">{u.nation}</span>
                  <h3>{u.name}</h3>
                  <p>{u.course}</p>
                </div>
                <External className="button secondary" href={u.url}>
                  Explore course
                </External>
              </article>
            ))}
          </div>
          <div className="study-reminder">
            <h3>A good university is one that fits your life.</h3>
            <p>
              Compare the modules, accreditation, entry requirements, location,
              funding, and support. The broadest degree isn't always the best
              route for a regulated profession.
            </p>
            <div>
              <External href="https://www.ucas.com/">Search UCAS</External>
              <External href="https://discoveruni.gov.uk/">
                Compare with Discover Uni
              </External>
            </div>
          </div>
        </section>
      )}
      {tab === "reality" && (
        <>
          <div className="evidence-metrics">
            <MetricDetail
              career={career}
              metricKey="pay_median"
              label="The middle half of annual pay"
            />
            <MetricDetail
              career={career}
              metricKey="demand_trend"
              label="Recent employment trend"
            />
            <MetricDetail
              career={career}
              metricKey="exposure"
              label="Automation exposure (research estimate)"
            />
          </div>
          <SalaryChart careers={[career]} />
          <div className="quiet-callout">
            <Icon name="info" />
            <p>
              Starting salaries, working hours, and overtime are not included in
              the supplied dataset. Ask employers about these; median earnings
              describe the full-time workforce, not a new starter.
            </p>
          </div>
        </>
      )}
    </>
  );
}

function Opportunities({
  careers,
  prefs,
  update,
  notify,
}: {
  careers: Career[];
  prefs: Preferences;
  update: (p: Partial<Preferences>) => void;
  notify: (s: string) => void;
}) {
  const [kind, setKind] = useState("All");
  const [scope, setScope] = useState("nearby");
  const [onlySaved, setOnlySaved] = useState(false);
  const [refreshed, setRefreshed] = useState("");
  const all = careers
    .flatMap((c) => getCareerContent(c.soc, c.family).opportunities)
    .filter((o, i, a) => a.findIndex((x) => x.url === o.url) === i);
  const visible = all.filter(
    (o) =>
      (kind === "All" || o.kind === kind) &&
      (!onlySaved || prefs.saved.includes(o.id)) &&
      (scope === "all" ||
        o.nation === prefs.nation ||
        o.nation === "UK" ||
        o.location.toLowerCase().includes("online") ||
        o.location.toLowerCase().includes(prefs.location.toLowerCase())),
  );
  return (
    <>
      <PageHeading
        label="A reason to keep exploring"
        title="Find your next opportunity."
        description={`Communities, experience, and events relevant to your three directions. Start close to ${prefs.location || "home"}, or look a little further.`}
        action={
          <button
            className="button secondary"
            onClick={() => {
              setRefreshed(
                new Date().toLocaleTimeString("en-GB", {
                  hour: "2-digit",
                  minute: "2-digit",
                }),
              );
              notify(
                "Directory refreshed. Open an organiser's site to check current dates and places.",
              );
            }}
          >
            <Icon name="refresh" size={15} /> Refresh
          </button>
        }
      />
      <div className="opportunities-toolbar">
        <div className="filter-pills" aria-label="Opportunity type">
          {["All", "Event", "Internship", "Programme", "Community"].map((k) => (
            <button
              key={k}
              className={kind === k ? "active" : ""}
              aria-pressed={kind === k}
              onClick={() => setKind(k)}
            >
              {k === "All"
                ? "All opportunities"
                : `${k}${k === "Community" ? "" : "s"}`}
            </button>
          ))}
        </div>
        <label className="inline-select">
          <Icon name="pin" size={16} />
          <select
            aria-label="Opportunity location"
            value={scope}
            onChange={(e) => setScope(e.target.value)}
          >
            <option value="nearby">{prefs.nation} & online</option>
            <option value="all">All UK locations</option>
          </select>
        </label>
      </div>
      <div className="directory-meta">
        <span>
          {visible.length} places to explore
          {refreshed ? ` · Refreshed ${refreshed}` : ""}
        </span>
        <label>
          <input
            type="checkbox"
            checked={onlySaved}
            onChange={(e) => setOnlySaved(e.target.checked)}
          />{" "}
          Saved only ({prefs.saved.length})
        </label>
      </div>
      <div className="opportunity-grid">
        {visible.length ? (
          visible.map((o) => (
            <article className="opportunity-card" key={o.id}>
              <div className="opportunity-card-top">
                <span
                  className={`opportunity-kind kind-${o.kind.toLowerCase()}`}
                >
                  <Icon
                    name={
                      o.kind === "Event"
                        ? "calendar"
                        : o.kind === "Community"
                          ? "chat"
                          : "book"
                    }
                    size={17}
                  />
                  {o.kind}
                </span>
                <button
                  className={`icon-button save-button ${prefs.saved.includes(o.id) ? "saved" : ""}`}
                  aria-label={`${prefs.saved.includes(o.id) ? "Unsave" : "Save"} ${o.title}`}
                  aria-pressed={prefs.saved.includes(o.id)}
                  onClick={() => {
                    update({
                      saved: prefs.saved.includes(o.id)
                        ? prefs.saved.filter((id) => id !== o.id)
                        : [...prefs.saved, o.id],
                    });
                    notify(
                      prefs.saved.includes(o.id)
                        ? "Removed from saved opportunities."
                        : "Opportunity saved to this device.",
                    );
                  }}
                >
                  <Icon name="save" size={18} />
                </button>
              </div>
              <h3>{o.title}</h3>
              <p>{o.description}</p>
              <div className="opportunity-location">
                <Icon name="pin" size={14} />
                {o.location}
              </div>
              <External href={o.url}>Explore with the organiser</External>
            </article>
          ))
        ) : (
          <div className="empty-state">
            <Icon name="calendar" size={35} />
            <h3>No matching opportunities in this view.</h3>
            <p>Try all UK locations, another type, or turn off “Saved only”.</p>
            <button
              className="button secondary"
              onClick={() => {
                setKind("All");
                setScope("all");
                setOnlySaved(false);
              }}
            >
              Show all opportunities
            </button>
          </div>
        )}
      </div>
      <div className="quiet-callout">
        <Icon name="info" size={20} />
        <p>
          This is a curated discovery directory, not a live vacancy feed. Dates,
          places, costs, age limits, and availability change. Check each
          organiser before making plans. Refresh checks this saved directory; it
          doesn't fetch new listings.
        </p>
      </div>
    </>
  );
}

function Guides({ careers }: { careers: Career[] }) {
  const [soc, setSoc] = useState(careers[0].soc);
  const career = careers.find((c) => c.soc === soc) ?? careers[0];
  const guide = guideFor(career);
  const [messages, setMessages] = useState<
    { role: "user" | "guide"; text: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setMessages([]);
    setError("");
    setInput("");
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, [soc]);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [messages]);
  useEffect(() => () => window.speechSynthesis?.cancel(), []);
  const send = async (text: string) => {
    if (!text.trim() || sending) return;
    setMessages((m) => [...m, { role: "user", text: text.trim() }]);
    setInput("");
    setSending(true);
    setError("");
    try {
      const answer = await api<{ text: string; mode: string }>("guide", {
        soc: career.soc,
        message: text.trim(),
        history: messages.slice(-8).map((m) => ({
          role: m.role === "guide" ? "assistant" : "user",
          content: m.text,
        })),
      });
      setMessages((m) => [...m, { role: "guide", text: answer.text }]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  };
  const introduction = `Hi, I'm ${guide.name}. Let's explore ${career.title.toLowerCase()} together. I can help you think through the day-to-day work, the skills to build, and routes into it. What would you like to understand?`;
  const lastText =
    messages.filter((m) => m.role === "guide").slice(-1)[0]?.text ??
    introduction;
  return (
    <>
      <PageHeading
        label="A conversation, a little clarity"
        title="Talk through your next step."
        description="Meet a guide for your chosen career. Ask the practical questions, or start with the ones below."
      />
      <div className="guide-layout">
        <aside className="guide-choices">
          <h3>Your career guides</h3>
          {careers.map((c) => {
            const g = guideFor(c);
            return (
              <button
                key={c.soc}
                className={c.soc === career.soc ? "active" : ""}
                onClick={() => setSoc(c.soc)}
              >
                <span className="guide-avatar small">{g.name.charAt(0)}</span>
                <span>
                  <b>{g.name}</b>
                  <small>{c.title}</small>
                </span>
                <Icon name="chevron" size={14} />
              </button>
            );
          })}
          <p>
            Prepared demo guides explain the supplied evidence. They aren't live
            LLM conversations.
          </p>
        </aside>
        <section className="guide-chat">
          <header>
            <span className="guide-avatar">{guide.name.charAt(0)}</span>
            <div>
              <h3>{guide.name}</h3>
              <span>{guide.role}</span>
            </div>
            <span className="subtle-badge">Demo guide</span>
          </header>
          <div
            className="chat-scroll"
            role="log"
            aria-label={`Conversation with ${guide.name}`}
          >
            <div className="chat-message guide-message">
              <b>{guide.name}</b>
              <p>{introduction}</p>
            </div>
            {messages.map((m, i) => (
              <div
                className={`chat-message ${m.role === "user" ? "user-message" : "guide-message"}`}
                key={i}
              >
                <b>{m.role === "user" ? "You" : guide.name}</b>
                <p>{m.text}</p>
                {m.role === "guide" && (
                  <span className="tiny">
                    Prepared from supplied career evidence. Check the source.
                  </span>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-message guide-message" role="status">
                <span className="spinner" /> Looking through your career
                evidence…
              </div>
            )}
            <div ref={end} />
          </div>
          {messages.length === 0 && (
            <div className="chat-suggestions">
              {[
                "What does a normal day look like?",
                "What skills could I start building?",
                "Which degree keeps my options open?",
                "How might AI change this career?",
              ].map((p) => (
                <button disabled={sending} onClick={() => send(p)} key={p}>
                  {p}
                  <Icon name="plus" size={13} />
                </button>
              ))}
            </div>
          )}
          {error && (
            <div role="alert" className="inline-error">
              {error} Your question is still in this conversation; try sending
              it again.
            </div>
          )}
          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              void send(input);
            }}
          >
            <input
              maxLength={1500}
              aria-label="Ask your career guide"
              value={input}
              disabled={sending}
              placeholder={`Ask ${guide.name} about ${career.title.toLowerCase()}…`}
              onChange={(e) => setInput(e.target.value)}
            />
            <button
              type="submit"
              className="button primary"
              disabled={!input.trim() || sending}
              aria-label="Send question"
            >
              <Icon name="arrow" size={19} />
            </button>
          </form>
          <div className="chat-disclosure">
            <span>Exploratory guidance. Your conversation isn't saved.</span>
            {typeof window.speechSynthesis !== "undefined" && (
              <button
                onClick={() => {
                  if (speaking) {
                    window.speechSynthesis.cancel();
                    setSpeaking(false);
                  } else {
                    const utterance = new SpeechSynthesisUtterance(lastText);
                    utterance.lang = "en-GB";
                    utterance.onend = () => setSpeaking(false);
                    window.speechSynthesis.speak(utterance);
                    setSpeaking(true);
                  }
                }}
              >
                {speaking ? "Stop reading" : "Read response aloud"}
              </button>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

type HistoricalGroup = {
  key: string;
  label: string;
  n: number;
  real_pay_growth: { median: number; low: number; high: number } | null;
  jobs_growth: { median: number; low: number; high: number } | null;
  share_jobs_fell: number | null;
};
function BacktestGroup({ group: g }: { group: HistoricalGroup }) {
  return (
    <article>
      <h3>{g.label}</h3>
      <div className="backtest-stat">
        <span>Occupations in the group</span>
        <b>{g.n}</b>
      </div>
      {(
        [
          ["Real pay growth", g.real_pay_growth],
          ["Employment growth", g.jobs_growth],
        ] as const
      ).map(([label, metric]) => (
        <div key={label} className="historical-metric">
          <div className="backtest-stat">
            <span>{label}</span>
            <b>{metric ? percent(metric.median) : "Not comparable"}</b>
          </div>
          {metric && (
            <small>
              Middle half: {percent(metric.low)} to {percent(metric.high)}
            </small>
          )}
        </div>
      ))}
      <div className="backtest-stat">
        <span>Share with fewer jobs</span>
        <b>
          {g.share_jobs_fell == null
            ? "Not comparable"
            : `${(g.share_jobs_fell * 100).toFixed(1)}%`}
        </b>
      </div>
    </article>
  );
}

function Evidence({ data, selected }: { data: Bootstrap; selected: Career[] }) {
  const [windowIndex, setWindowIndex] = useState(0);
  const windows = (data.backtest.windows ?? []) as {
    base_year: number;
    outcome_year: number;
    groups: (HistoricalGroup | null)[];
    [k: string]: unknown;
  }[];
  const w = windows[windowIndex];
  const raw = data.sources as Record<string, unknown>;
  const registry = (raw?.sources ?? raw ?? {}) as Record<
    string,
    {
      name?: string;
      publisher?: string;
      url?: string;
      status?: string;
      coverage?: string;
    }
  >;
  return (
    <>
      <PageHeading
        label="Context before confidence"
        title="Where the numbers come from."
        description="Real evidence can help you ask better questions. It can't make the decision for you."
      />
      <SalaryChart careers={selected} />
      <section className="track-record">
        <div className="section-header">
          <div>
            <h2>How did earlier signals hold up?</h2>
            <p>Earlier career signals, compared with what happened next.</p>
          </div>
          <select
            aria-label="Historical test window"
            value={windowIndex}
            onChange={(e) => setWindowIndex(Number(e.target.value))}
          >
            {windows.map((item, i) => (
              <option key={i} value={i}>
                {item.base_year} → {item.outcome_year}
              </option>
            ))}
          </select>
        </div>
        {w ? (
          <>
            <div className="backtest-groups">
              {w.groups
                ?.filter((g): g is HistoricalGroup => g !== null)
                .map((g) => (
                  <BacktestGroup key={g.key} group={g} />
                ))}
            </div>
            <p className="fine-print">
              Source: supplied historical test · Preliminary. Historical tiers
              are based on market data only; they do not test the personalised
              quiz or the three priority sliders.
            </p>
          </>
        ) : (
          <p>Historical test results aren't available in this snapshot.</p>
        )}
        <details>
          <summary>Read the method and limitations</summary>
          <p>{String(data.backtest.method ?? "")}</p>
          <ul className="plain-list">
            {((data.backtest.caveats ?? []) as string[]).map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </details>
      </section>
      <section className="evidence-explainer">
        <h2>Know what you're looking at.</h2>
        <div>
          <article>
            <Icon name="heart" />
            <h3>Interest fit is exploratory.</h3>
            <p>
              The questions are informed by work-interest psychology. They are
              not a validated assessment. Interest matching uses the supplied
              {data.data_status.fit === "mock"
                ? " sample affinities"
                : " preliminary embedding affinities"}
              . These indices are a starting point for exploration, not
              probabilities.
            </p>
            <p>{data.data_status.fit_evaluation?.note}</p>
          </article>
          <article>
            <Icon name="chart" />
            <h3>Need isn't a promise.</h3>
            <p>
              The need signal compares historical employee-job trends across the
              available careers. It is not an LLM forecast, vacancy count, or a
              probability of finding a job.
            </p>
          </article>
          <article>
            <Icon name="money" />
            <h3>Pay needs context.</h3>
            <p>
              Median full-time pay is not a starting salary. Inflation-adjusted
              pay measures purchasing power. The data excludes self-employed
              workers; overtime and working-hours comparisons are not supplied.
            </p>
          </article>
        </div>
      </section>
      <section className="source-list">
        <h2>Follow the sources.</h2>
        {Object.entries(registry)
          .filter(([, s]) => s && typeof s === "object" && s.name && s.url)
          .map(([key, s]) => (
            <article key={key}>
              <div>
                <b>{s.publisher ?? s.name}</b>
                <p>{s.name}</p>
                <span>{s.coverage}</span>
              </div>
              <span className="subtle-badge">{s.status ?? "snapshot"}</span>
              <External href={s.url!}>View source</External>
            </article>
          ))}
      </section>
    </>
  );
}
