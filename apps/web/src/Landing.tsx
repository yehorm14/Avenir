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
        <div className="mission-wordmark" aria-label="Aventier">
          <span className="mission-symbol">a</span>
          <span>
            Aventier<span className="mission-period">.</span>
          </span>
        </div>
        <h1 id="mission-heading">
          Helping students decide
          <br />
          and plan their future.
        </h1>
        <p>
          Find a direction that feels like you.
          <br />
          Then turn it into a plan you can actually follow.
        </p>
        <button
          className="scroll-invitation"
          onClick={() => scrollTo(reassurance.current)}
        >
          Let's take it one step at a time
          <Icon name="down" size={20} />
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
