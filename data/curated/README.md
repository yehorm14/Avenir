# data/curated/

Hand-made tables that are committed. Every row needs `verified_by` (a team member's
initials) before the ETL will load it; empty `verified_by` fails the load.

- `occupations.csv`: the 20 demo occupations (candidate list from the spec, team to confirm).
  List columns use `|`. `interest_tags` and `entry_subjects` must use the vocab in
  `packages/contracts/avenir_contracts/vocab.py`.
  Codes are deliberately empty: fill SOC 2020 from the ONS coding index, ISCO-08 via
  SOC 2010 (see `data/manifest.yaml`), ESCO from the ESCO download. Never guess a code.
  `mapping_quality`: `one_to_one` or `many_to_many` (many-to-many lowers confidence).
- `ilo_exposure.csv` (to add): rows from WP140 Annex Table A1 for the ISCO codes we use.
- `routes.csv`: routes in by nation, one per row, copied by a person from the real page (header only until
  then). `nation` and `kind` use `vocab.Nation` / `vocab.RouteKind`; `url` must be `https://`; `source` names the
  site; `provider` may be empty. Build with `python -m avenir_etl.build` (it validates before writing).

Editing in Excel: save with `Save As > CSV UTF-8 (Comma delimited)`; plain "CSV" is not UTF-8 and the build rejects it.
