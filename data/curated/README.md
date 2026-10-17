# data/curated/

Hand-made tables that are committed. Every row needs `verified_by` (a team member's
initials) before the ETL will load it; empty `verified_by` fails the load.

- `occupations.csv`: the 20 demo occupations (candidate list from the spec, team to confirm).
  Codes are deliberately empty: fill SOC 2020 from the ONS coding index, ISCO-08 via
  SOC 2010 (see `data/manifest.yaml`), ESCO from the ESCO download. Never guess a code.
  `mapping_quality`: `one_to_one` or `many_to_many` (many-to-many lowers confidence).
- `ilo_exposure.csv` (to add): rows from WP140 Annex Table A1 for the ISCO codes we use.
- `routes.csv` (to add): routes in by nation, each with a source URL.
