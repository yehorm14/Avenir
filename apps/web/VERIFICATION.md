# Verification — 17 October 2026

The production app runs at http://127.0.0.1:4175 using `node scripts/run-app.mjs --preview`; API port 8015. This is a local integration on `codex/complete-career-experience`, not a public deployment or a merged branch. The original dirty KATYATA checkout is preserved.

## Commands and results

- `npm --prefix apps/web run format:check`: all matched files use Prettier style.
- `npm --prefix apps/web run build`: TypeScript and Vite production build pass. Approx. 247 kB JavaScript / 78 kB gzip; 55 kB CSS / 12 kB gzip.
- `.venv/bin/python -m pytest`: 305 passed, 1 skipped. The skipped smoke test requires the optional full real model environment. Two pre-existing FastAPI lifecycle deprecations remain.
- `.venv/bin/python -m pytest apps/web/api/tests -q`: 13 passed. One dependency deprecation warns about Starlette's httpx test client; no test failures.
- `.venv/bin/python -m ruff check apps/web/api`: passes.
- `node --check scripts/run-app.mjs`: passes.
- `git diff --check`: passes.

After importing latest ML, the old fixture-specific eligibility count changed from seven to eleven. The test was updated to match cb9e169's supplied embedding table; selection rules are unchanged. Frontend schema/examples were regenerated from the imported owner's v2.1 models and latest data. No protected contract was manually edited.

## Browser evidence

Chrome DevTools exercised the actual production bundle and real Python API. The eight quiz questions were answered through their visible radio controls and continued through the location screen. Five matches rendered with exactly three sliders; choosing three careers enabled pathway creation, prevented a fourth selection, and populated the first-choice route. Universities opened as official course links. The guide handled consecutive AI/pay questions with exact supplied salary/range and appropriate caveats. An opportunity was saved and filtered successfully.

A final automated browser pass completed **27/27 assertions** on the latest ML import:

- Source mode real, fit preliminary, 20 mapped demo careers, 2007 salary history, populated ESCO shared skills.
- Overview, matches, pathway, opportunities, guides and evidence render without horizontal overflow at 390px.
- Five matches and exactly three priority sliders.
- Changing Pay to 100% reorders the actual cards to the highest supplied median pay. Original weights restore successfully.
- Ranked choices survive priority changes; location and local progress persist.
- Historical outcomes include real pay growth and negative results.
- Employee-job charts split into two eras per career at 2021; text tables contain all 19 years.
- Related careers show actual shared skills; alumni outreach kit is retained.

At 1440px, overview renders at scroll position zero with no horizontal overflow. Chrome reports **no console errors or warnings**. Modal focus containment, arrow-key quiz selection, keyboard chart inspection, reduced motion and clear input labels are implemented. These are browser checks, not a formal code review or a comprehensive accessibility certification.

Screenshots: `artifacts/overview-desktop.jpg`, `artifacts/pathway-mobile.jpg`.

## Limits reflected in the UI

Career metrics and fit are preliminary. The quiz is not psychometrically validated. Need is a historical trend, not an LLM forecast. Guides are prepared, grounded demos, with browser read-aloud where supported. University and opportunity links are curated discovery sources, not confirmed places or live vacancies. Overtime and starting-salary data are unavailable. No credentials or remote providers are needed.

## Desktop top navigation follow-up

Moved workspace navigation into the sticky top header; removed the sidebar and its layout offsets. All six destinations, active-page states and match count are retained. Overview/pathway retain the primary career context previously repeated in the sidebar. No mobile work was requested.

Fresh verification: production TypeScript/Vite build passes, format check and git whitespace check pass. Chrome DevTools verifies all six header links activate and render their pages, no sidebar remains, main starts at x=0, and the top menu fits at 1894px and 1280px without overflow or overlap with profile controls. Screenshot: artifacts/top-navigation-desktop.jpg.

## Aventier conversation-first entry

New scrolling entry: Aventier logo/student mission, reassurance, then two choices. Exploring asks four questions (interests, school subjects, values, skills); known direction adds the intended career first. Free text and multi-select suggestions, saved submitted answers, editing, confirmation and retry are supported. Both routes produce exactly three descriptions and feed the existing ranking/pathway experience.

Fresh checks: production build/format pass, API Ruff and whitespace pass. Root suite305 passed/1 optional real-model smoke skipped; app API30 passed (335 passing total). Discovery tests cover both routes, three unique results, original metrics/history, typed/bounded inputs, unsupported roles, priority wording, explicit dislikes, known references and no-signal errors. Dependency deprecation warnings remain as previously documented.

Chrome exercised a fresh browser context at1440px: first arrival shows logo/mission; reassurance and two choices follow in scroll order. Multiple suggestion chips append into free text. All4 exploring answers persist, summary confirmation returns3 descriptions and appropriate demand weights. Known Civil engineer flow asks5 questions, retains2121 first after re-ranking, saves context, allows ranking3 choices and opens the civil-engineering pathway. No horizontal overflow or console errors/warnings. The first screenshot-node click timed out before results; retry after scrolling the confirmation into view succeeded. Both actual endpoints and visible results were verified.

Screenshots: artifacts/aventier-landing-desktop.jpg and artifacts/aventier-starting-points-desktop.jpg. Desktop only; no mobile work or formal review. Guided prepared chat, deterministic extraction, preliminary affinities; no live LLM claim.
