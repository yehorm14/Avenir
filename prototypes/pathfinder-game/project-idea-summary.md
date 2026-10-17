# Career Choice App: Idea Summary

**Event:** GUTS Hackathon, challenge by Aladdin by BlackRock ("One app. One clear decision.")
**Format:** Web app, United Kingdom-wide

## The problem

School pupils and students choose what to study with almost no evidence. The useful information exists, but it is scattered: government skills reports, employer surveys, interest tests and university course data live on different websites, in different formats, and none of them talk to each other.

## The idea

We do not try to predict the perfect job. We show **where the UK is short of people, now and by 2035**, and **where that overlaps with what the user already likes and has**. The result is a short, explained shortlist of 3 to 5 careers, each with a clear roadmap.

## The user and the decision

- **User:** Ellie, 16, in S5 at a school in Glasgow, unsure what to put on her UCAS form.
- **Decision:** Which 3 to 5 careers should she seriously explore, and what is her first concrete step towards each?
- **Secondary user:** A university student reconsidering their course.

## How it works

1. **Interest quiz:** the O*NET Interest Profiler (RIASEC, 60 items), plus school subjects, experience and skills the user already has.
2. **Matching:** a transparent, deterministic score built from four signals, all linked to one UK occupation code (SOC 2020):
   - Interest fit (40%)
   - Projected demand by 2035 (25%)
   - Demand now (20%)
   - Head start, meaning what the user already has (15%)
3. **Shortlist:** 3 to 5 careers, each with its score breakdown, a plain-language trade-off and a link to the exact source. The user can adjust the weights with sliders.
4. **Roadmap per career:** what the job is, the level of study, the most direct routes (university, apprenticeship, college), example courses with graduate earnings, the skills to build, and one first step for this month.
5. **Watchlist:** the user follows up to 5 careers and sees what changed when a new report is published. It is stored in the browser only, so no personal data is kept.

## Safeguards

- Careers with an interest fit below 0.5 are never shown, however high their demand.
- Missing data is shown as "no data" and never filled in.
- Every number is traceable to its source.

## Data sources

| Source | What it gives us |
| --- | --- |
| Skills England annual skills report 2026 and its 10 sector assessments | Priority occupations, projected growth to 2035 |
| Employer Skills Survey 2024 (and 2022 for the change feed) | Current skill-shortage vacancies |
| O*NET database and Interest Profiler | Interest profiles per occupation, interest quiz |
| Discover Uni dataset (HESA) | University courses, graduate outcomes and earnings, all UK |
| Skills England occupational maps API | Apprenticeships, T Levels, skills per occupation (England) |

Context only, not scored: the Temporary Shortage List and Skills Development Scotland Regional Skills Assessments.

## Responsible use of AI

- AI **never** decides the ranking; the scoring formula is deterministic.
- AI helps extract figures from report PDFs and suggest occupation code mappings; a person checks every row.
- An "Ask about this result" explainer answers only from our evidence, must cite it, and is checked by a validator.
- If AI is unavailable or wrong, the app falls back to template explanations and works fully without it.
- Option: run an open-weight model on our own GPU cluster (8 × A6000), so we do not depend on an external API.

## Architecture

Three separated layers:

- **Experience:** React and TypeScript
- **Decision:** Python, FastAPI, Pydantic
- **Data integration:** one adapter per source, with snapshot fallback

The work is API-first: the OpenAPI contract is written before the interface is built.

## What makes it different

Existing career tools ask "what are you like?". We also ask "where is the UK short of people?", and we join both answers with evidence the user can check.
