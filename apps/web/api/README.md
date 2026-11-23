# Avenir app API

`api.application:app` is the served application. It combines the experience
endpoints with the canonical `/api/v1` decision API and wraps both in the shared
response envelope. It uses committed evidence and prepared guidance without API
keys or a live language model.

## Standalone backend and Vite development

From the repository root, with Python 3.12+ and Node 20+:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm --prefix apps/web ci
npm --prefix apps/web run api
```

The editable installation makes the local contracts, decision engine, adapters
and canonical API packages available to the assembled app. The backend listens
at `http://127.0.0.1:8015`. Its interactive API documentation is at
`http://127.0.0.1:8015/docs`.

In a second terminal, from the repository root:

```sh
npm --prefix apps/web run dev
```

Open `http://127.0.0.1:4175`. Vite proxies `/api` to port 8015, so browser requests
stay on the frontend's origin. Run only one backend on port 8015
and one frontend on port 4175 at a time. The equivalent direct backend command,
from `apps/web`, is:

```sh
../../.venv/bin/python -m uvicorn api.application:app --host 127.0.0.1 --port 8015
```

For the single-process production launcher and setup on Windows, see the
[root README](../../../README.md).

## Response contract

Both API layers return `{ok, data, error, meta}`. Read successful payloads from
`data`; errors contain a code, message and field details. Metadata contains the
request ID, evidence date and source statuses. Unknown occupations return HTTP 404;
invalid inputs return HTTP 422. A snapshot-backed response can succeed while reporting
snapshot or missing source status.

For example, this request exercises the canonical decision endpoint:

```sh
curl -sS http://127.0.0.1:8015/api/v1/recommendations \
  -H 'Content-Type: application/json' \
  -d '{"profile":{"interests":["maths","design"],"nation":"scotland"},"first_idea":"architect"}'
```

## Experience endpoints

- `GET /api/health`: status, curated-career count, ML mode, guide mode and text-to-speech status.
- `GET /api/bootstrap`: 21 curated profiles (20 matched careers plus plumber),
  tags, original source registry, backtest, crises, evidence metadata and data status.
  `evidence_metadata` carries the source schema version, CPIH price base and a
  readable price label; full career profiles retain it for charts and exports.
- `GET /api/catalogue`: 412 lightweight occupation summaries for Jobs. Pay and
  employee-job counts retain their source and observation year; any older count
  is explicitly marked as the last available historical observation.
- `GET /api/careers/{soc}`: full occupation profile with exact supplied metrics,
  history and top-five hedge candidates. Current missing observations remain
  null; a separate display observation may show an older employee-job count.
- `POST /api/matches`: tags and pay/interest/need weights produce 20 ranked
  careers with supplied calibrated interest affinities. Plumber and the broader
  catalogue remain available for evidence browsing.
- `POST /api/discovery`: known-direction or exploring answers produce three
  options within the 20-career matching set, with assumptions and caveats.
- `GET /api/path/{soc}?nation=Scotland`: curated pathway example where available.
  Related-pathway bridges are disclosed. Course earnings remain null so
  illustrative prototype values do not replace occupation evidence. Unsupported
  routes return HTTP 404.
- `GET /api/careers/{soc}/evidence-pack`: one compact, display-ready object per
  role with the statistics from the ML analysis: pay (median and middle half),
  employee jobs, the 2022-2025 employment trend against the typical occupation,
  automation exposure with its research range, history for 2011/2015/2019/2022
  and the latest year (real and nominal pay, jobs, price base and the 2021
  recoding caveat), the top three hedge careers, this role's results in the
  historical rule checks, each crisis check with its placebo result, fit tags,
  sources and `allowed_numbers`. Each metric carries its source, year, status,
  flags and the exact caveat sentences the app shows. Missing data stays `null`
  with a one-line reason.
- `POST /api/guide`: `{ "soc": "2134", "message": "What skills can I build?",
  "history": [] }` returns source-linked guidance and explicitly identifies its
  mode (`llm_grounded` or `prepared_demo`), `ai_written`, `model`, `based_on`
  (the stat lines the pack supplied) and `checks` (`passed` or
  `fallback: <reason>`). Broader profiles disclose unavailable detailed routes.

## Grounded guide

With no model configured the guide is the prepared template. When a model is
configured, the reply is written by the model from the role's evidence pack only
(the pack minus `allowed_numbers`, the last six turns and the question), with a
system prompt that forbids numbers outside the pack, forecasts, probabilities of
job loss, graduate salaries and "you should". Configuration uses the LLM
writer's variables, `LLM_ENABLED`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`
(OpenAI-compatible chat completions), or `ANTHROPIC_API_KEY` with
`LLM_BASE_URL` empty for the Anthropic Messages API (`LLM_MODEL` or
`claude-sonnet-5-5`, 600 output tokens). The repo-root `.env` is loaded at app
start by the adapter registry without overriding real environment variables.
Before a reply is accepted, every number in it must appear in the pack's
`allowed_numbers`, it must avoid the banned phrases ("you should", "don't",
"guarantee", "will earn", "probability"), be non-empty and be under 1,200
characters. Any failed check, timeout (20 s), HTTP error or exception falls back
to the prepared reply with the reason in `checks`; logs and responses never
carry the key, the URL or the prompt. Only the evidence pack is cached (per
SOC); nothing from a conversation is kept.

