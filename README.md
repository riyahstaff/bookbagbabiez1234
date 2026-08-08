# AI Cartoon Studio

An open-source, budget-conscious production pipeline for generating character-consistent
animated episodes — from treatment to finished MP4 — without betting the whole app on
any single AI model vendor.

## Status: Phase 6 (Video System) complete

Phases 0-5 (research/architecture, app shell, Character Bible, story pipeline,
storyboard system, voice system) are done. Phase 6 adds video: a `VideoProvider`
abstraction (a deterministic Mock provider that animates the shot's own approved
reference image with a simple zoom and a prompt/seed text overlay, saved as a real
animated GIF since this dev environment has no ffmpeg/muxer available - the default so
the app works with zero GPU; and a ComfyUI provider for Wan2.2-TI2V-5B, the
Apache-2.0 image-to-video model `docs/RESEARCH.md` recommends, with Wan2.2-Animate
deliberately deferred past the pilot per the phased plan). Video generation reuses the
same `Generation`/versioning/approval infrastructure again - a shot can now have an
active image, dialogue take, narration take, and video all at once - and enforces the
"storyboard before video" rule directly in the API: generating video is blocked with a
409 unless the shot's active storyboard image is approved, with an explicit
override for a human who wants to skip ahead anyway. Frontend renders GIF output via
`<img>` and real mp4/webm via `<video>`, dispatched on the file extension. There is
still no lip-sync, QC automation, or episode assembly - that starts in Phase 7 (QC and
approvals) and Phase 8 (episode assembler).

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
