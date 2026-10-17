import { useEffect, useRef, useState } from "react";
import type { Career, Weights } from "./types";
import { api } from "./store";
import "./discovery.css";

export type DiscoveryDraft = { answers: Record<string, string>; step: number };
export type DiscoveryResult = {
  results: Career[];
  tags: string[];
  target_soc: string | null;
  profile_summary: string;
  notices: string[];
  method: string;
  weights: Weights;
};
type Props = {
  mode: "known" | "explore";
  careers: Career[];
  draft: DiscoveryDraft;
  onDraft: (draft: DiscoveryDraft) => void;
  onComplete: (result: DiscoveryResult) => void;
  onBack: () => void;
};
type Question = {
  id: string;
  label: string;
  text: string;
  hint: string;
  chips: string[];
};
const unsure = "I'm not sure yet";
const short = (answer: string) =>
  answer.length > 90 ? `${answer.slice(0, 87).trimEnd()}…` : answer;
const acknowledgement = (answer: string, id: string) => {
  if (answer === unsure) return "We can leave that open for now.";
  const subject: Record<string, string> = {
    direction: "your starting direction",
    interests: "what interests you",
    subjects: "your subjects",
    values: "what matters to you",
    skills: "the strengths you mentioned",
  };
  return `I’ll include ${subject[id] ?? "that context"}: “${short(answer)}”.`;
};

