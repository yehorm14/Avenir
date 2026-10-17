import { useEffect, useMemo, useState } from "react";
import type { Quiz } from "../types";
import { Avatar, Hexagon } from "../components/Character";
import { TRAIT, className, isFlat, profileFrom } from "../game";

interface Props {
  quiz: Quiz;
  answers: Record<string, number>;
  onAnswer: (id: string, value: number) => void;
  onDone: () => void;
  onExit: () => void;
}

const MIN_TO_FINISH = 20;
const FACE = ["Not me", "Nope", "Maybe", "Like it", "Love it"];

export function QuizScreen({ quiz, answers, onAnswer, onDone, onExit }: Props) {
  const firstOpen = quiz.items.findIndex((it) => answers[it.id] === undefined);
  const [i, setI] = useState(firstOpen === -1 ? 0 : firstOpen);
  const [flash, setFlash] = useState<{ key: number; text: string; up: boolean } | null>(null);
  const item = quiz.items[i];
  const answered = quiz.items.filter((it) => answers[it.id] !== undefined).length;
  const profile = useMemo(() => profileFrom(answers, quiz.items), [answers, quiz.items]);
  const shaped = answered >= 6 && !isFlat(profile);

  const choose = (v: number) => {
    onAnswer(item.id, v);
    if (v !== 3) setFlash({ key: Date.now(), text: `${TRAIT[item.type].stat} ${v > 3 ? "grew" : "dipped"}`, up: v > 3 });
    window.setTimeout(() => {
      if (i < quiz.items.length - 1) setI(i + 1);
      else onDone();
    }, 170);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const n = Number(e.key);
      if (n >= 1 && n <= 5) choose(n);
      else if ((e.key === "Backspace" || e.key === "ArrowLeft") && i > 0) setI(i - 1);
      else if (e.key === "ArrowRight" && answers[item.id] !== undefined && i < quiz.items.length - 1) setI(i + 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <main className="creator">
      <div className="quiz-top" style={{ maxWidth: 980, margin: "0 auto 14px" }}>
        <button className="btn ghost small" onClick={() => (i > 0 ? setI(i - 1) : onExit())}>‹ {i > 0 ? "Back" : "Home"}</button>
        <span className="small muted">Creating your character · <span style={{ fontVariantNumeric: "tabular-nums" }}>{i + 1} of {quiz.items.length}</span></span>
        <button className="btn ghost small" onClick={onDone} disabled={answered < MIN_TO_FINISH} title={`Answer at least ${MIN_TO_FINISH} to finish early`}>Finish</button>
      </div>
      <div className="progress" aria-hidden style={{ maxWidth: 980, margin: "0 auto 28px" }}>
        <div style={{ width: `${(answered / quiz.items.length) * 100}%` }} />
      </div>

      <div className="creator-grid">
        <aside className="card creator-preview" aria-live="polite">
          <Avatar profile={profile} size={104} />
          <div className="creator-class">
            <div className="tiny">Your class</div>
            <div className="creator-name">{shaped ? className(profile) : "Taking shape…"}</div>
          </div>
          <Hexagon profile={profile} size={230} pop={answered} />
          <p className="tiny" style={{ margin: 0, textAlign: "center" }}>Your stats grow with every answer.</p>
        </aside>

        <section className="creator-main">
          <div className="question" key={item.id}>
            <p className="prompt">Would you enjoy this?</p>
            <h1>{item.text}</h1>
          </div>
          <div className="flash-slot">
            {flash && <span key={flash.key} className={`flash ${flash.up ? "up" : "down"}`}>{flash.up ? "▲" : "▼"} {flash.text}</span>}
          </div>
          <div className="scale" role="radiogroup" aria-label="Your answer">
            {quiz.scale.map((label, idx) => {
              const v = idx + 1;
              return (
                <button
                  key={label}
                  role="radio"
                  aria-checked={answers[item.id] === v}
                  aria-label={label}
                  className={answers[item.id] === v ? "selected" : ""}
                  onClick={() => choose(v)}
                >
                  <span className="pip" />
                  {FACE[idx]}
                </button>
              );
            })}
          </div>
          <p className="keys">Tip: press <kbd>1</kbd> to <kbd>5</kbd> to answer, <kbd>←</kbd> to go back</p>
        </section>
      </div>
    </main>
  );
}
