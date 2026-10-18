# Codex: simpler My plan

- Branch: `codex/final-delivery`
- Status: verified; final chat reports the branch's published revision
- Publication: this branch only; main is outside scope

User request: remove all tabs inside My plan and simplify it. Remove the secondary tab row from overview and both repeated comparison tables. Keep the chosen career, key figures, embedded chat, monthly checklist and download. Retain saved opportunities and safe-reset controls when relevant. Replace the former comparison edit button with a small Change career action; provide a simple View pathway link so the detailed route remains accessible without tabs.

Design: preserve the current charcoal, silver and blue style and primary Home/Quiz/Jobs/My plan/Chatbot menu. No storage, contract, backend or ML changes. Other workspace routes retain their navigation. UI/glue verification follows the user's browser-first rule rather than adding implementation-mirroring tests.

Plan: remove redundant overview UI, verify browser layout and existing controls, run the project gate and independent source review, record evidence, commit and push final-delivery only.

Done: removed overview tabs and both comparison tables; added direct Change career and View pathway actions. Independent review accepted the assembled diff and confirmed existing checklist, saved-item, safe-reset, chat, preference and export code remains intact. Chrome checked pathway access/return, direct career editing/return, actual chat reply and all three checklist items with existing progress; no 390px overflow or console warnings/errors. A read-only preview of the user's completed plan confirms the same simplified page without mutating its 0/3 progress. Screenshot: `apps/web/artifacts/my-plan-simple.png`.

Verification: make check 672 passed/3 optional skipped; 477 core, 130 API/integration/scripts, 39 prototype, 26 web. Lint, formatting, production build and tracked-file secret scan passed. Log: `/private/tmp/aventier-plan-single-check.log`. No contract, API, ranking, ML, storage or export changes; no main merge or push.