## Guide tools

When a model is configured, `POST /api/guide` gives it read-only tools
(`guide_tools.py`) so it fetches the app's own data itself before answering. The
backend runs every tool from data already loaded; no tool writes or uses the network:

- `get_role_stats(soc)`: the role's evidence pack summary (pay, jobs, trend,
  automation exposure, Occupations in Demand rating, hedges, crisis checks) with sources.
- `search_jobs(query?, min_pay?, demand?, limit<=8)`: catalogue roles by title words,
  minimum median pay and demand rating (`Critical`, `Elevated`, `Not in high demand`,
  read from the same table as the Jobs page), sorted by demand rating, then median pay.
- `compare_roles(socs)`: up to three roles side by side.
- `get_career_path(soc)`: the same structure as the response's `path`.
- `get_employer(name)`: only BlackRock, from `apps/web/public/employers/blackrock.json`
  (ways in, career ladder, how pay works, sources); nothing beyond the file.

The loop allows 2 tool rounds plus the final answer (each round is one request, to
fit free-tier quotas), within a 25 s total deadline. With tools on, the prompt
carries only the role's headline metrics, not the whole pack; the model calls tools
for the rest. A reply is accepted only if every number in it appears in the pack or
in a tool result, plus the existing checks. Unknown tools and bad arguments come
back to the model as `{"error": ...}`; any transport error, timeout or failed check
falls back to the prepared reply with the reason in `checks`. OpenAI-compatible
endpoints use `tools` with `tool_choice: "auto"`; Anthropic uses its
`tool_use`/`tool_result` blocks.

The response adds `tools_used: [{name, args, summary}]` (for example
`get_role_stats(2134): pay, jobs, trend, exposure, demand, 3 hedges`; empty for a
prepared reply) and `cached`. Every existing field stays.

Keys and quota: set `LLM_API_KEY` and optionally `LLM_API_KEY_2`. On HTTP 429 or
403 the same request is retried once with the other key, and the exhausted key is
skipped for the rest of the process.

Cache: accepted model replies (text, model, tools used, checks; never links or the
path, which are rebuilt per request) are stored on disk, keyed by sha256 of every
input the model sees: SOC, message, follow-up history, quiz profile, model name, a
digest of the evidence given to the model, and a cache version. A different
follow-up context, profile, model or evidence change is a different key; an
identical repeat request replays the stored reply without spending quota
(`cached: true`). The key-free prepared fallback is deterministic and never cached.
Writes use a unique temporary file and an atomic replace, and a missing or
unwritable folder is ignored. The default folder is `apps/web/api/.cache/guide/`
(git-ignored); set `GUIDE_CACHE_DIR` to move it or `GUIDE_CACHE=0` to turn it off.

Enable with a Gemini key in the repo-root `.env`:

```
LLM_ENABLED=1
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_API_KEY=<your key>
LLM_MODEL=gemini-3.5-flash-lite
```

`gemini-3.5-flash-lite` (free tier 500 requests a day) is the default;
`gemini-3.8-flash` gives higher-quality replies but allows 20 requests a day.
`/api/health` and `/api/bootstrap` are unchanged; `guide_mode` already says
`llm_grounded` when a model is configured.

The canonical API also provides `/api/v1/tags`, `/api/v1/careers`,
`/api/v1/profile`, `/api/v1/recommendations`, history, hedges, routes, sources and
backtests. Inspect `/docs` or `/openapi.json` for their exact input/output models.
Canonical ranking excludes unreviewed sample catalogue metrics and route rows;
missing inputs reduce evidence coverage and confidence. Production scoring also
withholds crisis measures whose supplied `show_on_card` policy is false, including
the 2008 and cost-of-living measures that failed the placebo check. The raw
bootstrap and career evidence retain these observations and their crisis checks
for inspection. The decision engine itself is unchanged.

## Employer outreach

