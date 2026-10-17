import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { Check, nationOf } from "./components/ui";
import { profileFrom, type Profile } from "./game";
import { About } from "./screens/About";
import { Advisers } from "./screens/Advisers";
import { Arcade } from "./screens/Arcade";
import { Career } from "./screens/Career";
import { CharacterScreen } from "./screens/CharacterScreen";
import { Home } from "./screens/Home";
import { Path } from "./screens/Path";
import { Proof } from "./screens/Proof";
import { PayScreen } from "./screens/Pay";
import { QuizScreen } from "./screens/QuizScreen";
import { RadarScreen } from "./screens/Radar";
import { Results } from "./screens/Results";
import { Trust } from "./screens/Trust";
import { Watchlist } from "./screens/Watchlist";
import { DEFAULT_WEIGHTS, MAX_WATCH, clearAll, useHashRoute, usePersistent, type Watched } from "./store";
import type { MatchRequest, MatchResponse, Quiz, Weights } from "./types";

// A character needs a fair spread of answers. 20 of 30 gives about three per trait.
const MIN_ANSWERS = 20;
const ZERO: Profile = { R: 0, I: 0, A: 0, S: 0, E: 0, C: 0 };

const NAV = [
  { id: "character", label: "Character" },
  { id: "party", label: "Party" },
  { id: "radar", label: "Radar" },
  { id: "pay", label: "Pay" },
  { id: "arcade", label: "Arcade" },
];