export default function Discovery({
  mode,
  careers,
  draft,
  onDraft,
  onComplete,
  onBack,
}: Props) {
  const questions: Question[] = [
    ...(mode === "known"
      ? [
          {
            id: "direction",
            label: "Your direction",
            text: "What career or area are you thinking about?",
            hint: "A job title, an industry or a rough idea is enough. You can name more than one.",
            chips: careers.slice(0, 5).map((c) => c.title),
          },
        ]
      : []),
    {
      id: "interests",
      label: "Your interests",
      text:
        mode === "known"
          ? "What draws you to that direction, and what do you enjoy doing?"
          : "When do you feel most interested in what you’re doing?",
      hint: "Think about a lesson, project, hobby or moment you enjoyed. What part held your attention?",
      chips: [
        "Solving a tricky problem",
        "Making or designing something",
        "Helping someone learn",
        "Organising a team",
        "Working with numbers",
      ],
    },
    {
      id: "subjects",
      label: "Your subjects",
      text: "Which subjects are you studying, or have you enjoyed most?",
      hint: "Tell me what you like about them. You can mention subjects you’re considering too.",
      chips: [
        "Maths",
        "Computing",
        "Physics",
        "Art and design",
        "Biology",
        "Business or economics",
        "English and humanities",
      ],
    },
    {
      id: "values",
      label: "What matters",
      text: "What would make a career feel worthwhile to you?",
      hint: "You can care about several things. Tell me if one matters more, or if there’s something you want to avoid.",
      chips: [
        "Enjoying the daily work",
        "Good pay",
        "Long-term demand",
        "A manageable schedule",
        "Making a useful impact",
        "Room to keep learning",
      ],
    },
    {
      id: "skills",
      label: "Your strengths",
      text: "What skills or personal strengths would you like to use or develop?",
      hint: "Include practical skills and how you work with people. Examples from school, hobbies or part-time work count; you don’t need experience yet.",
      chips: [
        "Coding or digital tools",
        "Maths and data",
        "Drawing or design",
        "Listening and explaining",
        "Practical problem-solving",
        "Teamwork",
      ],
    },
  ];
  const step = Math.max(0, Math.min(draft.step, questions.length));
  const question = questions[step];
  const complete = step === questions.length;
  const [answer, setAnswer] = useState(
    question ? (draft.answers[question.id] ?? "") : "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef<AbortController | null>(null);
  const mounted = useRef(true);
  const composer = useRef<HTMLTextAreaElement>(null);
  const current = useRef<HTMLDivElement>(null);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      request.current?.abort();
    };
  }, []);
  useEffect(() => {
    setAnswer(question ? (draft.answers[question.id] ?? "") : "");
    setError("");
    if (step > 0) current.current?.scrollIntoView({ block: "nearest" });
    composer.current?.focus({ preventScroll: true });
  }, [step, mode]);

  function send() {
    if (!question || !answer.trim() || busy) return;
    onDraft({
      answers: { ...draft.answers, [question.id]: answer.trim() },
      step: step + 1,
    });
  }
  function editPrevious() {
    request.current?.abort();
    setBusy(false);
    setError("");
    onDraft({ ...draft, step: Math.max(0, step - 1) });
  }
  async function findCareers() {
    if (busy) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    try {
      const result = await api<DiscoveryResult>(
        "discovery",
        { mode, answers: draft.answers },
        controller.signal,
      );
      if (mounted.current && !controller.signal.aborted) onComplete(result);
    } catch (cause) {
      if (mounted.current && !controller.signal.aborted)
        setError(
          cause instanceof Error
            ? cause.message
            : "We couldn’t compare your answers. Please try again.",
        );
    } finally {
      if (mounted.current && !controller.signal.aborted) setBusy(false);
    }
  }
  const chips = question ? [...question.chips, unsure] : [];
  const chosen = answer.split(/\s*;\s*/).filter(Boolean);

  return (
    <section
      className="discovery-conversation"
      aria-labelledby="discovery-title"
    >
      <button className="discovery-back" onClick={onBack}>
        ← Choose a different starting point
      </button>
      <header className="discovery-intro">
        <h1 id="discovery-title">
          {mode === "known"
            ? "Let’s explore your direction."
            : "Let’s find a starting point."}
        </h1>
        <p>A few questions about you, then three careers worth exploring.</p>
      </header>
      <div className="discovery-layout">
        <div className="discovery-chat-column">
          <div className="discovery-guide-identity">
            <span aria-hidden="true">a</span>
            <div>
              <strong>Aventier guide</strong>
              <small>Guided conversation</small>
            </div>
          </div>
          <div
            className="discovery-transcript"
            role="log"
            aria-label="Your career discovery conversation"
          >
            {questions.slice(0, step).map((q, i) => (
              <div className="discovery-exchange" key={q.id}>
                <div className="discovery-guide-message">
                  {i > 0 && (
                    <p className="discovery-acknowledgement">
                      {acknowledgement(
                        draft.answers[questions[i - 1].id] ?? unsure,
                        questions[i - 1].id,
                      )}
                    </p>
                  )}
                  <p>{q.text}</p>
                </div>
                <div className="discovery-user-message">
                  <span className="discovery-sr-only">You: </span>
                  {draft.answers[q.id] ?? unsure}
                </div>
              </div>
            ))}
          </div>
          <div className="discovery-current" ref={current}>
            {step > 0 && (
              <p className="discovery-acknowledgement">
                {acknowledgement(
                  draft.answers[questions[step - 1].id] ?? unsure,
                  questions[step - 1].id,
                )}
              </p>
            )}
            {question ? (
              <>
                <h2 id="discovery-question">{question.text}</h2>
                <p className="discovery-question-hint">{question.hint}</p>
                <div
                  className="discovery-quick-replies"
                  aria-label="Ideas to add to your answer"
                >
                  {chips.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      aria-pressed={chosen.includes(chip)}
                      onClick={() =>
                        setAnswer((previous) => {
                          const parts = previous
                            .split(/\s*;\s*/)
                            .filter(Boolean);
                          if (chip === unsure)
                            return parts.includes(unsure) ? "" : unsure;
                          return (
                            parts.includes(chip)
                              ? parts.filter((part) => part !== chip)
                              : [
                                  ...parts.filter((part) => part !== unsure),
                                  chip,
                                ]
                          ).join("; ");
                        })
                      }
                    >
                      {chip}
                    </button>
                  ))}
                </div>
                <form
                  className="discovery-composer"
                  onSubmit={(event) => {
                    event.preventDefault();
                    send();
                  }}
                >
                  <label htmlFor="discovery-answer">Your answer</label>
                  <textarea
                    id="discovery-answer"
                    ref={composer}
                    value={answer}
                    onChange={(event) => setAnswer(event.target.value)}
                    maxLength={2000}
                    rows={3}
                    placeholder="Write in your own words, or add a few ideas above…"
                    aria-describedby="discovery-composer-hint"
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" &&
                        (event.metaKey || event.ctrlKey)
                      ) {
                        event.preventDefault();
                        send();
                      }
                    }}
                  />
                  <div className="discovery-composer-footer">
                    <span id="discovery-composer-hint">
                      Choose several ideas, then send. ⌘ / Ctrl + Enter
                    </span>
                    <button
                      className="discovery-send"
                      type="submit"
                      disabled={!answer.trim()}
                    >
                      Send answer <span aria-hidden="true">↑</span>
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="discovery-ready" aria-busy={busy}>
                <h2>Ready to explore the possibilities?</h2>
                <p>
                  I’ll compare your interests, subjects, priorities and
                  strengths with the careers in our collection. These are
                  starting points to explore, not a verdict about you.
                </p>
                {error && (
                  <p className="discovery-error" role="alert">
                    {error} Your answers are saved here.
                  </p>
                )}
                <button
                  className="discovery-send"
                  onClick={findCareers}
                  disabled={busy}
                >
                  {busy
                    ? "Comparing your answers…"
                    : error
                      ? "Try again"
                      : "Explore my three careers"}
                </button>
              </div>
            )}
            {step > 0 && (
              <button
                className="discovery-edit"
                onClick={editPrevious}
                disabled={busy}
              >
                Edit my previous answer
              </button>
            )}
          </div>
        </div>
        <aside
          className="discovery-progress"
          aria-label="Conversation progress"
        >
          <p>
            {complete
              ? "Your context is ready"
              : `Question ${step + 1} of ${questions.length}`}
          </p>
          <ol>
            {questions.map((q, index) => (
              <li
                key={q.id}
                className={
                  index < step ? "is-done" : index === step ? "is-current" : ""
                }
                aria-current={index === step ? "step" : undefined}
              >
                <span aria-hidden="true">{index < step ? "✓" : index + 1}</span>
                {q.label}
              </li>
            ))}
          </ol>
          <small>
            You can be uncertain. You can change your mind. This is a place to
            begin.
          </small>
        </aside>
      </div>
    </section>
  );
}
