import { Avatar, Hexagon, StatBars, XpBar } from "../components/Character";
import { TRAIT, className, isFlat, ranked, readXp, type Profile } from "../game";

interface Props {
  profile: Profile;
  region: string;
  subjects: string[];
  skills: string[];
  onParty: () => void;
  onGear: () => void;
  onRespec: () => void;
}

export function CharacterScreen({ profile, region, subjects, skills, onParty, onGear, onRespec }: Props) {
  const flat = isFlat(profile);
  const top = ranked(profile).slice(0, 3);
  const gear = [...subjects, ...skills];
  return (
    <main className="page">
      <p className="eyebrow">Character created</p>
      <div className="char-hero">
        <div className="char-avatar"><Avatar profile={profile} size={170} /></div>
        <div>
          <p className="small muted" style={{ margin: 0 }}>Your class</p>
          <h1 className="title">{flat ? "Still taking shape" : className(profile)}</h1>
          <p className="lede" style={{ marginTop: 10 }}>
            {flat
              ? "Your answers were all the same, so we can't tell your traits apart yet. Respec and use the full scale."
              : `You lean ${TRAIT[top[0]].tagline.toLowerCase()}, with a ${TRAIT[top[1]].tagline.toLowerCase()} streak. A class is a label for your interests today, not a verdict, and you can respec any time.`}
          </p>
          <div className="row" style={{ marginTop: 22 }}>
            <button className="btn large" onClick={onParty} disabled={flat}>Meet your party</button>
            <button className="btn ghost large" onClick={onGear}>Gear up first ›</button>
          </div>
        </div>
      </div>

      <div className="two" style={{ marginTop: 40 }}>
        <div className="card" style={{ display: "grid", justifyItems: "center", gap: 6, alignSelf: "start" }}>
          <h2 className="h3" style={{ justifySelf: "start" }}>Stats</h2>
          <Hexagon profile={profile} size={280} />
        </div>
        <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
          <div className="card">
            <h2 className="h3" style={{ marginBottom: 14 }}>Traits</h2>
            <StatBars profile={profile} />
          </div>
          <div className="card" style={{ display: "grid", gap: 12 }}>
            <h2 className="h3">Level</h2>
            <XpBar xp={readXp()} />
            <p className="tiny" style={{ margin: 0 }}>XP comes only from real-world evidence you tick off, like a certificate or a volunteering visit, never from time spent here.</p>
          </div>
          <div className="card" style={{ display: "grid", gap: 10 }}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h2 className="h3">Gear</h2>
              <button className="btn ghost small" onClick={onGear}>Edit</button>
            </div>
            <div className="pills">
              <span className="tag blue">{region === "UK-wide" ? "Anywhere in the UK" : region}</span>
              {gear.length === 0 && <span className="small muted">No gear yet: add subjects and experience.</span>}
              {gear.map((g) => <span className="tag" key={g}>{g}</span>)}
            </div>
          </div>
        </div>
      </div>

      <div className="row" style={{ marginTop: 28 }}>
        <button className="btn soft small" onClick={onRespec}>Respec: retake the quiz</button>
      </div>
    </main>
  );
}
