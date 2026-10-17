import { useState } from "react";
import { api } from "../api";
import type { DiscoverResponse } from "../types";
import { Avatar, Hexagon } from "../components/Character";
import { className, type Profile } from "../game";

interface Props {
  profile: Profile;
  ready: boolean;
  onStart: () => void;
  onCharacter: () => void;
  onOpen: (soc: string) => void;
  onArcade: () => void;
}

const EXAMPLE: Profile = { R: 0.3, I: 0.92, A: 0.3, S: 0.72, E: 0.4, C: 0.55 };

const STEPS = [
  { n: 1, t: "Create your character", d: "Answer 30 quick questions. Your stats and class grow with every answer." },
  { n: 2, t: "Gear up", d: "Add your region, school subjects and experience. They count as gear." },
  { n: 3, t: "Meet your party", d: "Three careers that fit you, each with a backup, scored on real data." },
  { n: 4, t: "Open the quest map", d: "Degrees, universities, skills, guilds, boss battles and mentors, step by step." },
  { n: 5, t: "Survive events", d: "AI shifts, slumps and surprises. Split your effort and see how your party copes." },
  { n: 6, t: "Play the arcade", d: "Call the year: can you beat our algorithm at spotting growth?" },
];

const ANALYSIS = [
  { t: "Fit", d: "How closely the job matches what you enjoy (O*NET interests).", c: "var(--c-interest)" },
  { t: "Pay", d: "Median pay and the range around it (ONS ASHE).", c: "var(--c-pay)" },
  { t: "Demand", d: "Where the UK is short of people now and by 2035, for your region.", c: "var(--c-future)" },
  { t: "AI exposure", d: "How many of the job's tasks generative AI could change (ILO).", c: "var(--c-ai)" },
  { t: "Confidence", d: "How much the evidence behind each pick can be trusted.", c: "var(--green)" },
  { t: "Backup", d: "A related career with similar strengths but different risks.", c: "var(--c-now)" },
  { t: "Events", d: "Does the pick still hold if AI, pay or your sector go the wrong way?", c: "var(--orange)" },
  { t: "Your path", d: "Degrees, universities, skills, societies and alumni to talk to.", c: "var(--c-head)" },
];