export default function App() {
  const [route, go] = useHashRoute();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = usePersistent<Record<string, number>>("cp.answers.v2", {});
  const [subjects, setSubjects] = usePersistent<string[]>("cp.subjects", []);
  const [skills, setSkills] = usePersistent<string[]>("cp.skills", []);
  const [region, setRegion] = usePersistent<string>("cp.region", "UK-wide");
  const [storedWeights, setWeights] = usePersistent<Weights>("cp.weights.v2", DEFAULT_WEIGHTS);
  const [watch, setWatch] = usePersistent<Watched[]>("cp.watch", []);
  const [homeNation, setHomeNation] = usePersistent<string>("cp.nation", "");
  const [partyFields, setPartyFields] = usePersistent<string[]>("cp.party.fields", []);
  const [partySocs, setPartySocs] = usePersistent<string[]>("cp.party.socs", []);
  const [paySocs, setPaySocs] = usePersistent<string[] | null>("cp.pay.socs", null);
  const [result, setResult] = useState<MatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cameFrom = useRef<string>("results");

  const weights = useMemo(() => ({ ...DEFAULT_WEIGHTS, ...storedWeights }), [storedWeights]);
  const page = route[0] ?? "";
  const ready = Object.keys(answers).length >= MIN_ANSWERS;
  const profile = useMemo(() => (quiz ? profileFrom(answers, quiz.items) : ZERO), [quiz, answers]);
  const nation = homeNation || nationOf(region);

  useEffect(() => {
    api.quiz().then(setQuiz, (e) => setError(String(e.message ?? e)));
  }, []);

  const request: MatchRequest | null = useMemo(
    () => (ready ? { answers, subjects, skills, region, weights, limit: 3 } : null),
    [ready, answers, subjects, skills, region, weights],
  );

  // Re-score whenever inputs change. Debounced so sliders feel instant but stay cheap.
  useEffect(() => {
    if (!request || page !== "results") return;
    const t = window.setTimeout(() => {
      api.match(request).then(
        (r) => { setResult(r); setError(null); },
        (e) => setError(String(e.message ?? e)),
      );
    }, 180);
    return () => window.clearTimeout(t);
  }, [request, page]);

  // Remember which fields your party covers, so the radar opens on them.
  useEffect(() => {
    const fams = Array.from(new Set((result?.results ?? []).map((r) => r.family).filter(Boolean)));
    if (fams.length && fams.join() !== partyFields.join()) setPartyFields(fams);
    const socs = (result?.results ?? []).map((r) => r.soc);
    if (socs.length && socs.join() !== partySocs.join()) setPartySocs(socs);
  }, [result]);

  const toggleWatch = async (soc: string, title: string) => {
    if (watch.some((w) => w.soc === soc)) {
      setWatch(watch.filter((w) => w.soc !== soc));
      return;
    }
    if (watch.length >= MAX_WATCH) return;
    let edition = "";
    try {
      edition = (await api.changes([soc])).latest_edition;
    } catch { /* offline: we still follow, the edition fills in later */ }
    setWatch((list) => [...list.filter((w) => w.soc !== soc), { soc, title, edition }].slice(0, MAX_WATCH));
  };

  const remember = () => {
    if (page !== "career" && page !== "path") cameFrom.current = page || "home";
  };
  const openCareer = (soc: string) => { remember(); go(`career/${soc}`); };
  const openPath = (soc: string) => { remember(); go(`path/${soc}`); };
  const openPay = (soc: string) => {
    remember();
    setPaySocs([soc, ...(paySocs ?? partySocs).filter((s) => s !== soc)].slice(0, 4));
    go("pay");
  };

  const respec = () => { setAnswers({}); setResult(null); go("quiz"); };
  const toCharacter = () => go(ready ? "character" : "");
  const toParty = () => go(ready ? "results" : "");
  const watching = watch.map((w) => w.soc);
  const backTo = cameFrom.current;
  const backLabel = ({ results: "Your party", watchlist: "Watchlist", proof: "Proof", advisers: "Advisers", arcade: "Arcade", radar: "Radar", pay: "Pay", home: "Home", "": "Home" } as Record<string, string>)[backTo] ?? "Back";
  const goBack = () => go(backTo === "home" ? "" : backTo === "results" && !ready ? "" : backTo);

  let body: JSX.Element;
  if (page === "quiz" && quiz) {
    body = (
      <QuizScreen
        quiz={quiz}
        answers={answers}
        onAnswer={(id, v) => setAnswers((a) => ({ ...a, [id]: v }))}
        onDone={() => go("character")}
        onExit={() => go("")}
      />
    );
  } else if (page === "character" && ready) {
    body = (
      <CharacterScreen
        profile={profile}
        region={region}
        subjects={subjects}
        skills={skills}
        onParty={() => go("results")}
        onGear={() => go("about")}
        onRespec={respec}
      />
    );
  } else if (page === "about" && quiz) {
    body = (
      <About
        region={region}
        regions={quiz.regions}
        onRegion={setRegion}
        subjects={subjects}
        skills={skills}
        allSubjects={quiz.subjects}
        allSkills={quiz.skills}
        onChange={(s, k) => { setSubjects(s); setSkills(k); }}
        onDone={() => go("results")}
        onBack={() => go(ready ? "character" : "quiz")}
      />
    );
  } else if (page === "results" && ready) {
    body = (
      <Results
        result={result}
        error={error}
        weights={weights}
        onWeights={setWeights}
        region={region}
        watching={watching}
        onToggleWatch={toggleWatch}
        onOpen={openCareer}
        onPath={openPath}
        onPay={openPay}
        onRadar={() => go("radar")}
        onRetake={respec}
        onEditAbout={() => go("about")}
      />
    );
  } else if (page === "career" && route[1]) {
    body = (
      <Career
        soc={route[1]}
        request={request}
        watching={watching}
        onToggleWatch={toggleWatch}
        onOpen={openCareer}
        onPath={openPath}
        onPay={openPay}
        onProof={() => go("proof")}
        onBack={goBack}
        backLabel={backLabel}
      />
    );
  } else if (page === "path" && route[1]) {
    body = (
      <Path
        key={route[1]}
        soc={route[1]}
        nation={nation}
        onNation={setHomeNation}
        onAnalysis={openCareer}
        onOpen={openPath}
        onCharacter={toCharacter}
        request={request}
        profile={profile}
        onBack={goBack}
        backLabel={backLabel}
      />
    );
  } else if (page === "pay") {
    body = <PayScreen partySocs={partySocs} onPath={openPath} />;
  } else if (page === "radar") {
    body = <RadarScreen partyFields={partyFields} nation={nation} onNation={setHomeNation} onPath={openPath} onCharacter={toCharacter} />;
  } else if (page === "arcade") {
    body = <Arcade onProof={() => { cameFrom.current = "arcade"; go("proof"); }} />;
  } else if (page === "watchlist") {
    body = <Watchlist list={watch} onOpen={openCareer} onRemove={(soc) => setWatch(watch.filter((w) => w.soc !== soc))} onExplore={toParty} />;
  } else if (page === "proof") {
    body = <Proof onOpen={openCareer} />;
  } else if (page === "advisers") {
    body = <Advisers region={region} onOpen={openCareer} />;
  } else if (page === "trust" || page === "sources") {
    body = (
      <Trust
        onClear={() => {
          clearAll();
          setAnswers({}); setSubjects([]); setSkills([]); setRegion("UK-wide"); setWeights(DEFAULT_WEIGHTS); setWatch([]);
          setHomeNation(""); setResult(null);
        }}
      />
    );
  } else {
    body = <Home profile={profile} ready={ready} onStart={() => go("quiz")} onCharacter={() => go("character")} onOpen={openCareer} onArcade={() => go("arcade")} />;
  }

  const section = (() => {
    if (page === "career" || page === "path") return ["watchlist", "proof", "advisers", "arcade", "radar", "pay"].includes(backTo) ? (backTo === "proof" || backTo === "arcade" ? "arcade" : backTo === "advisers" ? "" : backTo) : "party";
    if (["quiz", "character", "about"].includes(page)) return "character";
    if (page === "results") return "party";
    if (page === "arcade" || page === "proof") return "arcade";
    if (page === "radar") return "radar";
    if (page === "pay") return "pay";
    if (page === "advisers" || page === "sources" || page === "trust") return "";
    return page;
  })();

  const navTo = (id: string) => {
    if (id === "character") toCharacter();
    else if (id === "party") toParty();
    else go(id);
  };

  return (
    <>
      {page !== "quiz" && (
        <nav className="nav">
          <div className="nav-inner">
            <button className="brand" onClick={() => go("")} aria-label="Pathfinder home">
              <span className="brand-mark"><Check /></span>
              <span className="hide-sm">Pathfinder</span>
            </button>
            <div className="nav-links">
              {NAV.map((n) => (
                <button key={n.id} className={`nav-link ${section === n.id ? "active" : ""}`} onClick={() => navTo(n.id)}>
                  {n.label}
                  {n.id === "watchlist" && watch.length > 0 && <span className="count">{watch.length}</span>}
                </button>
              ))}
            </div>
          </div>
        </nav>
      )}
      {!quiz && error ? (
        <main className="page narrow">
          <div className="notice warn">The app can't reach its backend ({error}). Start it with <code>./run.sh</code> in the project folder, keep that terminal open, then refresh this page.</div>
        </main>
      ) : (
        body
      )}
      {page !== "quiz" && (
        <footer className="footer">
          <div className="footer-inner">
            <span>Demo snapshot. Figures are illustrative until checked against each source; the track record is synthetic.</span>
            <span>
              <button className="btn ghost small" style={{ padding: 0, fontSize: 12 }} onClick={() => go("watchlist")}>Watchlist{watch.length > 0 ? ` (${watch.length})` : ""}</button>
              {" · "}
              <button className="btn ghost small" style={{ padding: 0, fontSize: 12 }} onClick={() => go("trust")}>Trust and sources</button>
              {" · "}
              <button className="btn ghost small" style={{ padding: 0, fontSize: 12 }} onClick={() => go("proof")}>Proof</button>
              {" · "}
              <button className="btn ghost small" style={{ padding: 0, fontSize: 12 }} onClick={() => go("advisers")}>For advisers</button>
              {" · Careers guidance, not financial advice."}
            </span>
          </div>
        </footer>
      )}
    </>
  );
}
