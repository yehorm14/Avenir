import type { Career } from "./types";
import { money } from "./Charts";
import "./landing.css";

const subjects = [
  {
    area: "cs" as const,
    name: "Computer Science",
    soc: "2134",
    description: "Software development, data analysis and cyber security.",
    action: "Explore CS",
  },
  {
    area: "finance" as const,
    name: "Finance",
    soc: "2422",
    description: "Investment analysis, accountancy and quantitative work.",
    action: "Explore finance",
  },
];

export default function Landing({
  careers,
  onChoose,
  onDashboard,
  onAmira,
  amiraBusy = false,
  amiraError = "",
  resume,
}: {
  careers: Career[];
  onChoose: (mode: "known" | "explore") => void;
  onDashboard: (area: "cs" | "finance") => void;
  onAmira: () => void;
  amiraBusy?: boolean;
  amiraError?: string;
  resume?: { title: string; onResume: () => void };
}) {
  return (
    <div className="aventier-landing">
      <section className="mission-section" aria-labelledby="mission-heading">
        <header className="mission-heading">
          <h1 id="mission-heading">Aventier</h1>
          <p>Compare careers. Choose a route. Plan your next step.</p>
        </header>
        <article className="amira-journey" aria-labelledby="amira-heading">
          <span className="amira-kicker">Start here</span>
          <h2 id="amira-heading">Amira, 17, S6 in Glasgow</h2>
          <p>
            Good at maths and art. Her first idea is architect, and she is
            worried about AI. See three careers worth exploring next to that
            first idea, a hedge career, how simple rules held up, and her next
            step.
          </p>
          <button
            className="mission-cta mission-cta-primary"
            onClick={onAmira}
            disabled={amiraBusy}
          >
            {amiraBusy ? "Comparing…" : "Try architect"}
          </button>
          {amiraError && (
            <p className="amira-error" role="alert">
              {amiraError}
            </p>
          )}
        </article>
        <h2 className="other-journey-heading">
          Another journey: Computer Science and Finance
        </h2>
        <div className="subject-choices" aria-label="Career dashboards">
          {subjects.map((subject) => {
            const career = careers.find((item) => item.soc === subject.soc);
            const pay = career?.metrics.pay_median;
            const available =
              pay?.status !== "pending" && !pay?.flags.includes("suppressed");
            return (
              <article className="subject-choice" key={subject.area}>
                <h2>{subject.name}</h2>
                <p>{subject.description}</p>
                <div className="subject-role">
                  <span>Example career</span>
                  <h3>{career?.title ?? "Career evidence unavailable"}</h3>
                  <strong>{money(available ? pay?.value : null)}</strong>
                  <small>
                    Median annual pay · {pay?.as_of ?? "Year unavailable"} · UK
                  </small>
                </div>
                <button
                  className="mission-cta mission-cta-primary"
                  onClick={() => onDashboard(subject.area)}
                >
                  {subject.action}
                </button>
              </article>
            );
          })}
        </div>
        <p className="subject-source">
          ONS ASHE · Full-time employee pay, provisional. Figures describe the
          example occupations, not graduate earnings.
        </p>
        <div className="other-directions">
          <span>Or start with your own idea</span>
          <div>
            <button onClick={() => onChoose("known")}>Explore career</button>
            <button onClick={() => onChoose("explore")}>Find careers</button>
          </div>
        </div>
        {resume && (
          <div className="resume-plan">
            <div>
              <span>Your saved plan</span>
              <strong>{resume.title}</strong>
            </div>
            <button
              className="mission-cta mission-cta-secondary"
              onClick={resume.onResume}
            >
              Resume plan
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
