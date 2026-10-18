# Quiz and Jobs cleanup

Ready for review. User supplied four precise removals, requested Quiz/Jobs debugging, then asked to merge with the latest Codex final. Based on final-delivery5ec744f; task branch codex/final-quiz-jobs. The latest assembled MLv1.2 product now runs on4175; the older release is preserved in Git.

Removed the marked quiz filler and redundant Jobs heading description. Previous question remains from question2. Fixed question heading focus/scroll and radio tab stops. Reproduced Jobs Back skipping the list; profiles now have career-specific hash URLs, refresh/history support, retained list filters, restored focus and a stale-profile guard. Offline failures show connection guidance; AbortError cancellation remains silent.

Final make check:645 passed/3 optional skips, lint/format/build/secret scan pass. Browser covers all8 questions, exact removals, saved-plan preservation, keyboard arrows/Tab,412-row reset, case/space/SOC search, both sorts, profile Back/refresh, offline retry and390px page overflow. The actual user tab was refreshed and visually inspected. Screenshots:apps/web/artifacts/quiz-cleanup.png and jobs-cleanup.png. Log:/private/tmp/aventier-quiz-jobs-release-check.log.

Fast-forwarded the verified task into codex/final-delivery, preserving authorship. No engine/ML/contracts changed, no main merge/public deployment. Prior PR authentication blocker unchanged; no rejected method retried.
