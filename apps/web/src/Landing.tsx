import { useRef } from "react";
import { Icon } from "./icons";
import "./landing.css";

export default function Landing({
  onChoose,
}: {
  onChoose: (mode: "known" | "explore") => void;
}) {
  const reassurance = useRef<HTMLElement>(null),
    choices = useRef<HTMLElement>(null);
  const scrollTo = (el: HTMLElement | null) =>
    el?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  return (
    <div className="aventier-landing">
      <section className="mission-section" aria-labelledby="mission-heading">
        <svg
          className="mission-waves"
          viewBox="0 0 1440 900"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <defs>
            <linearGradient
              id="aventier-wave-light"
              x1="0"
              y1="0"
              x2="1"
              y2="0"
            >
              <stop stopColor="#f4e4bc" stopOpacity="0" />
              <stop offset=".3" stopColor="#f4e4bc" stopOpacity=".8" />
              <stop offset=".7" stopColor="#e0bf77" />
              <stop offset="1" stopColor="#f4e4bc" stopOpacity="0" />
            </linearGradient>
          </defs>
          <g fill="none" stroke="url(#aventier-wave-light)" strokeWidth=".75">
            {Array.from({ length: 30 }, (_, i) => (
              <path
                key={i}
                d={`M -160 ${605 + i * 7} C 180 ${295 + i * 5}, 430 ${1060 - i * 8}, 775 ${655 + i * 2} S 1190 ${190 + i * 10}, 1600 ${415 + i * 8}`}
                opacity={0.18 + i * 0.009}
              />
            ))}
          </g>
        </svg>
        <div className="mission-wordmark" aria-label="Aventier">
          AVENTIER
        </div>
        <h1 id="mission-heading">
          Helping students decide and plan their future.
        </h1>
        <p>
          Find a direction that feels like you.
          <br />
          Then turn it into a plan you can actually follow.
        </p>
        <div className="mission-actions">
          <button
            className="mission-cta mission-cta-primary"
            onClick={() => scrollTo(choices.current)}
          >
            Start wherever you are <Icon name="arrow" size={17} />
          </button>
          <button
            className="mission-cta mission-cta-secondary"
            onClick={() => scrollTo(reassurance.current)}
          >
            Let's take it one step at a time
          </button>
        </div>
        <button
          className="scroll-invitation"
          onClick={() => scrollTo(reassurance.current)}
          aria-label="Read why it's okay not to know what comes next"
        >
          <Icon name="down" size={19} />
        </button>
      </section>
      <section
        ref={reassurance}
        className="reassurance-section"
        aria-labelledby="reassurance-heading"
      >
        <span className="reassurance-icon">
          <Icon name="compass" size={35} />
        </span>
        <h2 id="reassurance-heading">
          It's okay not to know
          <br />
          what comes next.
        </h2>
        <p>
          You don't need a perfect answer about your future.
          <br />
          You need space to explore—and someone to help you make sense of it.
        </p>
        <p className="reassurance-promise">
          We're here to help you find your way.
        </p>
        <button
          className="button secondary"
          onClick={() => scrollTo(choices.current)}
        >
          Start wherever you are
          <Icon name="down" size={17} />
        </button>
      </section>
      <section
        ref={choices}
        className="direction-section"
        aria-labelledby="direction-heading"
      >
        <h2 id="direction-heading">Where are you right now?</h2>
        <p>A clear idea or a blank page. Both are a good place to start.</p>
        <div className="direction-choices">
          <button
            className="direction-choice"
            onClick={() => onChoose("known")}
          >
            <span className="direction-choice-icon">
              <Icon name="path" size={27} />
            </span>
            <h3>I have a direction in mind.</h3>
            <p>
              I know the career or field I'm interested in. Help me understand
              my options and how to get there.
            </p>
            <span className="direction-choice-action">
              Explore my direction
              <Icon name="arrow" size={18} />
            </span>
          </button>
          <button
            className="direction-choice"
            onClick={() => onChoose("explore")}
          >
            <span className="direction-choice-icon">
              <Icon name="compass" size={27} />
            </span>
            <h3>I'm still figuring it out.</h3>
            <p>
              Help me connect what I enjoy, what I'm studying, and what matters
              to me with careers I could explore.
            </p>
            <span className="direction-choice-action">
              Find my possibilities
              <Icon name="arrow" size={18} />
            </span>
          </button>
        </div>
        <div className="direction-note">
          <Icon name="chat" size={16} />
          <span>
            A short conversation. Three career options. A practical next step.
          </span>
        </div>
      </section>
    </div>
  );
}
