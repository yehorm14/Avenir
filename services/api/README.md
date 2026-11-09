# services/api (Backend slice)

FastAPI + Pydantic v2 implementing `docs/contracts.md`: envelope, error codes, validation.
Loads JSON artefacts from `snapshots/` at start; calls adapters, never files or the network directly.
Must start and serve the demo with no API keys (snapshot mode).
