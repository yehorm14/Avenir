# Codex main sync — 18 October 2026

Status: complete on `codex/final-delivery`.

Merged fetched `origin/main` through `eaf0740`. Added its integrated Home/Amira journey, updated Jobs catalogue and demand evidence, grounded guide API and BlackRock employer card. Preserved the five-item primary navigation, simple My plan and Inter-based product styling. Restored the quiz simplifications and focus behavior that the merge would have regressed. Fixed misleading fallback and source-link notes in Chatbot.

Verification: `PATH="$PWD/.venv/bin:$PATH" make check` passed 716 tests with 3 optional skips, plus lint, formatting, production build and secret scan. Chrome DevTools verified Home, Jobs, first quiz screen, My plan and a real prepared Chatbot reply in isolated QA pages. The user's saved browser plan was not modified.

Pushed only `codex/final-delivery`; `main` was not modified. Local app runs at http://127.0.0.1:4175.
