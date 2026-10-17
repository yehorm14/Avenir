import "./landing.css";

export default function Landing({
  onChoose,
}: {
  onChoose: (mode: "known" | "explore") => void;
}) {
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
        <div className="direction-choices" aria-label="Choose how to start">
          <article className="direction-choice">
            <h2>I have a career in mind.</h2>
            <p>Explore that career and compare your options.</p>
            <button
              className="mission-cta mission-cta-primary"
              onClick={() => onChoose("known")}
            >
              Explore career
            </button>
          </article>
          <article className="direction-choice">
            <h2>I’m still deciding.</h2>
            <p>Answer a few questions to find three career options.</p>
            <button
              className="mission-cta mission-cta-secondary"
              onClick={() => onChoose("explore")}
            >
              Find careers
            </button>
          </article>
        </div>
      </section>
    </div>
  );
}