export function Home({ profile, ready, onStart, onCharacter, onOpen, onArcade }: Props) {
  const [text, setText] = useState("");
  const [hits, setHits] = useState<DiscoverResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const shown = ready ? profile : EXAMPLE;

  const find = async () => {
    if (text.trim().length < 3) return;
    setBusy(true);
    try {
      setHits(await api.discover(text));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page">
      <section className="hero-game">
        <div>
          <p className="eyebrow">One app. One clear decision.</p>
          <h1 className="display">
            Build your character.
            <br />
            <span className="gradient">Find your path.</span>
          </h1>
          <p className="lede">
            Answer 30 quick questions to create a character. Meet a party of three careers that fit it, then open a quest map for
            each, with real data under every step.
          </p>
          <div className="row" style={{ marginTop: 30 }}>
            <button className="btn large" onClick={onStart}>{ready ? "Respec your character" : "Create your character"}</button>
            {ready && <button className="btn ghost large" onClick={onCharacter}>Open your character ›</button>}
          </div>
          <div className="reassure" style={{ justifyContent: "flex-start" }}>
            <span>About 3 minutes</span>
            <span>No account</span>
            <span>Nothing stored on our servers</span>
          </div>
        </div>
        <div className="card hero-char" aria-label={ready ? "Your character" : "An example character"}>
          <Avatar profile={shown} size={120} />
          <div className="creator-name">{className(shown)}</div>
          <div className="tiny">{ready ? "Your character" : "Example character"}</div>
          <Hexagon profile={shown} size={240} />
        </div>
      </section>

      <div className="section-title">
        <h2 className="title">How the game works.</h2>
        <p className="lede">Six steps, from "I don't know" to a plan you can start this month.</p>
      </div>
      <div className="grid-3">
        {STEPS.map((s) => (
          <div className="card signal" key={s.n}>
            <div className="step-n">{s.n}</div>
            <h3 className="h3" style={{ marginTop: 12 }}>{s.t}</h3>
            <p className="small muted" style={{ margin: "8px 0 0" }}>{s.d}</p>
          </div>
        ))}
      </div>

      <div className="section-title">
        <h2 className="title">Real analysis under the game.</h2>
        <p className="lede">The fun is a skin. Every number is sourced, and the downside is as plain as the upside.</p>
      </div>
      <div className="grid-4">
        {ANALYSIS.map((s) => (
          <div className="card signal" key={s.t}>
            <span className="dot" style={{ background: s.c, width: 10, height: 10, borderRadius: "50%", display: "inline-block" }} />
            <h3 className="h3" style={{ marginTop: 12 }}>{s.t}</h3>
            <p className="small muted" style={{ margin: "8px 0 0" }}>{s.d}</p>
          </div>
        ))}
      </div>

      <div className="section-title">
        <h2 className="title">Not sure where to start?</h2>
        <p className="lede">Describe something you enjoyed doing, in your own words.</p>
      </div>
      <div className="card discover" style={{ maxWidth: 720, margin: "0 auto" }}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="For example: I spent the summer fixing up an old bike and loved working out what was wrong with it"
          maxLength={400}
          aria-label="Describe something you enjoyed"
        />
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="tiny">Sent once to match careers, never stored.</span>
          <button className="btn small" onClick={find} disabled={busy || text.trim().length < 3}>
            {busy ? "Matching…" : "Find careers"}
          </button>
        </div>
        {hits && (
          <div className="hits">
            {hits.hits.length === 0 && <p className="muted small">No close matches. Try describing what you did, not the job title.</p>}
            {hits.hits.slice(0, 3).map((h) => (
              <div className="hit" key={h.soc}>
                <span>
                  <b>{h.title}</b>
                  <span className="tiny" style={{ display: "block" }}>Matched on: {h.matched.join(", ")}</span>
                </span>
                <button className="btn ghost small" onClick={() => onOpen(h.soc)}>Look ›</button>
              </div>
            ))}
            <p className="tiny" style={{ margin: 0 }}>A quick lead, not a ranking. Create your character for your full analysis.</p>
          </div>
        )}
      </div>

      <div className="section-title">
        <h2 className="title">We grade ourselves.</h2>
        <p className="lede">
          In the arcade you play against our algorithm using past years' data. No peeking ahead, for you or for us.
        </p>
        <button className="btn soft" style={{ marginTop: 22 }} onClick={onArcade}>Call the year ›</button>
      </div>

      <div className="grid-3">
        <div className="card">
          <h3 className="h3">XP comes from evidence</h3>
          <p className="small muted">You level up by doing real things, like a first-aid course or a volunteering visit, never by time spent here.</p>
        </div>
        <div className="card">
          <h3 className="h3">Interest comes first</h3>
          <p className="small muted">A career that doesn't fit your interests is never shown, however well it pays. Your class is a label for today, not a verdict.</p>
        </div>
        <div className="card">
          <h3 className="h3">AI explains, never decides</h3>
          <p className="small muted">The ranking is a fixed formula. AI only helps explain it, and must cite its evidence.</p>
        </div>
      </div>

      <div className="card persona" style={{ marginTop: 96 }}>
        <div className="avatar">E</div>
        <div>
          <p className="small muted" style={{ margin: 0 }}>Made for people like Ellie</p>
          <p style={{ margin: "4px 0 0", fontSize: 19, fontWeight: 500 }}>
            16, in S5 in Glasgow, and not sure what to put on her UCAS form. She leaves with a character, a party of three
            careers, a backup for each, and one quest to start this month.
          </p>
        </div>
      </div>
    </main>
  );
}
