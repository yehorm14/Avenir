# Status: Codex

Updated: 17 October 2026

Doing now: Aventier conversation-first entry complete locally on codex/conversational-onboarding. Preview http://127.0.0.1:4175/ now opens the new mission page.

Done and merged: Public logo/name now Aventier; scrolling mission, reassurance and two starting points. Exploring route asks interests, school subjects, values, hard/soft skills. Known route adds desired career/context. Both lead to3 career descriptions and retain existing weights, ranking, pathways, universities and opportunities. Drafts persist; edits/retry/multi-select suggestions work. Nothing pushed or merged remotely; no formal review.

Interfaces changed: Added app-local POST /api/discovery using existing loaded ML evidence, bounded answers, deterministic extraction and exactly3 results. Explicit dislikes excluded. Known exact career is a reference, related unsupported titles disclosed. Shared contracts/data untouched.

Verified: Build/format/API Ruff/whitespace pass.305 root tests +30 app API tests pass;1 optional model smoke skipped. Browser exercised both routes, saved answers, values weights, three descriptions, known reference after reranking and path creation, with no desktop overflow or console errors. Screenshots in apps/web/artifacts.

Blocked on: Nothing for this requested change. Conversational text is guided/prepared rather than a live LLM; matching remains preliminary as labelled.
