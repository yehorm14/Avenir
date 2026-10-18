# Codex: final-delivery navigation

- Branch: `codex/final-delivery`
- Status: complete on final-delivery; final chat reports the verified remote revision
- Publication: this branch only; no main update or PR merge

The user requested the exact primary menu Home, Quiz, Jobs, My plan and Chatbot while retaining the new design and merging the cleanup into final-delivery. The later explicit menu list resolves the earlier repeated Quiz/Jobs wording. Remove the Computer Science and Finance top-level tabs, rename the Career guide tab/page to Chatbot, and retain their existing dashboard routes, Home cards, guide deep links and secondary plan tools.

Merged the latest plan-simplify checkpoint 1ca1014 by fast-forward. Work happens in the existing integration checkout, now on codex/final-delivery; the old temporary delivery worktree is preserved on codex/final-navigation. No main commits are being added for this navigation task.

Plan: update the two UI labels/menu list; verify all five destinations, active state, direct chat and narrow layout in Chrome; run the full project gate and independent read-only review; commit and push final-delivery; verify remote refs and preserve user state.

Design: retain the existing Inter, charcoal/silver/blue palette, floating pill menu, page layouts and focus states. No new CSS, typography or visual assets are needed.

Done: exact menu and Chatbot heading implemented; all five destinations and active states checked at 390px without overflow or console warnings/errors. Chat reply returned actual pay with two sources. Career deep link 2134 checked at 1280px. User tab refreshed; existing plan preserved. Independent read-only source review accepted the change. Full make check 672 passed/3 optional skips, including lint/format/build/secret scan. Log: `/private/tmp/aventier-final-navigation-check.log`.

No contract, backend or ML edits. No main merge or push is authorized for this task. Current source includes the earlier plan cleanup and approved teammate fixes through 076cdbe; later main changes remain outside this requested branch update.
