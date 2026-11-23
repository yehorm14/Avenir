import { exampleSteps } from "./exampleProfile";
import type { Page } from "./types";

type Props = {
  page: Page;
  go: (page: Page) => void;
  onFreshSession: () => void;
};

/** Labels the sample flow and offers a one-click way back to a clean, empty session. */
export default function GuidedExample({ page, go, onFreshSession }: Props) {
  return (
    <aside className="guided-example" aria-label="Example profile">
      <div>
        <strong>Example profile: Amira</strong>
        <p>
          These are prepared sample answers, not yours, and no personal details
          or provider keys are used. Follow the steps from quiz answers to
          comparison to plan. The plan is stored only in this browser and is
          never sent to an account.
        </p>
        <ol className="guided-example-steps">
          {exampleSteps.map((step) => (
            <li key={step.page}>
              <button
                type="button"
                onClick={() => go(step.page)}
                aria-current={page === step.page ? "step" : undefined}
              >
                {step.label}
              </button>
            </li>
          ))}
        </ol>
      </div>
      <button
        className="button secondary"
        type="button"
        onClick={onFreshSession}
      >
        Start a fresh session
      </button>
    </aside>
  );
}