`POST /api/outreach/draft` with `{ "soc": "2134", "employer": "blackrock",
"message"?: "<= 2000 chars", "name"?: "<= 80 chars", "route"?: "university" | "apprenticeship" }`
returns `{to, subject, body, mailto, form_url, employer_contact, note}`. Frontend
contract: on "Make a first connection", show an editable `<textarea>` prefilled from
`plan.alumni.template` (or `template_apprenticeship` for the apprenticeship route),
send the edited text as `message`, then open `mailto` if it is set, otherwise
`form_url` in a new tab, and show `note` and `employer_contact.source`/`checked`.
Without `message` the body is the same template with the employer, role and first
kit question filled in; `[degree]`, `[university]` and `[Your name]` stay for the
student to edit. Control characters are stripped and the body is capped at 2,000
characters; bad input returns HTTP 422 and an unknown SOC 404. The server never
sends email or posts forms. The contact is read from
`public/employers/blackrock.json` (`contact`, checked 18 Oct 2026): BlackRock's
careers site publishes no general enquiry email, so the route is its official
"Talent Community for students & graduates" form, `mailto` is `null` and
`form_url` is set. `mailto` (RFC 6068, `%20` spaces, `%0D%0A` newlines) is used
only if a verified email contact is added later.

## Text to speech

`POST /api/tts` reads one guide answer aloud with Gemini's native speech model.
Body: `{"text": "...", "voice": "Kore"}`. `text` is 1 to 1,500 characters and
`voice` is one of `Kore` (default), `Puck`, `Charon`, `Aoede`; anything else,
or text that is empty once markdown and URLs are removed, returns HTTP 422.
Markdown links are read as their label; bare URLs, headings, bullets and
emphasis marks are dropped. The reply is JSON, not raw bytes, because the
assembled app wraps every experience route in the `{ok, data, error, meta}`
envelope: `data` is `{mime_type: "audio/wav", audio_base64, voice, model, cached}`.

Keys come from `GEMINI_API_KEY`, then `GEMINI_API_KEY_2`, then `LLM_API_KEY`
when `LLM_BASE_URL` points at generativelanguage.googleapis.com. The key is sent
in the `x-goog-api-key` header and never appears in logs, URLs or responses.
The model is `TTS_MODEL` (default `gemini-3.8-flash-tts`), falling back once to
`gemini-2.5-flash-preview-tts` on 404, 5xx or when every key is out of quota for
the first model; that model's raw 24 kHz 16-bit PCM is wrapped in a WAV header.
The whole call has a 20 s deadline.

The free tier allows only 3 requests a minute and 10 a day per key and model.
A key that returns 429 is retried once with the other key and remembered as
spent for the process (60 s for a per-minute limit); a 401/403 key is skipped
for the process. Audio is cached in memory (64 entries) and on disk in
`data/cache/tts/` (or `TTS_CACHE_DIR`; the folder writes its own `.gitignore`),
keyed by model, voice and the cleaned text, so rehearsed answers replay instantly
and free across restarts, even without a key. With no key, or every key spent,
the route answers HTTP 503: on `api.main` the detail is
`{"code": "TTS_UNAVAILABLE", "message": "<short reason>"}`; through the assembled
app it is the envelope's standard error with `ok: false`. `GET /api/health` and
the bootstrap `data_status` report `tts` (a key is configured) and
`tts_quota_note`.

Frontend contract: a small speaker button under each guide answer POSTs
`{text}` to `/api/tts`. On 200, play
`new Audio(URL.createObjectURL(blob))`, where `blob` is
`new Blob([Uint8Array.from(atob(data.audio_base64), c => c.charCodeAt(0))], {type: "audio/wav"})`.
On 503 (or any other failure) fall back to `window.speechSynthesis` with a
`SpeechSynthesisUtterance` of the same text. That fallback is the normal path
once the day's quota is spent, not an error to show.

## Evidence and matching coverage

The imported ML evidence revision is Arsenii's `41a55f4` (contract v1.2), with
tax-year CPIH, relative demand, purity flags and revised uncertainty. Evidence covers
412 occupations; histories span 2007–2025 with employee-job counts from 2011.
The 2021 occupation-code break, older-code bridges, wider-group estimates,
provisional values and missing observations retain their supplied flags and
notes. Pay covers full-time employees; each employee-job metric states its own
coverage. Self-employed workers require separate evidence.

The experience matcher uses the 20-career affinity set. Fit is the mean supplied
tag affinity; pay and need use available median-pay and observed-demand
percentile ranks. Scores run 0–100. Missing inputs are excluded from the weighted
mean and all-zero weights use equal importance. Demand describes historical
employee-job change relative to the typical occupation over the supplied period,
rather than predicting future vacancies. Fit/hedge status, method,
evaluation limits and real/mock origin are reported in the payload. Unknown tags
return HTTP 422. Curated study routes, university examples and opportunities retain
their coverage notes; they are not a live calendar or university ranking.

## Verification

From the repository root:

```sh
.venv/bin/python -m pytest apps/web/api/tests -q
.venv/bin/python -m pytest
```

The app tests cover the assembled envelope, both API layers, no-key decisions,
static UI and raw internal experience behavior. The repository suite covers the
underlying packages. `api.main:app` is the internal experience app used by some
low-level tests; use `api.application:app` when serving the complete product.
