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
  resume,
}: {
  careers: Career[];
  onChoose: (mode: "known" | "explore") => void;
  onDashboard: (area: "cs" | "finance") => void;
  resume?: { title: string; onResume: () => void };
}) {
  return (
    <div className="aventier-landing">
      <section className="mission-section" aria-labelledby="mission-heading">
        <header className="mission-heading">
          <h1 id="mission-heading">Aventier</h1>
          <p>Compare careers. Choose a route. Plan your next step.</p>
        </header>
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
          <span>Explore other careers</span>
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
