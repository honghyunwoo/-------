# Engineering Roadmap

## Scope And Mission
- Deliver a stable, production-ready version of the MoneyPrinter Turbo ("올빼미") platform.
- Eliminate crashes in media generation pipeline and stabilize API endpoints.
- Establish repeatable verification steps (automated tests + manual smoke scripts).

## Current Snapshot (2025-10-02)
- FastAPI backend with JWT auth, payments, video/subtitle/audio generation services.
- Config loader auto-copies `config.example.toml` -> `config.toml`; relies on TOML + environment overrides.
- Database layer defaults to SQLite via `USE_SQLITE=true`; PostgreSQL path exists but untested.
- Tests exist (`test_api.py`, legacy `test_*.py`, `tests/e2e/`) but not yet executed in this session.
- Significant custom services: `video.py`, `thumbnail_generator.py`, `material.py`, task management (`task.py`, `state.py`).

## Initial Issue Radar
- `VideoAspect.to_resolution` compares enum members to `.value`, so non-default branches never trigger; causes portrait fallback.
- Payment flow returns stubbed data (`Payment` response with hard-coded IDs) and mixes persistence logic between controller/service.
- `thumbnail_generator.py` imports `openai` inside function without guard; may break without dependency or API key.
- `material.py` persists downloaded media without sandboxing; lacks error resilience for request failures.
- Global state managers (`state.py`) rely on Redis config but do not validate connection; potential runtime crash when Redis enabled.
- Tests and services assume external binaries (FFmpeg, ImageMagick) and network APIs are present; need strategy for local testing.

## Immediate Next Steps
1. Run unit/API tests locally to capture failing cases and log errors.
2. Reproduce media pipeline manually on small fixture data to surface runtime exceptions.
3. Prioritize fixes (enum bug, auth/payment correctness, thumbnail generation robustness) and implement with targeted tests.
4. Document verification checklist (commands + expected outcomes) and automate where possible.

## Longer-Term Considerations
- Introduce dependency injection or configuration validation on startup to fail fast when keys/resources missing.
- Harden payment module with real persistence + external gateway abstraction for mocking.
- Add background task monitoring/cleanup for `task_manager` to prevent orphaned work folders.
- Expand logging/metrics once core flows stabilize.

## Open Questions For Product/Stakeholders
- What external APIs (OpenAI, Pexels, Toss Payments, etc.) must be supported in MVP scope?
- Are there legal/contractual requirements around storing generated media or user uploads?
- Do we need multi-tenant support or single-tenant is sufficient?
- What constitutes "done" for launch (feature list vs. reliability SLA)?

