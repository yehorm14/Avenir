import { useEffect, useRef, useState } from "react";
import type { Career } from "./types";
import { Icon } from "./icons";
import { api } from "./store";
import "./guides.css";

type Source = {
  id?: string;
  name?: string;
  url?: string;
  coverage?: string;
};
type GuideResponse = { text: string; sources?: Source[] };
type Message = {
  role: "user" | "guide";
  text: string;
  sources?: Source[];
};
type PendingQuestion = {
  text: string;
  history: { role: "user" | "assistant"; content: string }[];
};

const questionLimit = 2000;
const suggestions = [
  "What does the work involve?",
  "What skills can I start building?",
  "What are the routes into this career?",
  "How might AI affect the work?",
];

function sourceLinks(sources: Source[] = []) {
  const seen = new Set<string>();
  return sources.flatMap((source) => {
    if (!source || typeof source.url !== "string") return [];
    try {
      const url = new URL(source.url);
      if (
        !["https:", "http:"].includes(url.protocol) ||
        url.username ||
        url.password ||
        seen.has(url.href)
      )
        return [];
      seen.add(url.href);
      return [
        {
          url: url.href,
          name: source.name?.trim() || source.id || "Original source",
          coverage: source.coverage,
        },
      ];
    } catch {
      return [];
    }
  });
}

export default function Guides({ careers }: { careers: Career[] }) {
  const [soc, setSoc] = useState(careers[0]?.soc ?? "");
  const career = careers.find((item) => item.soc === soc) ?? careers[0];
  const singleCareer = careers.length === 1;

  return (
    <section
      className={`evidence-guide${singleCareer ? " evidence-guide-single" : ""}`}
      aria-labelledby="guide-page-title"
    >
      <header className="page-heading">
        <div>
          <h1 id="guide-page-title">Career questions.</h1>
          <p className="page-description">
            Explore the work, study routes and evidence behind your options.
          </p>
        </div>
      </header>
      {career ? (
        <div className="evidence-guide-layout">
          {!singleCareer && (
            <aside className="evidence-guide-careers">
              <h2>Choose a career</h2>
              <nav aria-label="Career for your guide">
                {careers.map((item) => (
                  <button
                    key={item.soc}
                    type="button"
                    aria-pressed={career.soc === item.soc}
                    onClick={() => setSoc(item.soc)}
                  >
                    <span>
                      <strong>{item.title}</strong>
                      <small>{item.sector}</small>
                    </span>
                    <Icon name="chevron" size={16} />
                  </button>
                ))}
              </nav>
              <p>
                Conversations last while this guide is open. Switching careers
                starts a new conversation.
              </p>
            </aside>
          )}
          {/* A separate instance prevents a late response entering another career's conversation. */}
          <CareerGuide
            key={career.soc}
            career={career}
            compact={singleCareer}
          />
        </div>
      ) : (
        <div className="empty-state">
          <Icon name="book" size={32} />
          <h2>No career profiles are available.</h2>
          <p>Reload the career collection to open an evidence guide.</p>
          <button
            type="button"
            className="button secondary"
            onClick={() => window.location.reload()}
          >
            Reload career evidence
          </button>
        </div>
      )}
    </section>
  );
}

