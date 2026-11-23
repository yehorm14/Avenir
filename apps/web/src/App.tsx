import { useEffect, useRef, useState } from "react";
import type { Bootstrap, Career, Page, Preferences, Weights } from "./types";
import { api, initial, usePreferences } from "./store";
import { questions, tagsFromAnswers } from "./quiz";
import { Icon, careerIcon } from "./icons";
import { SalaryChart, money, percent } from "./Charts";
import { allOpportunities, getCareerContent } from "./content";
import {
  buildPlanDocument,
  resolvePlanRoute,
  demandTrendLabel,
  isRelativeDemand,
  metricCaveats,
} from "./planDocument";
import MyPlan from "./MyPlan";
import { metricLabel } from "./metricLabel";
import Guides from "./Guides";
import Landing from "./Landing";
import Jobs from "./Jobs";
import Discovery, { type DiscoveryResult } from "./Discovery";
import CareerDashboard from "./CareerDashboard";

const pageNames: Record<Page, string> = {
  discover: "Discover",
  "computer-science": "Computer Science",
  finance: "Finance",
  conversation: "Your conversation",
  quiz: "Quiz",
  jobs: "Jobs",
  matches: "Your matches",
  overview: "My plan",
  path: "Your pathway",
  opportunities: "Opportunities",
  guides: "Chatbot",
  evidence: "The evidence",
};
const nav: { id: Page; icon: string }[] = [
  { id: "overview", icon: "home" },
  { id: "matches", icon: "compass" },
  { id: "path", icon: "path" },
  { id: "opportunities", icon: "calendar" },
];
// Pages shown under the Jobs tab: the full directory and the two subject dashboards.
const jobsSection: Page[] = ["jobs", "computer-science", "finance"];
const directPlanSocs = ["2134", "3544", "2133", "2135", "2422", "2421", "2433"];
// Amira, 17, S6 in Glasgow: the primary demo journey.
const amiraAnswers: Record<string, string> = {
  direction: "Architect",
  interests: "Making or designing something; Solving a tricky problem",
  subjects: "Maths; Art and design",
  values: "Long-term demand; Making a useful impact",
  skills: "Maths and data; Drawing or design",
};
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
  const [guideSoc, setGuideSoc] = useState<string | null>(
    () => window.location.hash.split("/")[2] ?? null,
  );
  const [data, setData] = useState<Bootstrap | null>(null);
  const [loadError, setLoadError] = useState("");
  const [reload, setReload] = useState(0);
  const [matches, setMatches] = useState<Career[]>([]);
  const [ranking, setRanking] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [toast, setToast] = useState("");
  const [amiraBusy, setAmiraBusy] = useState(false);
  const [amiraError, setAmiraError] = useState("");
  const [inspect, setInspect] = useState<Career | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const go = (p: Page, soc?: string) => {
    setPage(p);
    setGuideSoc(p === "guides" ? (soc ?? null) : null);
    window.location.hash = `/${p}${p === "guides" && soc ? `/${soc}` : ""}`;
    window.scrollTo(0, 0);
    setTimeout(() => mainRef.current?.focus({ preventScroll: true }), 0);
  };
  useEffect(() => {
    const fn = () => {
      setPage(route());
      setGuideSoc(window.location.hash.split("/")[2] ?? null);
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
  const guideCareer = careers.find((career) => career.soc === guideSoc);
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
    update({
      completed: true,
      step: questions.length,
      discovery: undefined,
    });
    go("matches");
  };
  const completeDiscovery = (result: DiscoveryResult) => {
    setPrefs((p) => ({
      ...p,
      completed: true,
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
  const startAmira = async () => {
    if (amiraBusy) return;
    setAmiraBusy(true);
    setAmiraError("");
    try {
      const result = await api<DiscoveryResult>("discovery", {
        mode: "known",
        answers: amiraAnswers,
      });
      const reference = result.reference_soc ?? result.target_soc;
      const socs = [
        ...new Set([reference, ...result.results.map((c) => c.soc)]),
      ]
        .filter((soc): soc is string => !!soc)
        .slice(0, 3);
      setPrefs((p) => ({
        ...p,
        completed: true,
        answers: {},
        weights: result.weights,
        nation: "Scotland",
        location: "Glasgow",
        selected: socs,
        discovery: {
          mode: "known",
          answers: amiraAnswers,
          step: 5,
          tags: result.tags,
          targetSoc: result.target_soc,
          referenceSoc: result.reference_soc,
          summary: result.profile_summary,
          notices: result.notices,
        },
      }));
      setMatches(result.results);
      go("matches");
    } catch (cause) {
      setAmiraError(
        cause instanceof Error
          ? cause.message
          : "We couldn’t compare careers. Try again.",
      );
    } finally {
      setAmiraBusy(false);
    }
  };
  const showShell = !["discover", "quiz", "conversation"].includes(page);
  const useCareer = (career: Career, destination: Page, weights?: Weights) => {
    // Subject exploration does not imply a completed quiz or a personal match.
    setPrefs((current) => ({
      ...current,
      ...(weights ? { weights } : {}),
      completed: false,
      selected: [
        career.soc,
        ...current.selected.filter((soc) => soc !== career.soc),
      ].slice(0, 3),
    }));
    go(destination);
  };
  const exportPlan = () => {
    if (!primary || !data) return;
    const body = buildPlanDocument({
      careers: selected,
      preferences: prefs,
      content: Object.fromEntries(
        selected.map((c) => [c.soc, getCareerContent(c.soc, c.family)]),
      ),
      opportunities: allOpportunities,
      sources: data.sources as Record<string, { name?: string; url?: string }>,
    });
    const url = URL.createObjectURL(
      new Blob([body], { type: "text/html;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "my-avenir-plan.html";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setToast("Plan downloaded. Open it in a browser to share or print.");
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
        <nav className="top-links" aria-label="Main navigation">
          {(
            [
              ["discover", "Home"],
              ["quiz", "Quiz"],
              ["jobs", "Jobs"],
              ["overview", "My plan"],
              ["guides", "Chatbot"],
            ] as const
          ).map(([id, label]) => {
            // The subject dashboards live under Jobs, so Jobs stays active inside them.
            const current =
              page === id || (id === "jobs" && jobsSection.includes(page));
            return (
              <button
                key={id}
                onClick={() => go(id)}
                className={current ? "active" : ""}
                aria-current={current ? "page" : undefined}
              >
                {label}
              </button>
            );
          })}
        </nav>
      </header>
      <main
        id="main"
        ref={mainRef}
        tabIndex={-1}
        className={`main-content ${showShell ? "workspace" : ""}`}
      >
        {showShell &&
          primary &&
          ["matches", "path", "opportunities", "evidence"].includes(page) && (
            <nav className="plan-navigation" aria-label="Plan navigation">
              {[...nav, { id: "evidence" as const, icon: "chart" }]
                .filter((n) => n.id !== "matches" || prefs.completed)
                .map((n) => (
                  <button
                    key={n.id}
                    onClick={() => go(n.id)}
                    aria-current={page === n.id ? "page" : undefined}
                  >
                    {pageNames[n.id]}
                  </button>
                ))}
            </nav>
          )}
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
            {jobsSection.includes(page) && <JobsTabs page={page} go={go} />}
            {page === "discover" && (
              <Landing
                careers={careers}
                onChoose={start}
                onAmira={startAmira}
                amiraBusy={amiraBusy}
                amiraError={amiraError}
                onJobs={() => go("jobs")}
                onPlan={() => go("overview")}
                nation={prefs.nation}
                location={prefs.location}
                onNation={(nation) => update({ nation })}
                onLocation={(location) => update({ location })}
                onDashboard={(area) =>
                  go(area === "cs" ? "computer-science" : "finance")
                }
                resume={
                  primary
                    ? { title: primary.title, onResume: () => go("overview") }
                    : undefined
                }
              />
            )}
            {(page === "computer-science" || page === "finance") && (
              <CareerDashboard
                key={page}
                area={page === "computer-science" ? "cs" : "finance"}
                careers={careers}
                sourceRegistry={
                  data.sources as Record<
                    string,
                    { name?: string; url?: string }
                  >
                }
                onPlan={(career, weights) => useCareer(career, "path", weights)}
                onGuide={(career) => go("guides", career.soc)}
                saved={prefs.saved}
                onToggleSave={(id) =>
                  setPrefs((current) => ({
                    ...current,
                    saved: current.saved.includes(id)
                      ? current.saved.filter((savedId) => savedId !== id)
                      : [...current.saved, id],
                  }))
                }
              />
            )}
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
              <Quiz prefs={prefs} update={update} finish={finish} />
            )}
            {page === "jobs" && (
              <Jobs
                careers={careers}
                onExplore={(career) => {
                  update({
                    discovery: {
                      mode: "known",
                      answers: { direction: career.title },
                      step: 1,
                    },
                  });
                  go("conversation");
                }}
              />
            )}
            {page === "matches" &&
              (prefs.completed ? (
                <>
                  <PageHeading title="Three careers to explore." />
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
                                <span>
                                  {demandTrendLabel(c.metrics.demand_trend)}
                                </span>
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
                            {i === 0 &&
                              !prefs.discovery?.referenceSoc &&
                              !prefs.discovery?.targetSoc && (
                                <span className="sr-only">
                                  Highest overall score for your current
                                  priorities.
                                </span>
                              )}
                          </article>
                        ))
                      )}
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
                        <button
                          className="text-button muted"
                          onClick={() => update({ weights: initial.weights })}
                        >
                          <Icon name="refresh" size={14} /> Reset balance
                        </button>
                      </section>
                      <section className="shortlist">
                        <h3>Your three directions</h3>
                        <p>
                          The first choice becomes your main plan. Your choices
                          stay here until you remove or replace them.
                        </p>
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
                <MyPlan
                  careers={selected}
                  prefs={prefs}
                  update={update}
                  go={go}
                  onExport={exportPlan}
                  onReset={() => {
                    setPrefs(structuredClone(initial));
                    setMatches([]);
                    go("discover");
                    setToast("Saved plan cleared from this browser.");
                  }}
                />
              ) : prefs.completed ? (
                <NeedChoices go={go} />
              ) : (
                empty
              ))}
            {page === "path" &&
              (primary ? (
                <Pathway
                  career={primary}
                  allowedSocs={
                    !prefs.completed && directPlanSocs.includes(primary.soc)
                      ? directPlanSocs
                      : undefined
                  }
                  nation={prefs.nation}
                  routeType={resolvePlanRoute(
                    getCareerContent(primary.soc, primary.family),
                    prefs.routes[primary.soc],
                  )}
                  onRouteChange={(routeType) =>
                    update({
                      routes: { ...prefs.routes, [primary.soc]: routeType },
                    })
                  }
                  onExport={exportPlan}
                  onOpportunities={() => go("opportunities")}
                  onGuide={() => go("guides", primary.soc)}
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
            {page === "guides" && careers.length > 0 && (
              <Guides
                key={guideCareer?.soc ?? "all"}
                careers={
                  guideCareer
                    ? [guideCareer]
                    : selected.length
                      ? selected
                      : careers
                }
              />
            )}
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
          <span>© 2026 Avenir</span>
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
                label={`${demandTrendLabel(inspect.metrics.demand_trend)}, ${inspect.metrics.demand_trend?.as_of || "period unavailable"}`}
              />
              <MetricDetail
                career={inspect}
                metricKey="exposure"
                label="Automation exposure (research estimate)"
              />
            </div>
            <SalaryChart careers={[inspect]} compact />
            {page === "jobs" ? (
              <button
                className="button primary"
                onClick={() => {
                  update({
                    discovery: {
                      mode: "known",
                      answers: { direction: inspect.title },
                      step: 1,
                    },
                  });
                  setInspect(null);
                  go("conversation");
                }}
              >
                Explore career
              </button>
            ) : (
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
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function JobsTabs({ page, go }: { page: Page; go: (p: Page) => void }) {
  return (
    <nav className="content-tabs jobs-sections" aria-label="Jobs sections">
      {(
        [
          ["jobs", "All jobs"],
          ["computer-science", "Computer Science"],
          ["finance", "Finance"],
        ] as const
      ).map(([id, label]) => (
        <button
          key={id}
          className={page === id ? "active" : ""}
          aria-current={page === id ? "page" : undefined}
          onClick={() => go(id)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

function PageHeading({
  label,
  title,
  description,
  action,
}: {
  label?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        {label && <p className="page-context">{label}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action}
    </header>
  );
}
function NeedChoices({ go }: { go: (p: Page) => void }) {
  return (
    <div className="empty-state">
      <h2>Choose a career to plan</h2>
      <p>Open a dashboard, then select “Build my plan”.</p>
      <div className="decision-buttons">
        <button
          className="button primary"
          onClick={() => go("computer-science")}
        >
          Computer Science
        </button>
        <button className="button secondary" onClick={() => go("finance")}>
          Finance
        </button>
      </div>
    </div>
  );
}

function Quiz({
  prefs,
  update,
  finish,
}: {
  prefs: Preferences;
  update: (p: Partial<Preferences>) => void;
  finish: () => void;
}) {
  // A finished quiz stores the end position. Reopening it should let the
  // learner review their answers from the start, rather than strand them.
  const step = prefs.step < questions.length ? prefs.step : 0,
    q = questions[step];
  const answered = prefs.answers[q.id];
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [step]);
  return (
    <section className="quiz-container" key={q.id}>
      <div className="quiz-progress">
        {step > 0 && (
          <button
            className="text-button"
            onClick={() => update({ step: step - 1 })}
          >
            <Icon name="back" size={16} /> Previous question
          </button>
        )}
        <span>
          Question {step + 1} of {questions.length}
        </span>
      </div>
      <div className="progress-track">
        <i style={{ width: `${((step + 1) / questions.length) * 100}%` }} />
      </div>
      <h1 ref={headingRef} tabIndex={-1}>
        {q.title}
      </h1>
      <div className="quiz-options" role="radiogroup" aria-label={q.title}>
        {q.options.map((o, i) => (
          <button
            role="radio"
            aria-checked={answered === i}
            tabIndex={i === (answered ?? 0) ? 0 : -1}
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
                    q.options.length) %
                  q.options.length;
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
        <button
          className="button primary"
          disabled={answered === undefined}
          onClick={() =>
            step === questions.length - 1
              ? finish()
              : update({ step: step + 1 })
          }
        >
          {step === questions.length - 1 ? "Finish quiz" : "Continue"}
          <Icon name="arrow" size={18} />
        </button>
      </div>
      <p className="fine-print">
        The quiz explores work interests; it is not a validated psychological
        assessment.
      </p>
    </section>
  );
}

function RelatedCareers({
  career,
  allowedSocs,
}: {
  career: Career;
  allowedSocs?: readonly string[];
}) {
  const related =
    career.hedges
      ?.filter((hedge) => !allowedSocs || allowedSocs.includes(hedge.soc2020))
      .slice(0, 2) ?? [];
  if (!related.length) return null;
  return (
    <section className="related-careers">
      <h3>Skills that open another door.</h3>
      <p>Related careers can give you another way forward.</p>
      {related.map((h) => (
        <article key={h.soc2020}>
          {!directPlanSocs.includes(career.soc) && (
            <Icon name="path" size={18} />
          )}
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
          ? `${metricLabel(m).text} · ${m.status} · ${m.confidence} confidence`
          : "Not included in this snapshot"}
      </small>
      {metricKey === "pay_median" && (
        <p>
          Middle half of full-time employees; excludes self-employed workers.
          This is not a starting salary.
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
          {isRelativeDemand(m)
            ? "Annual employee-job growth relative to the typical occupation. "
            : "Historical annual employee-job growth. "}
          {m?.low != null && m.high != null
            ? `Range: ${percent(m.low)} to ${percent(m.high)}. `
            : ""}
          Not a forecast of vacancies.
        </p>
      )}
      {m?.note && <p>{m.note}</p>}
      {m && metricCaveats(m) && <p>{metricCaveats(m)}</p>}
      {m?.flags.includes("imputed_parent") && (
        <p>
          No direct figure exists; this is estimated from the wider occupation
          group.
        </p>
      )}
      {m?.flags.includes("provisional") && (
        <p>This figure is provisional and may be revised.</p>
      )}
      {m?.flags.includes("category_level") && (
        <p>
          Broad job-advert category, not this exact occupation
          {typeof m.extra?.adverts_category === "string"
            ? `: ${m.extra.adverts_category}`
            : ""}
          .
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
  allowedSocs,
  nation,
  routeType,
  onRouteChange,
  onExport,
  onOpportunities,
  onGuide,
}: {
  career: Career;
  allowedSocs?: readonly string[];
  nation: string;
  routeType: "university" | "apprenticeship";
  onRouteChange: (route: "university" | "apprenticeship") => void;
  onExport: () => void;
  onOpportunities: () => void;
  onGuide: () => void;
}) {
  const content = getCareerContent(career.soc, career.family);
  const focused = directPlanSocs.includes(career.soc);
  const [tab, setTab] = useState("plan");
  const [plan, setPlan] = useState<Plan | null>(null);
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
    <section className={`pathway${focused ? " pathway-focused" : ""}`}>
      <PageHeading
        label={focused ? "" : "Career pathway"}
        title={career.title}
        description="Compare study routes, practise the skills and choose a next step."
        action={
          <button className="button secondary" onClick={onExport}>
            <Icon name="download" size={16} /> Save my plan
          </button>
        }
      />
      <div className="path-hero">
        {!focused && <CareerMark career={career} large />}
        <div>
          {!focused && (
            <>
              <span className="tiny">Your first choice</span>
              <h2>{career.title}</h2>
            </>
          )}
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
          ["reality", "Pay and employment"],
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
                <h2>Study and training routes</h2>
              </div>
              <div className="broad-degree">
                {!focused && <Icon name="book" size={24} />}
                <div>
                  {!focused && (
                    <span className="tiny">A route worth exploring</span>
                  )}
                  <h3>{content.broadDegree}</h3>
                  <p>{content.whyBroad}</p>
                </div>
              </div>
              <div className="route-switch">
                <span>Explore a route</span>
                <div className="segmented">
                  <button
                    aria-pressed={routeType === "university"}
                    onClick={() => onRouteChange("university")}
                  >
                    University
                  </button>
                  <button
                    aria-pressed={routeType === "apprenticeship"}
                    onClick={() => onRouteChange("apprenticeship")}
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
              <RelatedCareers career={career} allowedSocs={allowedSocs} />
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
                <h3>Typical tasks</h3>
                {content.dayToDay.map((s) => (
                  <p key={s}>
                    {!focused && <Icon name="check" size={16} />}
                    {s}
                  </p>
                ))}
              </section>
              <section className="guide-invite">
                {!focused && <Icon name="chat" size={28} />}
                <h3>Ask about the evidence.</h3>
                <p>
                  Ask about the work, the route, or the things you're still
                  unsure about.
                </p>
                <button
                  className="button secondary full-width"
                  onClick={onGuide}
                >
                  Open career guide {!focused && <Icon name="chat" size={16} />}
                </button>
                <small>Prepared demo guidance</small>
              </section>
              <button className="opportunity-nudge" onClick={onOpportunities}>
                {!focused && <Icon name="calendar" size={22} />}
                <b>Start with an opportunity</b>
                <span>Communities, events, and experience.</span>
                {!focused && <Icon name="arrow" size={18} />}
              </button>
            </aside>
          </div>
        </>
      )}
      {tab === "skills" && (
        <section className="skills-section">
          <h2>Skills to practise</h2>
          <p>
            Explore these through a project, a class, or a small piece of real
            experience.
          </p>
          <div className="skills-columns">
            <div>
              {!focused && <Icon name="code" size={25} />}
              <h3>Hard skills</h3>
              <p>The practical tools of the work.</p>
              {content.hardSkills.map((s, i) => (
                <div className="skill-row" key={s}>
                  {!focused && <span>{String(i + 1).padStart(2, "0")}</span>}
                  <b>{s}</b>
                  {!focused && <Icon name="plus" size={15} />}
                </div>
              ))}
            </div>
            <div>
              {!focused && <Icon name="chat" size={25} />}
              <h3>Human skills</h3>
              <p>Useful here, and wherever you go next.</p>
              {content.softSkills.map((s, i) => (
                <div className="skill-row" key={s}>
                  {!focused && <span>{String(i + 1).padStart(2, "0")}</span>}
                  <b>{s}</b>
                  {!focused && <Icon name="plus" size={15} />}
                </div>
              ))}
            </div>
          </div>
          <div className="quiet-callout">
            {!focused && <Icon name="leaf" />}
            <p>
              One small project can build several skills at once. Start with:{" "}
              <b>{content.firstSteps[0]}</b>
            </p>
          </div>
        </section>
      )}
      {tab === "study" && (
        <section className="study-section">
          <h2>Course examples</h2>
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
                {!focused && (
                  <span className="university-icon">
                    <Icon name="building" size={25} />
                  </span>
                )}
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
    </section>
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
  const relevant = careers
    .flatMap((c) => getCareerContent(c.soc, c.family).opportunities)
    .filter((o, i, a) => a.findIndex((x) => x.url === o.url) === i);
  const all = onlySaved ? allOpportunities : relevant;
  const visible = all.filter(
    (o) =>
      (kind === "All" || o.kind === kind) &&
      (!onlySaved || prefs.saved.includes(o.id)) &&
      (onlySaved ||
        scope === "all" ||
        o.nation === prefs.nation ||
        o.nation === "UK" ||
        o.location.toLowerCase().includes("online") ||
        o.location.toLowerCase().includes(prefs.location.toLowerCase())),
  );
  return (
    <>
      <PageHeading
        label="Opportunities"
        title="Learning and work experience"
        description={`Links for your selected careers. Showing ${prefs.nation} and online options by default.`}
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
        <span>{visible.length} links</span>
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
          organiser before making plans.
        </p>
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
      )
        .filter(
          ([label, metric]) =>
            label === "Real pay growth" ||
            metric ||
            g.jobs_growth ||
            g.share_jobs_fell != null,
        )
        .map(([label, metric]) => (
          <div key={label} className="historical-metric">
            <div className="backtest-stat">
              <span>{label}</span>
              <b>{metric ? percent(metric.median) : "Not comparable"}</b>
            </div>
            {metric && (
              <small>
                95% confidence interval for the median: {percent(metric.low)} to{" "}
                {percent(metric.high)}
              </small>
            )}
          </div>
        ))}
      {(g.jobs_growth || g.share_jobs_fell != null) && (
        <div className="backtest-stat">
          <span>Share with fewer jobs</span>
          <b>
            {g.share_jobs_fell == null
              ? "Not comparable"
              : `${(g.share_jobs_fell * 100).toFixed(1)}%`}
          </b>
        </div>
      )}
    </article>
  );
}

function Evidence({ data, selected }: { data: Bootstrap; selected: Career[] }) {
  const windows = (data.backtest.windows ?? []) as {
    base_year: number;
    outcome_year: number;
    groups: (HistoricalGroup | null)[];
    [k: string]: unknown;
  }[];
  const [windowIndex, setWindowIndex] = useState(() => {
    let last = -1;
    windows.forEach((item, i) => {
      if (item.outcome_year <= 2020) last = i;
    });
    return last >= 0 ? last : 0;
  });
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
            <h2>How simple rules held up</h2>
            <p>Base-year market rules, compared with later outcomes.</p>
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
                ?.filter((g): g is HistoricalGroup => g !== null && g.n > 0)
                .map((g) => (
                  <BacktestGroup key={g.key} group={g} />
                ))}
            </div>
            {w.base_year < 2021 && w.outcome_year >= 2021 && (
              <p className="fine-print">
                Employment measures are not comparable across the 2021 code
                change, so this window shows pay only.
              </p>
            )}
            <p className="fine-print">
              Source: supplied historical test · Preliminary. Historical tiers
              are based on market data only; they do not test the personalised
              quiz or the pay and employment priorities you set.
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
      <section className="track-record">
        <details>
          <summary>Which historical disruption checks are useful?</summary>
          <p>
            We compare the spread between occupations during a shock with
            ordinary periods. A similar spread in ordinary years weakens the
            claim that the measure captures crisis resilience.
          </p>
          <ul className="plain-list">
            {(
              data.crises as {
                key: string;
                label: string;
                window: string;
                show_on_card?: boolean;
                placebo?: {
                  passes?: boolean | null;
                  ratio?: number;
                  note?: string;
                };
              }[]
            ).map((crisis) => (
              <li key={crisis.key}>
                <b>
                  {crisis.label} · {crisis.window}
                </b>
                :{" "}
                {crisis.show_on_card === false
                  ? "Failed the placebo threshold; excluded from recommendations."
                  : crisis.placebo?.passes === true
                    ? "Passed the placebo threshold; remains preliminary."
                    : "No placebo comparison available; treat cautiously."}
                {crisis.placebo?.ratio != null &&
                  ` Spread ratio: ${crisis.placebo.ratio.toFixed(2)}; threshold 1.25.`}
                {crisis.placebo?.note && ` ${crisis.placebo.note}`}
              </li>
            ))}
          </ul>
          <p className="fine-print">
            These checks assess market measures, not the accuracy of
            personalised career advice. Failed checks stay visible in the
            detailed evidence.
          </p>
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
