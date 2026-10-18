# Avenier conversational onboarding

User brief: first page shows Avenier logo and mission to help students decide and plan their future. Scroll to reassurance that uncertainty is okay and we are here to help. Scroll again to two choices: known career direction or still exploring. Both lead into a conversation collecting relevant interests, school subjects, values and hard/soft skills; known direction adds context about the intended career. End with three career options/descriptions, then preserve existing comparison and pathway tools.

User preferences: fast, desktop only, make reasonable assumptions, no formal code-review workflow. Retain the existing minimal neutral/green design and top navigation. Use existing logo symbol with Avenier wordmark. Conversation is guided and prepared; extraction uses Arsenii's supplied tag matcher and affinities, not a claimed live LLM.

Implementation: scroll-based Landing component, persistent Discovery chat draft, app-local discovery endpoint with deterministic extraction and exactly three unique careers. Known supported career is a labelled reference alongside two alternatives; unsupported roles are acknowledged rather than fabricated. Values can influence transparent comparison priorities. No signal prompts for clarification instead of returning random matches. Core extraction/ranking receives tests first; UI is verified in the actual browser.

Status: complete locally on codex/conversational-onboarding. Independent API/chat work uses isolated worktrees. Shared contracts and source fixtures are untouched.

Verified: production build, formatting, API Ruff and whitespace pass;305 root +30 API tests pass,1 optional model smoke skipped. Fresh desktop browser exercised both routes and3 result descriptions, multi-selection, persistence, known reference preservation and pathway creation. Screenshot entry/choices saved. Exact supplied data retained. No review/push/publication.
