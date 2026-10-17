# API contract (v1, draft)

**Owner:** Yehor. Status: **draft, adopted from spec section 7**. Freeze target: Sat 20:30.
Change it only by PR with "needs a contract change" ticked. Backend generates the OpenAPI
schema from these models; the frontend generates its client from that schema.

## Envelope (every response)

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {
    "as_of": "2026-10-18",
    "request_id": "7f3c...",
    "sources": [
      { "name": "ashe", "status": "live | snapshot | missing", "as_of": "2025", "region": "UK" }
    ]
  }
}
```

On failure: `ok: false`, `data: null`,
`error: { "code": "...", "message": "...", "details": [{ "field": "...", "issue": "..." }] }`.

| Code | HTTP | When |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | Input fails the schema, slider out of range, unknown field |
| `NOT_FOUND` | 404 | Unknown SOC code or year |
| `UPSTREAM_UNAVAILABLE` | 503 | A live source is down **and** no snapshot exists |
| `INTERNAL` | 500 | Anything else |

Serving a snapshot is **not** an error: `200`, `ok: true`, that source's `status: "snapshot"`.

## Endpoints

| Method and path | In | Out |
| --- | --- | --- |
| `GET /health` | | each source's status |
| `POST /api/v1/profile` | interests[], free_text (≤300 chars), qualifications[], location, automation_worry (0 to 1) | confirmed tags, head start |
| `POST /api/v1/recommendations` | profile, first_idea (SOC or text) | three `Pick`s, `Hedge`, comparison vs first idea, explanation, sources |
| `GET /api/v1/careers/{soc}` | | full `Career` with provenance |
| `GET /api/v1/careers/{soc}/hedge` | | `Hedge` |
| `GET /api/v1/backtest?year=2015` | year 2010 to 2019 | `BacktestYear` |
| `GET /api/v1/routes/{soc}?nation=scotland` | nation: england, scotland, wales, ni | `Route[]` |
| `GET /api/v1/sources` | | name, licence, version, retrieved, status, coverage |

## Models

**Metric** (every number):
`{ value, low, high, source, year, region, granularity: "occupation"|"group"|"estimate", n, confidence: "high"|"medium"|"low" }`.
A missing metric is `{ value: null, ..., confidence: "low" }` and the UI shows "missing".

**Career**
```
soc2020, isco08[], esco_id, title,
metrics {
  pay_now, pay_early, pay_ceiling, pay_growth_10y, pay_spread,
  demand_trend, shortage, ads_now,
  exposure_ilo, exposure_inhouse,
  wellbeing, stress
}                       # each a Metric
```

**Profile**: `interests[], tags_confirmed[], free_text, qualifications[], location, automation_worry`

**Pick**: `tier: "ambitious"|"safe"|"balanced", career: Career, components {fit, return, market_risk, disruption_risk, risk}, vs_first_idea {component: delta}, trade_off: str`

**Hedge**: `soc2020, title, shared_skills[], skill_overlap, risk_delta`

**BacktestYear**: `year, tiers [{tier, occupations[], median_pay_growth_5y, share_employment_decline, worst_case}], caveats[]`

**Route**: `nation, kind: "degree"|"graduate_apprenticeship"|"apprenticeship"|"college", name, entry_requirements, url, source`

**Roadmap**: `steps [{order, title, detail, route?}]` (three steps), `first_step_this_month`

## Validation
All inputs schema-validated with Pydantic, unknown fields rejected, lists capped,
free text capped at 300 characters, slider bounded 0 to 1.