function CareerGuide({
  career,
  compact = false,
}: {
  career: Career;
  compact?: boolean;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState<PendingQuestion | null>(null);
  const [error, setError] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const request = useRef<AbortController | null>(null);
  const speech = useRef<SpeechSynthesisUtterance | null>(null);
  const transcript = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const inputId = `guide-question-${career.soc}`;
  const introduction = `Ask about the day-to-day work, pay, skills, study routes or automation research for ${career.title.toLowerCase()}. Responses use prepared information and the career evidence available in Aventier.`;
  const latestReply =
    messages.filter((message) => message.role === "guide").slice(-1)[0]?.text ??
    introduction;
  const canReadAloud =
    typeof window.speechSynthesis !== "undefined" &&
    typeof SpeechSynthesisUtterance !== "undefined";

  function stopReading() {
    if (speech.current) {
      speech.current.onend = null;
      speech.current.onerror = null;
      speech.current = null;
    }
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }

  useEffect(() => {
    return () => {
      request.current?.abort();
      request.current = null;
      if (speech.current) {
        speech.current.onend = null;
        speech.current.onerror = null;
      }
      window.speechSynthesis?.cancel();
    };
  }, []);

  useEffect(() => {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    transcript.current?.scrollTo({
      top: transcript.current.scrollHeight,
      behavior: reducedMotion ? "auto" : "smooth",
    });
  }, [messages, sending]);

  async function answerQuestion(question: PendingQuestion) {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    stopReading();
    setSending(true);
    setFailed(null);
    setError("");
    try {
      const response = await api<GuideResponse>(
        "guide",
        {
          soc: career.soc,
          message: question.text,
          history: question.history,
        },
        controller.signal,
      );
      if (controller.signal.aborted || request.current !== controller) return;
      if (typeof response.text !== "string" || !response.text.trim())
        throw new Error("The guide returned an empty reply. Please try again.");
      setMessages((previous) => [
        ...previous,
        {
          role: "guide",
          text: response.text,
          sources: Array.isArray(response.sources) ? response.sources : [],
        },
      ]);
    } catch (cause) {
      if (controller.signal.aborted || request.current !== controller) return;
      setFailed(question);
      setError(
        cause instanceof Error
          ? cause.message
          : "The guide couldn't load a reply. Please try again.",
      );
    } finally {
      if (!controller.signal.aborted && request.current === controller) {
        request.current = null;
        setSending(false);
      }
    }
  }

  function send(text: string) {
    const question = text.trim();
    if (!question || question.length > questionLimit || request.current) return;
    const history: PendingQuestion["history"] = messages
      .slice(-8)
      .map((message) => ({
        role: message.role === "guide" ? "assistant" : "user",
        content: message.text,
      }));
    setMessages((previous) => [...previous, { role: "user", text: question }]);
    setInput("");
    void answerQuestion({ text: question, history });
  }

  return (
    <section
      className={`evidence-guide-chat${messages.length ? " has-messages" : ""}`}
      aria-labelledby="guide-career-title"
    >
      <header className="evidence-guide-header">
        <div>
          <h2 id="guide-career-title">{career.title}</h2>
          <p>{career.sector}</p>
        </div>
        <span className="subtle-badge">Prepared evidence guide</span>
      </header>
      <div
        className="evidence-guide-transcript"
        ref={transcript}
        role="log"
        aria-label={`Questions and answers about ${career.title}`}
        aria-live="polite"
        aria-relevant="additions text"
        aria-busy={sending}
        tabIndex={0}
      >
        <article className="evidence-guide-message">
          {!compact && <h3>Explore {career.title.toLowerCase()}</h3>}
          <p>{introduction}</p>
          <p className="evidence-guide-note">
            Use this as a starting point. Check sources and current entry
            requirements before making a decision.
          </p>
        </article>
        {messages.map((message, index) => {
          const sources = sourceLinks(message.sources);
          return (
            <article
              className={`evidence-guide-message ${message.role === "user" ? "evidence-guide-question" : "evidence-guide-answer"}`}
              key={index}
            >
              <h3>{message.role === "user" ? "You" : "Prepared guide"}</h3>
              <p>{message.text}</p>
              {message.role === "guide" &&
                (sources.length ? (
                  <div className="evidence-guide-sources">
                    <h4>Sources for this answer</h4>
                    <ul>
                      {sources.map((source) => (
                        <li key={source.url}>
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`${source.name} (opens in a new tab)`}
                          >
                            {source.name} <Icon name="external" size={13} />
                          </a>
                          {source.coverage && <small>{source.coverage}</small>}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="evidence-guide-note">
                    No source links are available for this reply. Check details
                    with the relevant course provider or employer.
                  </p>
                ))}
            </article>
          );
        })}
        {sending && (
          <div className="evidence-guide-loading" role="status">
            <span className="spinner" aria-hidden="true" />
            Looking through the career evidence…
          </div>
        )}
      </div>
      {messages.length === 0 && (
        <div
          className="evidence-guide-suggestions"
          aria-label="Suggested questions"
        >
          {suggestions.map((question) => (
            <button
              type="button"
              disabled={sending}
              onClick={() => send(question)}
              key={question}
            >
              {question}
              <Icon name="plus" size={15} />
            </button>
          ))}
        </div>
      )}
      {failed && (
        <div className="evidence-guide-error" role="alert">
          <p>{error} Your question is kept above.</p>
          <button
            type="button"
            className="button secondary"
            onClick={() => void answerQuestion(failed)}
            disabled={sending}
          >
            <Icon name="refresh" size={15} /> Retry question
          </button>
        </div>
      )}
      <form
        className="evidence-guide-composer"
        onSubmit={(event) => {
          event.preventDefault();
          send(input);
          composer.current?.focus();
        }}
      >
        <label htmlFor={inputId}>Ask about {career.title.toLowerCase()}</label>
        <div>
          <textarea
            id={inputId}
            ref={composer}
            value={input}
            maxLength={questionLimit}
            rows={2}
            placeholder="What would you like to understand?"
            aria-describedby={`${inputId}-hint`}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                send(input);
              }
            }}
          />
          <button
            type="submit"
            className="button primary"
            disabled={!input.trim() || sending}
            aria-label="Send question"
          >
            <span>Send</span> <Icon name="arrow" size={18} />
          </button>
        </div>
        <p id={`${inputId}-hint`}>
          Enter to send. Shift + Enter for a new line.{" "}
          {input.length.toLocaleString("en-GB")} / 2,000
        </p>
      </form>
      <footer className="evidence-guide-footer">
        <p>Exploratory guidance. This conversation is not saved.</p>
        {canReadAloud && (
          <button
            type="button"
            aria-pressed={speaking}
            onClick={() => {
              if (speaking) {
                stopReading();
                return;
              }
              stopReading();
              const utterance = new SpeechSynthesisUtterance(latestReply);
              utterance.lang = "en-GB";
              const finish = () => {
                if (speech.current === utterance) {
                  speech.current = null;
                  setSpeaking(false);
                }
              };
              utterance.onend = finish;
              utterance.onerror = finish;
              speech.current = utterance;
              setSpeaking(true);
              window.speechSynthesis.speak(utterance);
            }}
          >
            {speaking ? "Stop reading" : "Read latest response aloud"}
          </button>
        )}
      </footer>
    </section>
  );
}
