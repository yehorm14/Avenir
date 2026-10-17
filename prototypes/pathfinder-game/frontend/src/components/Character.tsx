import { LETTERS, TRAIT, className, isFlat, levelFor, ranked, type Profile } from "../game";
import type { Letter } from "../types";

/** A flat, neutral figure (no skin tone). The outfit and accessory come from your top trait,
 *  and a small pin shows your second trait. */
export function Avatar({ profile, size = 120 }: { profile: Profile; size?: number }) {
  const flat = isFlat(profile);
  const [a, b] = ranked(profile);
  const main = flat ? "var(--text-3)" : TRAIT[a].color;
  const second = flat ? null : TRAIT[b];
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 120 138" role="img" aria-label={flat ? "Your character, still taking shape" : `Your character: ${className(profile)}`}>
      <circle cx="60" cy="70" r="58" fill={main} fillOpacity="0.14" />
      <path d="M20 132 C20 102 38 90 60 90 C82 90 100 102 100 132 Z" fill={main} fillOpacity="0.78" />
      <circle cx="60" cy="58" r="25" fill={main} />
      {!flat && a === "R" && (
        <g>
          <path d="M33 52 C33 28 87 28 87 52 Z" fill="#ffcc00" />
          <rect x="29" y="50" width="62" height="7" rx="3.5" fill="#e0b000" />
        </g>
      )}
      {!flat && a === "I" && (
        <g fill="none" stroke="#fff" strokeWidth="3">
          <circle cx="50" cy="58" r="8.5" /><circle cx="70" cy="58" r="8.5" /><line x1="58.5" y1="58" x2="61.5" y2="58" />
          <path d="M44 92 L60 112 L76 92" strokeWidth="4" />
        </g>
      )}
      {!flat && a === "A" && (
        <g>
          <ellipse cx="66" cy="33" rx="24" ry="10" fill="#2b2b30" transform="rotate(-10 66 33)" />
          <circle cx="76" cy="23" r="3.5" fill="#2b2b30" />
          <circle cx="48" cy="104" r="5" fill="#fff" /><circle cx="62" cy="112" r="5" fill="#fff" fillOpacity="0.8" /><circle cx="76" cy="104" r="5" fill="#fff" fillOpacity="0.6" />
        </g>
      )}
      {!flat && a === "S" && (
        <path d="M60 124 C46 112 46 100 54 100 C58 100 60 104 60 104 C60 104 62 100 66 100 C74 100 74 112 60 124 Z" fill="#fff" />
      )}
      {!flat && a === "E" && (
        <g fill="#fff">
          <path d="M44 92 L60 104 L76 92 L72 90 L60 98 L48 90 Z" />
          <path d="M56 100 L64 100 L67 120 L60 128 L53 120 Z" />
        </g>
      )}
      {!flat && a === "C" && (
        <g>
          <path d="M48 92 L60 110 L72 92" fill="none" stroke="#fff" strokeWidth="2.5" />
          <rect x="51" y="110" width="18" height="14" rx="3" fill="#fff" />
          <rect x="55" y="114" width="10" height="2" rx="1" fill={main} /><rect x="55" y="119" width="7" height="2" rx="1" fill={main} />
        </g>
      )}
      {second && b && (
        <g>
          <circle cx="100" cy="26" r="13" fill={second.color} stroke="var(--surface)" strokeWidth="3" />
          <text x="100" y="31" textAnchor="middle" fontSize="13" fontWeight="700" fill="#fff">{b}</text>
        </g>
      )}
    </svg>
  );
}

/** Six stats on a hexagon. `pop` re-triggers the shape's animation after each change. */
export function Hexagon({ profile, size = 240, pop }: { profile: Profile; size?: number; pop?: number }) {
  const cx = 120, cy = 112, R = 70;
  const pt = (i: number, r: number) => {
    const ang = -Math.PI / 2 + (i * Math.PI) / 3;
    return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)] as const;
  };
  const poly = (f: (i: number) => number) => LETTERS.map((_, i) => pt(i, f(i)).map((n) => Math.round(n * 10) / 10).join(",")).join(" ");
  return (
    <svg viewBox="0 0 240 224" width={size} height={size * (224 / 240)} role="img" aria-label="Your six stats">
      {[0.33, 0.66, 1].map((s) => <polygon key={s} points={poly(() => R * s)} fill="none" stroke="var(--line)" strokeWidth="1" />)}
      {LETTERS.map((_, i) => {
        const [x, y] = pt(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--line)" strokeWidth="1" />;
      })}
      <polygon key={pop} className="hex-shape" points={poly((i) => Math.max(4, R * profile[LETTERS[i]]))} fill="var(--accent)" fillOpacity="0.2" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />
      {LETTERS.map((l, i) => {
        const [x, y] = pt(i, R * Math.max(0.04, profile[l]));
        return <circle key={l} cx={x} cy={y} r="4" fill={TRAIT[l].color} stroke="var(--surface)" strokeWidth="2" />;
      })}
      {LETTERS.map((l, i) => {
        const [x, y] = pt(i, R + 22);
        return (
          <text key={l} x={x} y={y + 4} textAnchor="middle" fontSize="12" fontWeight="600" fill="var(--text-2)">
            {TRAIT[l].stat}
          </text>
        );
      })}
    </svg>
  );
}

export function StatBars({ profile }: { profile: Profile }) {
  return (
    <div className="profile">
      {ranked(profile).map((l: Letter) => (
        <div className="pbar" key={l} title={TRAIT[l].tagline}>
          <span>{TRAIT[l].stat}</span>
          <span className="track"><span className="fill" style={{ width: `${Math.round(profile[l] * 100)}%`, display: "block", background: TRAIT[l].color }} /></span>
          <span className="v">{Math.round(profile[l] * 100)}</span>
        </div>
      ))}
    </div>
  );
}

export function XpBar({ xp }: { xp: number }) {
  const lv = levelFor(xp);
  return (
    <div className="xp" aria-label={`Level ${lv.level}, ${lv.name}, ${xp} XP`}>
      <div className="xp-top">
        <span><b>Level {lv.level}</b> · {lv.name}</span>
        <span className="tiny">{lv.next === null ? `${xp} XP` : `${xp} / ${lv.next} XP`}</span>
      </div>
      <div className="xp-track"><div className="xp-fill" style={{ width: `${lv.pct}%` }} /></div>
    </div>
  );
}
