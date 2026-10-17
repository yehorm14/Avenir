interface Props {
  region: string;
  regions: string[];
  onRegion: (r: string) => void;
  subjects: string[];
  skills: string[];
  allSubjects: string[];
  allSkills: string[];
  onChange: (subjects: string[], skills: string[]) => void;
  onDone: () => void;
  onBack: () => void;
}

function toggle(list: string[], v: string) {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
}

export function About({ region, regions, onRegion, subjects, skills, allSubjects, allSkills, onChange, onDone, onBack }: Props) {
  return (
    <main className="page narrow">
      <button className="back" onClick={onBack}>‹ Character</button>
      <p className="eyebrow">Gear up</p>
      <h1 className="title">Gear up.</h1>
      <p className="lede">Your region sets the map and sharpens the demand picture. Your subjects and experience are your gear: they give you a head start. Pick as many as you like, or none.</p>

      <section className="sec" style={{ marginTop: 44 }}>
        <h2 className="h3" style={{ marginBottom: 6 }}>Where do you want to work?</h2>
        <p className="small muted" style={{ margin: "0 0 14px" }}>Demand differs across the UK, and so do the routes in.</p>
        <select className="select" value={region} onChange={(e) => onRegion(e.target.value)} aria-label="Nation or region">
          {regions.map((r) => (
            <option key={r} value={r}>{r === "UK-wide" ? "Anywhere in the UK" : r}</option>
          ))}
        </select>
      </section>

      <section className="sec" style={{ marginTop: 40 }}>
        <h2 className="h3" style={{ marginBottom: 14 }}>Subjects you study or enjoy</h2>
        <div className="chips">
          {allSubjects.map((s) => (
            <button key={s} className={`chip ${subjects.includes(s) ? "on" : ""}`} aria-pressed={subjects.includes(s)} onClick={() => onChange(toggle(subjects, s), skills)}>
              {s}
            </button>
          ))}
        </div>
      </section>

      <section className="sec" style={{ marginTop: 40 }}>
        <h2 className="h3" style={{ marginBottom: 14 }}>Skills and experience</h2>
        <div className="chips">
          {allSkills.map((s) => (
            <button key={s} className={`chip ${skills.includes(s) ? "on" : ""}`} aria-pressed={skills.includes(s)} onClick={() => onChange(subjects, toggle(skills, s))}>
              {s}
            </button>
          ))}
        </div>
      </section>

      <div className="row" style={{ marginTop: 52 }}>
        <button className="btn large" onClick={onDone}>Meet my party</button>
        <span className="small muted">{subjects.length + skills.length} selected</span>
      </div>
    </main>
  );
}
