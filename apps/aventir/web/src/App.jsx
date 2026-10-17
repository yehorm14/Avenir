import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Bookmark,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Code2,
  ExternalLink,
  GraduationCap,
  Layers3,
  LoaderCircle,
  Search,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import {
  HiringChart,
  SkillsChart,
  PayChart,
  Sparkline,
  rangePoints,
  number,
  money,
} from "./components/CareerChart.jsx";

async function request(path, options) {
  const response = await fetch(`/api${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Could not load this research. Please try again.",
    );
  return data;
}
function initialSaved() {
  try {
    const value = JSON.parse(localStorage.getItem("aventir.saved") || "[]");
    return Array.isArray(value)
      ? value.filter((id) => typeof id === "string").slice(0, 100)
      : [];
  } catch {
    return [];
  }
}
const titleCase = (s = "") => s.charAt(0).toUpperCase() + s.slice(1);
const formatDate = (s) =>
  s
    ? new Date(s).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Not available";
const chartLabels = {
  hiring: "Industry hiring",
  skills: "Skills",
  pay: "Pay range",
};

export default function App() {
  const [meta, setMeta] = useState(null),
    [health, setHealth] = useState(null);
  const [catalogue, setCatalogue] = useState({ items: [], total: 0 });
  const [career, setCareer] = useState(null),
    [selectedId, setSelectedId] = useState(null);
  const [query, setQuery] = useState(""),
    [group, setGroup] = useState(""),
    [offset, setOffset] = useState(0);
  const [saved, setSaved] = useState(initialSaved),
    [savedCareers, setSavedCareers] = useState([]),
    [view, setView] = useState("all");
  const [loading, setLoading] = useState(true),
    [searching, setSearching] = useState(false),
    [error, setError] = useState("");
  const [mode, setMode] = useState("hiring"),
    [range, setRange] = useState("3Y"),
    [hovered, setHovered] = useState(null);
  const [showSources, setShowSources] = useState(false),
    [showAllSkills, setShowAllSkills] = useState(false);
  const [question, setQuestion] = useState(""),
    [reflection, setReflection] = useState(null),
    [thinking, setThinking] = useState(false),
    [aiError, setAiError] = useState("");
  const browser = useRef(null),
    searchInput = useRef(null),
    aiInput = useRef(null),
    sourcesDialog = useRef(null);
  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;

  useEffect(() => {
    Promise.all([request("/meta"), request("/health")])
      .then(([m, h]) => {
        setMeta(m);
        setHealth(h);
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    let active = true;
    setSearching(true);
    const timer = setTimeout(
      () => {
        const params = new URLSearchParams({
          q: query,
          group,
          offset,
          limit: 8,
        });
        request(`/careers?${params}`)
          .then((data) => {
            if (!active) return;
            setCatalogue(data);
            setError("");
            if (!selectedRef.current && data.items.length)
              setSelectedId(
                (
                  data.items.find(
                    (c) => c.title.toLowerCase() === "software developer",
                  ) || data.items[0]
                ).id,
              );
          })
          .catch((e) => active && setError(e.message))
          .finally(() => {
            if (active) {
              setLoading(false);
              setSearching(false);
            }
          });
      },
      query ? 220 : 0,
    );
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query, group, offset]);
  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    setHovered(null);
    setReflection(null);
    setAiError("");
    setShowAllSkills(false);
    setQuestion("");
    request(`/careers/${encodeURIComponent(selectedId)}`)
      .then((c) => {
        if (!active) return;
        setCareer(c);
        setMode(c.industry ? "hiring" : "skills");
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [selectedId]);
  useEffect(() => {
    try {
      localStorage.setItem("aventir.saved", JSON.stringify(saved));
    } catch {
      /* Browsing still works when storage is unavailable. */
    }
    let active = true;
    Promise.all(
      saved.map((id) =>
        request(`/careers/${encodeURIComponent(id)}`).catch(() => null),
      ),
    ).then((items) => active && setSavedCareers(items.filter(Boolean)));
    return () => {
      active = false;
    };
  }, [saved]);
  useEffect(() => {
    if (showSources) sourcesDialog.current?.showModal();
    else sourcesDialog.current?.close();
  }, [showSources]);

  function toggleSave(id) {
    setSaved((ids) =>
      ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id].slice(-100),
    );
  }
  function openBrowser(nextView = "all") {
    setView(nextView);
    browser.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  async function research(e) {
    e.preventDefault();
    if (!career || thinking) return;
    const id = career.id;
    setThinking(true);
    setAiError("");
    setReflection(null);
    try {
      const result = await request("/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          career_id: id,
          question:
            question ||
            "What should I think about before choosing this career?",
        }),
      });
      if (selectedRef.current === id) setReflection(result);
    } catch (e) {
      if (selectedRef.current === id) setAiError(e.message);
    } finally {
      setThinking(false);
    }
  }

  const points = useMemo(
    () => rangePoints(career?.industry, range),
    [career, range],
  );
  const last = points.at(-1),
    first = points[0];
  const change = first?.value
    ? ((last.value - first.value) / first.value) * 100
    : null;
  const latestPeriod = career?.industry?.period_labels?.[last?.time] || "";
  const selectedSaved = saved.includes(career?.id);
  const list =
    view === "saved"
      ? savedCareers.filter(
          (c) =>
            (!group || c.group === group) &&
            (c.title.toLowerCase().includes(query.toLowerCase()) ||
              (c.aliases || []).some((a) =>
                a.toLowerCase().includes(query.toLowerCase()),
              )),
        )
      : catalogue.items;
  const total = view === "saved" ? list.length : catalogue.total;
  const skillCounts = career
    ? [
        career.essential.filter((s) => s.kind === "skill").length,
        career.essential.filter((s) => s.kind === "knowledge").length,
        career.optional.length,
      ]
    : [];
  const industries = useMemo(
    () => Object.fromEntries((meta?.industries || []).map((s) => [s.id, s])),
    [meta],
  );
  const isMock = health?.mode === "mock" || meta?.mode === "mock";

  return (
    <>
      <a className="skip-link" href="#career-browser">
        Skip to careers
      </a>
      <div className="dark-overview">
        {isMock && (
          <div className="demo-notice" role="status">
            <strong>Demo mode</strong>
            <span>Sample careers and research responses</span>
          </div>
        )}
        <header className="app-header shell">
          <a
            className="brand"
            href="#"
            aria-label="Aventir home"
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          >
            <span className="brand-symbol" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="23" height="23" fill="none">
                <path
                  d="M8.8 8.4h3.7c2.3 0 3.7 1.2 3.7 3.3v6.2M16.2 12H11c-2.1 0-3.4 1.1-3.4 3s1.3 3 3.4 3c2.6 0 4.2-1.5 5.2-3.8"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            aventir
          </a>
          <nav aria-label="Main navigation">
            <button
              className={view === "all" ? "nav-active" : ""}
              onClick={() => openBrowser("all")}
            >
              Explore
            </button>
            <button
              className={view === "saved" ? "nav-active" : ""}
              onClick={() => openBrowser("saved")}
            >
              Shortlist
              {saved.length > 0 && (
                <span className="nav-count">{saved.length}</span>
              )}
            </button>
          </nav>
          <div className="header-right">
            <span className="region">
              <span aria-hidden="true">🇬🇧</span> UK research
            </span>
            <button
              className="source-button"
              aria-label="Data sources"
              onClick={() => setShowSources(true)}
            >
              <Layers3 size={16} /> <span>Data sources</span>
            </button>
          </div>
        </header>

        <main id="main">
          <div className="shell overview-heading">
            <div>
              <h1>Explore your next move.</h1>
            </div>
            <button
              className="quiet-cta"
              onClick={() => {
                openBrowser();
                aiInput.current?.focus({ preventScroll: true });
              }}
            >
              Not sure where to start? <ArrowUpRight size={17} />
            </button>
          </div>
          {error && (
            <div role="alert" className="shell app-error">
              {error}
              <button onClick={() => window.location.reload()}>Retry</button>
            </div>
          )}
          {loading && !career ? (
            <div className="shell loading-state">
              <LoaderCircle className="spin" size={26} /> Loading official
              career research…
            </div>
          ) : career ? (
            <div className="shell overview-grid">
              <section
                className="main-chart dark-widget"
                aria-label={`Research for ${career.title}`}
              >
                <div className="chart-heading">
                  <div className="career-heading">
                    <span
                      className={`career-mark ${career.sector_id || "other"}`}
                      aria-hidden="true"
                    >
                      {career.sector_id === "technology" ? (
                        <Code2 size={21} />
                      ) : (
                        <GraduationCap size={22} />
                      )}
                    </span>
                    <div>
                      <h2>{titleCase(career.title)}</h2>
                      <span>{career.group}</span>
                    </div>
                  </div>
                  <button
                    className={`icon-button save-hero ${selectedSaved ? "is-saved" : ""}`}
                    aria-label={
                      selectedSaved
                        ? "Remove career from shortlist"
                        : "Save career to shortlist"
                    }
                    aria-pressed={selectedSaved}
                    onClick={() => toggleSave(career.id)}
                  >
                    <Bookmark
                      size={20}
                      fill={selectedSaved ? "currentColor" : "none"}
                    />
                  </button>
                </div>
                <div
                  className="chart-tabs"
                  role="tablist"
                  aria-label="Career evidence"
                  onKeyDown={(e) => {
                    if (
                      !["ArrowLeft", "ArrowRight", "Home", "End"].includes(
                        e.key,
                      )
                    )
                      return;
                    e.preventDefault();
                    const tabs = [
                      ...e.currentTarget.querySelectorAll(
                        "button:not(:disabled)",
                      ),
                    ];
                    const index = tabs.indexOf(document.activeElement);
                    const next =
                      e.key === "Home"
                        ? 0
                        : e.key === "End"
                          ? tabs.length - 1
                          : (index +
                              (e.key === "ArrowRight" ? 1 : -1) +
                              tabs.length) %
                            tabs.length;
                    tabs[next]?.focus();
                    tabs[next]?.click();
                  }}
                >
                  {Object.entries(chartLabels).map(([key, label]) => (
                    <button
                      key={key}
                      role="tab"
                      aria-selected={mode === key}
                      tabIndex={mode === key ? 0 : -1}
                      aria-controls="evidence-chart"
                      id={`tab-${key}`}
                      disabled={
                        (key === "hiring" && !career.industry) ||
                        (key === "pay" && !career.salary)
                      }
                      title={
                        key === "hiring" && !career.industry
                          ? "No reviewed UK industry match for this occupation"
                          : key === "pay" && !career.salary
                            ? "UK pay reference not yet matched"
                            : undefined
                      }
                      onClick={() => {
                        setMode(key);
                        setHovered(null);
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <div
                  id="evidence-chart"
                  role="tabpanel"
                  aria-labelledby={`tab-${mode}`}
                >
                  {mode === "hiring" && career.industry && (
                    <>
                      <div className="chart-value">
                        <strong>
                          {number(hovered?.value ?? last?.value ?? 0)}
                        </strong>
                        <div>
                          <span>UK industry vacancies</span>
                          <span className="observation-period">
                            {hovered?.period || latestPeriod}
                          </span>
                        </div>
                      </div>
                      <div
                        className={`change-label ${change !== null && change >= 0 ? "positive" : "negative"}`}
                      >
                        {change !== null && (
                          <>
                            {change >= 0 ? (
                              <ArrowUpRight size={15} />
                            ) : (
                              <ArrowDownLeft size={15} />
                            )}{" "}
                            {Math.abs(change).toFixed(1)}%{" "}
                            <span>
                              over{" "}
                              {range === "ALL"
                                ? "available history"
                                : range.toLowerCase()}
                            </span>
                          </>
                        )}
                      </div>
                      <HiringChart
                        points={points}
                        labels={career.industry.period_labels}
                        onHover={setHovered}
                      />
                      <div className="chart-bottom">
                        <span>{career.industry.name}</span>
                        <div
                          className="range-buttons"
                          aria-label="Chart time range"
                        >
                          {["1Y", "3Y", "5Y", "ALL"].map((r) => (
                            <button
                              className={range === r ? "selected" : ""}
                              key={r}
                              aria-pressed={range === r}
                              onClick={() => {
                                setRange(r);
                                setHovered(null);
                              }}
                            >
                              {r === "ALL" ? "All" : r.toLowerCase()}
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                  {mode === "skills" && (
                    <>
                      <div className="chart-value">
                        <strong>
                          {career.skills_available === false
                            ? "Unavailable"
                            : career.essential.length}
                        </strong>
                        <div>
                          <span>essential skills & knowledge</span>
                          <span className="observation-period">
                            ESCO occupation profile
                          </span>
                        </div>
                      </div>
                      {career.skills_available === false ? (
                        <div className="skills-plot">
                          <p>
                            The official API could not return this profile’s
                            skill relationships. Explore the source profile;
                            missing data is not a zero-skill requirement.
                          </p>
                          <a
                            href={career.source_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open official occupation profile{" "}
                            <ExternalLink size={13} />
                          </a>
                        </div>
                      ) : (
                        <SkillsChart career={career} />
                      )}
                    </>
                  )}
                  {mode === "pay" && career.salary && (
                    <>
                      <div className="chart-value">
                        <strong>
                          {money(career.salary.min)}
                          <span className="value-dash">–</span>
                          {money(career.salary.max)}
                        </strong>
                      </div>
                      <PayChart salary={career.salary} />
                    </>
                  )}
                </div>
                <div className="chart-source">
                  <span className="source-dot" />
                  {isMock && "Sample · "}
                  {mode === "hiring"
                    ? "ONS · Industry context, not a career forecast"
                    : mode === "pay"
                      ? "National Careers Service · England reference"
                      : "European Commission · ESCO"}
                  <button
                    onClick={() => setShowSources(true)}
                    aria-label="Inspect chart sources"
                  >
                    <ExternalLink size={13} />
                  </button>
                </div>
              </section>
              <aside className="metric-stack" aria-label="Career at a glance">
                <button
                  className="dark-widget metric-widget"
                  onClick={() =>
                    career.salary ? setMode("pay") : setShowSources(true)
                  }
                >
                  <span>
                    Annual pay reference <ArrowUpRight size={17} />
                  </span>
                  {career.salary ? (
                    <>
                      <strong>
                        £{number(career.salary.min / 1000)}k <em>–</em> £
                        {number(career.salary.max / 1000)}k
                      </strong>
                      <small>Starter to experienced · England</small>
                    </>
                  ) : (
                    <>
                      <strong className="missing-value">Not yet matched</strong>
                      <small>Explore the official occupation profile</small>
                    </>
                  )}
                </button>
                <button
                  className="dark-widget metric-widget skill-widget"
                  onClick={() => setMode("skills")}
                >
                  <span>
                    What you’d build on <ArrowUpRight size={17} />
                  </span>
                  <div className="skill-metric">
                    <strong>
                      {career.skills_available === false
                        ? "—"
                        : career.essential.length}
                    </strong>
                    <span>
                      essential skills
                      <br />& knowledge areas
                    </span>
                    <div className="mini-bars" aria-hidden="true">
                      {skillCounts.map((n, i) => (
                        <i
                          key={i}
                          style={{
                            height: `${8 + (n / Math.max(1, ...skillCounts)) * 37}px`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  <small>
                    {career.skills_available === false
                      ? "Skill relationships unavailable from source"
                      : "From the ESCO career profile"}
                  </small>
                </button>
                <button
                  className="research-nudge"
                  onClick={() => {
                    openBrowser();
                    aiInput.current?.focus({ preventScroll: true });
                  }}
                >
                  <span className="nudge-icon">
                    <Sparkles size={18} />
                  </span>
                  <span>
                    Find your way in
                    <strong>Start with a question about you</strong>
                  </span>
                  <ChevronRight size={18} />
                </button>
              </aside>
            </div>
          ) : null}
        </main>
      </div>

      <section
        className="career-sheet"
        id="career-browser"
        ref={browser}
        aria-labelledby="careers-title"
      >
        <div className="shell">
          <div className="browser-heading">
            <div>
              <h2 id="careers-title">A world of possibilities</h2>
              <p>
                {meta ? number(meta.occupation_count) : "…"} career profiles.
                One place to start.
              </p>
            </div>
            <span className="coverage-chip">
              <span /> {isMock ? "Sample data" : "Official source data"}
            </span>
          </div>
          <div className="browser-toolbar">
            <div className="browser-tabs" role="group" aria-label="Career list">
              <button
                className={view === "all" ? "active" : ""}
                aria-pressed={view === "all"}
                onClick={() => {
                  setView("all");
                  setOffset(0);
                }}
              >
                All careers
              </button>
              <button
                className={view === "saved" ? "active" : ""}
                aria-pressed={view === "saved"}
                onClick={() => setView("saved")}
              >
                Shortlist <span>{saved.length}</span>
              </button>
            </div>
            <div className="browser-controls">
              <label className="search-box">
                <Search size={17} />
                <input
                  ref={searchInput}
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setOffset(0);
                  }}
                  placeholder="Search careers"
                  aria-label="Search careers"
                />
                {query && (
                  <button
                    className="clear-search"
                    aria-label="Clear career search"
                    onClick={() => {
                      setQuery("");
                      setOffset(0);
                      searchInput.current?.focus();
                    }}
                  >
                    <X size={14} />
                  </button>
                )}
              </label>
              <label className="group-select">
                <SlidersHorizontal size={16} />
                <select
                  value={group}
                  aria-label="Occupation group"
                  onChange={(e) => {
                    setGroup(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All fields</option>
                  {meta?.groups.map((g) => (
                    <option key={g.name} value={g.name}>
                      {g.name} ({number(g.count)})
                    </option>
                  ))}
                </select>
                <ChevronDown size={14} />
              </label>
            </div>
          </div>

          <div className="research-grid">
            <section
              className="career-list"
              aria-label="Career catalogue"
              aria-busy={searching}
            >
              <div className="list-caption">
                <span>{view === "saved" ? "Your shortlist" : "Career"}</span>
                <span>
                  {searching ? "Searching…" : `${number(total)} results`}
                </span>
              </div>
              <div className={`career-rows ${searching ? "is-searching" : ""}`}>
                {list.map((c) => (
                  <div
                    className={`career-row ${career?.id === c.id ? "selected-career" : ""}`}
                    key={c.id}
                  >
                    <button
                      className="select-career"
                      aria-pressed={career?.id === c.id}
                      onClick={() => setSelectedId(c.id)}
                    >
                      <span
                        className={`career-avatar ${c.sector_id || "other"}`}
                        aria-hidden="true"
                      >
                        {c.title
                          .toLowerCase()
                          .split(" ")
                          .filter(Boolean)
                          .slice(0, 2)
                          .map((w) => w[0])
                          .join("")}
                      </span>
                      <span className="career-name">
                        <strong>{titleCase(c.title)}</strong>
                        <small>
                          {c.salary
                            ? `${money(c.salary.min)}–${money(c.salary.max)}`
                            : c.group}
                        </small>
                      </span>
                      {c.sector_id && industries[c.sector_id] ? (
                        <Sparkline points={industries[c.sector_id].points} />
                      ) : (
                        <ChevronRight className="row-chevron" size={16} />
                      )}
                    </button>
                    <button
                      className={`row-save ${saved.includes(c.id) ? "is-saved" : ""}`}
                      aria-label={`${saved.includes(c.id) ? "Remove" : "Save"} ${c.title} ${saved.includes(c.id) ? "from" : "to"} shortlist`}
                      aria-pressed={saved.includes(c.id)}
                      onClick={() => toggleSave(c.id)}
                    >
                      <Bookmark
                        size={16}
                        fill={saved.includes(c.id) ? "currentColor" : "none"}
                      />
                    </button>
                  </div>
                ))}
                {!list.length && !searching && (
                  <div className="empty-state">
                    <Search size={24} />
                    <h3>
                      {view === "saved" && !saved.length
                        ? "Your next move starts here"
                        : "No careers found"}
                    </h3>
                    <p>
                      {view === "saved" && !saved.length
                        ? "Save careers as you explore. They’ll stay in your shortlist on this device."
                        : "Try a broader title or choose a different field."}
                    </p>
                    <button
                      onClick={() => {
                        setQuery("");
                        setGroup("");
                        setOffset(0);
                        setView("all");
                      }}
                    >
                      Explore all careers
                    </button>
                  </div>
                )}
              </div>
              {view === "all" && total > 8 && (
                <div className="pagination">
                  <span>
                    {offset + 1}–{Math.min(offset + 8, total)} of{" "}
                    {number(total)}
                  </span>
                  <div>
                    <button
                      aria-label="Previous career page"
                      disabled={offset === 0 || searching}
                      onClick={() => setOffset((o) => Math.max(0, o - 8))}
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <button
                      aria-label="Next career page"
                      disabled={offset + 8 >= total || searching}
                      onClick={() => setOffset((o) => o + 8)}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </section>

            {career && (
              <>
                <section
                  className="career-detail"
                  aria-label="Selected career details"
                >
                  <div className="detail-heading">
                    <span className="detail-kicker">A closer look</span>
                    <span className="esco-code">ISCO {career.code}</span>
                  </div>
                  <h3>{titleCase(career.title)}</h3>
                  <p className="career-description">
                    {career.description ||
                      "Explore the official occupation profile for details about this work."}
                  </p>
                  <h4>Skills you could develop</h4>
                  {career.skills_available === false && (
                    <p className="career-description">
                      Skill relationships are unavailable from the source for
                      this profile.
                    </p>
                  )}
                  <div className="skill-tags">
                    {(showAllSkills
                      ? career.essential
                      : career.essential.slice(0, 6)
                    ).map((s) => (
                      <span key={s.uri}>{titleCase(s.title)}</span>
                    ))}
                  </div>
                  {career.essential.length > 6 && (
                    <button
                      className="text-button"
                      onClick={() => setShowAllSkills((v) => !v)}
                    >
                      {showAllSkills
                        ? "Show fewer skills"
                        : `See all ${career.essential.length} essential skills`}{" "}
                      <ChevronDown
                        size={14}
                        className={showAllSkills ? "rotate" : ""}
                      />
                    </button>
                  )}
                  <div className="entry-routes">
                    <GraduationCap size={22} />
                    <div>
                      <h4>There’s more than one way in</h4>
                      <p>
                        Explore university, college and apprenticeship routes in
                        official career guidance.
                      </p>
                      <a
                        href={career.salary?.source_url || career.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {career.salary
                          ? "Explore entry routes"
                          : "Open occupation profile"}
                        <ArrowUpRight size={14} />
                      </a>
                      {!career.salary && (
                        <a
                          href="https://www.apprenticeships.gov.uk/apprentices"
                          target="_blank"
                          rel="noreferrer"
                        >
                          Explore apprenticeships in England
                          <ArrowUpRight size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                  <details className="data-table">
                    <summary>View exact chart data</summary>
                    {mode === "hiring" && career.industry ? (
                      <>
                        <p>
                          UK {career.industry.name.toLowerCase()} vacancies;
                          three-month averages. Released{" "}
                          {formatDate(career.industry.release_date)}.
                        </p>
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th scope="col">Period</th>
                                <th scope="col">Vacancies</th>
                              </tr>
                            </thead>
                            <tbody>
                              {points
                                .slice()
                                .reverse()
                                .map((p) => (
                                  <tr key={p.time}>
                                    <td>
                                      {career.industry.period_labels[p.time] ||
                                        p.time}
                                    </td>
                                    <td>{number(p.value)}</td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    ) : mode === "pay" && career.salary ? (
                      <p>
                        Starter: {money(career.salary.min)} per year.
                        Experienced: {money(career.salary.max)} per year.
                        Checked {formatDate(career.salary.checked)}.
                      </p>
                    ) : career.skills_available === false ? (
                      <p>
                        Skill relationships are unavailable from the official
                        source. This does not mean the career has no skill
                        requirements.
                      </p>
                    ) : (
                      <p>
                        Essential skills: {skillCounts[0]}. Essential knowledge:{" "}
                        {skillCounts[1]}. Optional skills and knowledge:{" "}
                        {skillCounts[2]}.
                      </p>
                    )}
                  </details>
                </section>

                <aside
                  className="reflection-panel"
                  aria-labelledby="reflection-title"
                >
                  <div className="reflection-icon">
                    <Sparkles size={19} />
                  </div>
                  <h3 id="reflection-title">Think it through.</h3>
                  <p>
                    You don’t need to have it figured out. Start with what
                    you’re curious about.
                  </p>
                  <form onSubmit={research}>
                    <label htmlFor="research-question">
                      What matters to you?
                    </label>
                    <textarea
                      ref={aiInput}
                      id="research-question"
                      maxLength={600}
                      rows={3}
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="I like problem-solving, but I’m not sure coding is for me…"
                    />
                    <button
                      className="research-button"
                      type="submit"
                      disabled={thinking}
                    >
                      {thinking ? (
                        <>
                          <LoaderCircle size={16} className="spin" /> Thinking…
                        </>
                      ) : (
                        <>
                          <Sparkles size={16} />{" "}
                          {isMock ? "Preview research" : "Explore this career"}
                        </>
                      )}
                    </button>
                  </form>
                  {isMock ? (
                    <p className="ai-status">
                      Sample reflections are available. Live AI is off in this
                      demo.
                    </p>
                  ) : (
                    !health?.ai_configured && (
                      <p className="ai-status">
                        AI reflection is not connected yet. You can still
                        explore the career evidence.
                      </p>
                    )
                  )}
                  {aiError && (
                    <div className="ai-error" role="alert">
                      {aiError}
                    </div>
                  )}
                  {reflection && (
                    <div className="reflection-answer" aria-live="polite">
                      <p>{reflection.summary}</p>
                      <ul>
                        {reflection.considerations.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                      <strong>{reflection.next_question}</strong>
                      <small>
                        {reflection.is_mock
                          ? "Sample reflection for this demo. No live AI was used."
                          : "AI reflection based on this career’s sources. Check the evidence before deciding."}
                      </small>
                    </div>
                  )}
                  <div className="reflection-footer">
                    <Check size={13} />
                    <span>Your choice. Evidence to help you make it.</span>
                  </div>
                </aside>
              </>
            )}
          </div>
          <footer className="page-footer">
            <span className="footer-brand">aventir</span>
            <p>A clearer view of the work you could do.</p>
            <button onClick={() => setShowSources(true)}>
              Sources & coverage <ArrowUpRight size={13} />
            </button>
          </footer>
        </div>
      </section>

      <dialog
        ref={sourcesDialog}
        className="sources-dialog"
        onCancel={() => setShowSources(false)}
        onClose={() => setShowSources(false)}
        onClick={(e) => {
          if (e.target === sourcesDialog.current) setShowSources(false);
        }}
        aria-labelledby="sources-title"
      >
        <div className="dialog-content">
          <button
            className="dialog-close"
            aria-label="Close data sources"
            onClick={() => setShowSources(false)}
          >
            <X size={20} />
          </button>
          <Layers3 size={25} />
          <h2 id="sources-title">The evidence behind the view</h2>
          <p>
            {isMock
              ? "This demo uses a frozen sample of 20 career profiles and historical chart data. The links below identify the original sources."
              : "Different sources answer different questions. Here’s what this screen can tell you."}
          </p>
          <div className="source-record">
            <h3>
              Career profiles & skills <span>European Commission</span>
            </h3>
            <p>
              {number(meta?.occupation_count || 0)} occupations imported from
              the official ESCO API. Essential and optional relationships
              describe the occupation, not your personal fit.
            </p>
            <a href={meta?.esco_source} target="_blank" rel="noreferrer">
              Explore ESCO <ExternalLink size={14} />
            </a>
          </div>
          <div className="source-record">
            <h3>
              Industry hiring history <span>ONS</span>
            </h3>
            <p>
              UK vacancies, in absolute numbers, from monthly observations of
              three-month averages. Industry totals provide context for reviewed
              career matches. They are neither live job adverts nor occupation
              forecasts.
            </p>
            {career?.industry ? (
              <a
                href={career.industry.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {career.industry.name} · released{" "}
                {formatDate(career.industry.release_date)}{" "}
                <ExternalLink size={14} />
              </a>
            ) : (
              <a
                href="https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes"
                target="_blank"
                rel="noreferrer"
              >
                ONS labour market data <ExternalLink size={14} />
              </a>
            )}
          </div>
          <div className="source-record">
            <h3>
              Pay & entry-route guidance <span>National Careers Service</span>
            </h3>
            <p>
              Starter-to-experienced salary references for individually reviewed
              matches. England guidance; actual pay and entry requirements vary.
              Missing pay data stays missing.
            </p>
            <a
              href={
                career?.salary?.source_url ||
                "https://nationalcareers.service.gov.uk/explore-careers"
              }
              target="_blank"
              rel="noreferrer"
            >
              Check official career guidance <ExternalLink size={14} />
            </a>
          </div>
          <p className="import-note">
            Imported {formatDate(meta?.retrieved_at)}.{" "}
            {meta?.enriched_profiles || 0} reviewed UK salary matches. ESCO API
            version is not declared by the source response. Shortlists are saved
            on this device.
          </p>
        </div>
      </dialog>
    </>
  );
}
