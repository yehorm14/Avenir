import { getCareerContent } from "./content";
import type { Career } from "./types";
import "./dashboardNextSteps.css";

type DashboardNextStepsProps = {
  career: Career;
  onPlan: (career: Career) => void;
  saved: string[];
  onToggleSave: (id: string) => void;
};

export default function DashboardNextSteps({
  career,
  onPlan,
  saved,
  onToggleSave,
}: DashboardNextStepsProps) {
  const content = getCareerContent(career.soc, career.family);
  const courses = content.universities.slice(0, 2);
  const opportunities = content.opportunities.slice(0, 2);

  return (
    <aside className="dashboard-next-steps" aria-label="Your next steps">
      <header className="dashboard-next-steps-heading">
        <h2>Your next steps</h2>
        <p>For {career.title.toLowerCase()}</p>
      </header>

      <section className="dashboard-starter-task">
        <h3>Try the work</h3>
        <p>{content.firstSteps[0]}</p>
        <button
          type="button"
          className="dashboard-plan-button"
          onClick={() => onPlan(career)}
        >
          Build my plan
        </button>
        <p className="dashboard-plan-detail">
          Compare study routes, skills and practical steps.
        </p>
      </section>

      {courses.length > 0 && (
        <section className="dashboard-course-examples">
          <h3>Course examples</h3>
          <ul>
            {courses.map((course) => (
              <li key={course.url}>
                <a href={course.url} target="_blank" rel="noreferrer">
                  <span>{course.course}</span>
                  <small>{course.name}</small>
                </a>
                <p>{course.nation}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {opportunities.length > 0 && (
        <section className="dashboard-learning-links">
          <h3>Learning &amp; experience</h3>
          <ul>
            {opportunities.map((opportunity) => {
              const isSaved = saved.includes(opportunity.id);
              return (
                <li key={opportunity.id}>
                  <div className="dashboard-opportunity-heading">
                    <a href={opportunity.url} target="_blank" rel="noreferrer">
                      {opportunity.title}
                    </a>
                    <button
                      type="button"
                      className="dashboard-save-button"
                      aria-label={
                        isSaved
                          ? `Remove ${opportunity.title} from saved opportunities`
                          : `Save ${opportunity.title}`
                      }
                      aria-pressed={isSaved}
                      onClick={() => onToggleSave(opportunity.id)}
                    >
                      {isSaved ? "Saved" : "Save"}
                    </button>
                  </div>
                  <p className="dashboard-opportunity-location">
                    {opportunity.kind} · {opportunity.location}
                  </p>
                  <p className="dashboard-opportunity-description">
                    {opportunity.description}
                  </p>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <p className="dashboard-discovery-note">
        Examples and discovery links, not confirmed openings or university
        rankings. Check dates, fees, entry requirements and eligibility at the
        source.
      </p>
    </aside>
  );
}
