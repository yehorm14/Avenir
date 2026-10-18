# CS and Finance demo polish

User scope: review the current app and improve it for a desktop hackathon demo of Computer Science and Finance. Preserve the Quant Soc charcoal/silver/blue direction and real data; remove generic motivational copy, ornamental UI and unnecessary onboarding.

Base: b8ae819, isolated branch codex/cs-finance-demo. Existing release checkout and preview on 4175 are preserved.

Review evidence: 412-career directory hides the two subjects. Current role profiles are around 3,700px tall, chart starts around 1,300px and primary action around 3,560px. Broad subject strings are ambiguous in discovery; use explicit editorial anchors 2134 (software) and 2422 (finance analyst), with clearly labelled related occupations.

Implementation:
- Root: direct durable CS/Finance routes, focused home entry, concise pathway/opportunity copy and integrated preview.
- Dashboard design agent: shared role-switchable evidence dashboard with early chart, sourced facts and compact outlook.
- Next-step design agent: practical task, course examples and saveable learning/work-experience links.
- Content agent: concrete descriptions and honest scenario/outlook labels in existing profiles, followed by independent visual review.

Verification: existing frontend tests as baseline (17 passed), final build/format/test, actual desktop browser flows for both subjects, chart measures, role switch, reload, plan and saved links. Review integrated diff before completion. No protected contract, ML or backend changes are planned.

Status: complete locally, ready for review. No push, main merge or public deployment.

Integrated local agent checkpoints: content83fc87d/e3aa853, next stepsf88f491/fc046bd, dashboarda8e6a82/f8024d4/b0492ce, direct-plan editing662ecef. Root adds direct subject entry, separate durable guide context, direct-plan navigation and home/pathway copy.

Final evidence: full make check exit0,438 core+101 API/integration/scanner+32 prototype+17 frontend=588 passed,2 optional model skips. Build/format rerun after final two-line CSS divider cleanup. Three specialist agents independently checked screenshots, source links, evidence invariants and integrated code; no important open findings.

Chrome desktop checks: both subject/role hash routes and reload, all chart measures, source details, starter-pay positioning, saved links, direct plan creation, route/note persistence and change-career behavior. Opening a guide preserves all saved preferences. No console errors/warnings or horizontal overflow at1200x800 and1440x1000. Header plan action y109; chart and starter guide y495. Screenshots: apps/web/artifacts/demo-{cs,finance,home}-desktop.jpg. Walkthrough: docs/launch/cs-finance-demo.md.

Preview: http://127.0.0.1:4186. Existing4175 is untouched. This worktree reuses the original environment only for validation; if restarting without local dependencies, set AVENIR_PYTHON to /Users/zakharov/Documents/ChatGPT/DYHTG26/avenir-integration/.venv/bin/python and AVENIR_PORT=4186 before node scripts/run-app.mjs --production, or run the normal setup.

Limits preserved: workforce observations are not graduate outcomes, published sector scenarios retain original horizon/coverage, opportunities are discovery links, guide replies are prepared, snapshot data is dated. Protected ML/API/contract files are unchanged.
