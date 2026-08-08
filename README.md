# AI Cartoon Studio

An open-source, budget-conscious production pipeline for generating character-consistent
animated episodes — from treatment to finished MP4 — without betting the whole app on
any single AI model vendor.

## Status: Phase 4 (Storyboard System) complete

Phases 0-3 (research/architecture, app shell, Character Bible, story pipeline) are
done. Phase 4 adds the first image generation capability: an `ImageProvider`
abstraction (a deterministic Mock provider that draws a real placeholder PNG with the
prompt and seed baked in, the default so the app works with zero GPU/API keys; and a
ComfyUI HTTP provider for FLUX.1-`schnell`-class local/self-hosted models), a
deterministic shot-prompt builder (Series visual style + per-character Bible
descriptions + location + this shot's own camera/action/lighting fields — no LLM call
needed), and the storyboard workflow itself: generate any number of versions per shot,
each kept as its own row (nothing is auto-deleted, including failed attempts), with
approve/reject/activate actions and exactly one active version per shot. The Scene
view shows each shot's active-version thumbnail and approval status at a glance. There
is still no voice or video generation - that starts in Phase 5 (voice) and Phase 6
(video).

- [`docs/RESEARCH.md`](docs/RESEARCH.md) — current model landscape, verified licenses and hardware requirements
- [`docs/LICENSING.md`](docs/LICENSING.md) — license table for every model/tool under consideration
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — provider interfaces, repo layout, database schema, phased plan

## Running it

**With Docker (recommended):**

```
docker compose up --build
```

Frontend at http://localhost:3000, API at http://localhost:8000. Both bind to
localhost only, per the security default in `docs/ARCHITECTURE.md`.

**Manually, for development:**

```
# Backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to
`frontend/.env.local` if you need to override any defaults - both work unmodified for
local development.

Run the backend test suite with `.venv/bin/pytest` from `backend/`.

## Design philosophy

1. **Provider-agnostic.** Every AI capability (video, voice, image, upscaling, lip-sync,
   LLM, compute) sits behind an abstract interface with capability detection. No single
   model vendor is load-bearing — this space moves fast enough that betting on one
   model's continued existence is a real risk (see `docs/RESEARCH.md` for a concrete
   example: Alibaba's newest Wan versions are closed API-only).
2. **Local-first, cloud-optional.** The MVP pilot must run end-to-end on a single
   consumer GPU (or a few dollars of rented GPU time). Heavier workloads (batch
   rendering, higher-end models) can burst to rented cloud GPUs, never require them.
3. **Storyboard before video.** Cheap image generation gates expensive video
   generation. This is the single highest-leverage cost control in the whole system
   and is never optional, even in "quality mode."
4. **Series → Episode → Scene → Shot → Version is the fundamental hierarchy.** Nothing
   in the UI, database, or job system should be designed in a way that breaks this.
5. **Human approval before expensive rendering.** Nothing generates video without an
   approved storyboard unless a human explicitly overrides that.
6. **Never lose work.** Every generation is versioned and preserved (including
   rejected ones, until explicit cleanup). Jobs are resumable after a crash.

## License

Repository/application license: **TBD** — to be decided by the project owner before
any public release. This is independent of the licenses on the third-party models the
app talks to (see `docs/LICENSING.md`), which apply regardless of how this repo itself
is licensed.
