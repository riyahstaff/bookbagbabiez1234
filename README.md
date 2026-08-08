# AI Cartoon Studio

An open-source, budget-conscious production pipeline for generating character-consistent
animated episodes — from treatment to finished MP4 — without betting the whole app on
any single AI model vendor.

## Status: Phase 8 (Episode Assembler) complete

Phases 0-7 (research/architecture, app shell, Character Bible, story pipeline,
storyboard system, voice system, video system, automated QC) are done. Phase 8 is the
first time a shot's individually-approved assets actually become a watchable episode:
a new `assembler/` package (ffmpeg-based, the location docs/ARCHITECTURE.md reserved
for it from Phase 0) builds a timeline per episode - walking scenes/shots in order,
preferring each shot's active video over its held image, mixing dialogue and narration
audio underneath, skipping any shot with no renderable image or video and reporting
exactly which ones - then renders optional title and credits cards (Pillow), an
optional `.srt` from the same dialogue/narration text, concatenates everything with
ffmpeg, and soft-muxes the subtitles in. A new `EpisodeExport` row records every export
attempt (status, duration, which options were used, which shots were skipped, a link to
the rendered MP4), and `Episode.status` now actually moves through `RENDERING` and `QC`
around a real export instead of just existing as an unused enum value. The Episode page
has a new Export section: title/credits/subtitles checkboxes, an upfront skipped-shots
warning before you commit to exporting, a history of past exports with an inline
`<video controls>` player, download link, and delete. There is still no lip-sync pass or
job queue - generation and export are both still synchronous, deferred to pilot
production (Phase 9) per `docs/RESEARCH.md`.

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
