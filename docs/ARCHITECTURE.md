# Architecture

Status: proposed, not yet implemented. See `docs/RESEARCH.md` and `docs/LICENSING.md`
for the findings this is based on.

## Stack

- **Frontend:** Next.js, TypeScript, React, Tailwind CSS.
- **Backend:** Python 3.12+, FastAPI, for AI orchestration.
- **Database:** SQLite via SQLAlchemy, modeled so PostgreSQL can be swapped in later
  without a rewrite.
- **Job queue:** database-backed jobs + a Python worker process. No Redis/Celery
  unless a concrete need appears later.
- **Media:** FFmpeg via subprocess (system binary, not vendored).
- **Storage:** local filesystem behind a small storage abstraction, so S3-compatible
  storage can be added later.
- **Containerization:** Docker, Docker Compose.

No Kubernetes, microservices, Kafka, or enterprise auth in v1 — this is a
single-operator creator tool, not a platform.

## Provider interfaces

Every AI capability sits behind an abstract interface with capability detection, so no
single model/vendor is load-bearing.

```python
class VideoProvider(ABC):
    def generate_text_to_video(self, spec: ShotSpec) -> GenerationResult: ...
    def generate_image_to_video(self, spec: ShotSpec, image: ImageAsset) -> GenerationResult: ...
    def generate_reference_video(self, spec: ShotSpec, references: list[CharacterReference]) -> GenerationResult: ...
    def generate_character_animation(self, spec: ShotSpec, driving_video: VideoAsset) -> GenerationResult: ...

    def supports_audio_conditioning(self) -> bool: ...
    def supports_reference_image(self) -> bool: ...
    def supports_seed(self) -> bool: ...
    def requires_driving_video(self) -> bool: ...   # added: true for Wan-Animate, false for TI2V-5B
    def estimate_vram(self, spec: ShotSpec) -> int: ...
    def estimate_cost(self, spec: ShotSpec) -> Decimal: ...
    def cancel_job(self, job_id: str) -> None: ...
```

The same pattern applies to `VoiceProvider`, `ImageProvider` (storyboards), `LLMProvider`,
`UpscaleProvider`, `LipSyncProvider`, and `ComputeProvider` (local vs rented-GPU
execution), matching the original brief. `requires_driving_video()` is the one
addition — the UI needs it to know when to ask for a performance source before
letting someone pick Wan-Animate for a shot.

### Default implementations (v1)

| Capability | Default | Secondary/alternate | Not implemented in v1 |
|---|---|---|---|
| Video | Wan2.2-TI2V-5B | Wan2.2-Animate-14B (selective, needs driving video) | LTX (licensing), HunyuanVideo (territorial restriction) |
| Voice | Chatterbox | CosyVoice2, Qwen3-TTS | — |
| Storyboard image | FLUX.1 `[schnell]` | Qwen-Image | FLUX.1 `[dev]` (non-commercial, never) |
| Lip-sync | MuseTalk | LatentSync (quality mode) | — |
| LLM — creative stages | Anthropic API | OpenAI-compatible | — |
| LLM — mechanical stages | Local via Ollama (optional) | Anthropic/OpenAI-compatible | — |
| Compute | Local | Rented GPU (RunPod/Vast.ai-style, vendor-agnostic `ComputeProvider`) | — |
| Testing | `MockVideoProvider`, `MockVoiceProvider`, `MockImageProvider` | — | — |

Mock providers generate dummy media files (correct duration/resolution/container) so
the entire pipeline — treatment through episode assembly — can be exercised without
downloading or running any real model. Demo Mode uses these by default.

## Repo structure

```
ai-cartoon-studio/                  (or whatever this repo is named)
  frontend/                         # Next.js / TypeScript / Tailwind
  backend/
    app/
      providers/
        video/                     # wan_ti2v.py, wan_animate.py, mock.py, base.py
        voice/                     # chatterbox.py, cosyvoice.py, qwen3_tts.py, mock.py
        image/                     # flux_schnell.py, qwen_image.py, mock.py
        llm/                       # anthropic.py, openai_compatible.py, ollama.py
        lipsync/                   # musetalk.py, latentsync.py
        upscale/
        compute/                   # local.py, remote_gpu.py
      models/                      # SQLAlchemy entities
      pipeline/                    # treatment -> outline -> script -> scenes -> shots
      jobs/                        # queue + worker
      qc/                          # automated quality checks
      assembler/                   # ffmpeg episode assembly, timeline, subtitles
      api/                         # FastAPI routers
    workflows/                     # versioned ComfyUI workflow JSON files
      wan_image_to_video.v1.json
      wan_character_animation.v1.json
      storyboard_generation.v1.json
      upscale.v1.json
      lip_sync.v1.json
    tests/
      unit/  api/  db/  jobs/  ffmpeg/
      providers/mocks/
  data/                            # gitignored — created at runtime
    series/SERIES_001/{series.json, characters/, voices/, locations/, props/}
    series/SERIES_001/episodes/EP_001/{script/, scenes/SCENE_001/shots/SHOT_001/{storyboard/,audio/,generations/,approved/}, episode_output/}
  docs/
  docker-compose.yml
  .env.example
```

## Database schema (entities and key relationships)

Field-level detail mostly matches the original brief's per-entity field lists (Series,
Character, Episode, Scene, Shot, etc. — those are correct as specified). What's added
here is the relationship shape that makes versioning and resumability actually work:

- `Series` 1—N `Character`, `Location`, `Prop`, `Voice`, `Episode`
- `Character` 1—N `CharacterReference` (categorized: front/side/3-4/full-body/
  close-up/happy/angry/sad/talking/sitting/walking/running/additional)
- `Character` 1—N `CharacterOutfit` (identity is separate from wardrobe, per the brief)
- `Location` 1—N `LocationReference` (categorized: wide/medium/close-bg/interior N-S-E-W)
- `Episode` 1—N `Scene` 1—N `Shot`
- `Shot` N—N `Character` via `ShotCharacter` (this join table carries the *outfit
  used in this specific shot*, which is what actually prevents wardrobe drift — the
  outfit assignment lives on the join, not on the character)
- `Shot` 1—N `Generation` — **every attempt is a row, never overwritten.** Each
  `Generation` carries seed, model + model version, workflow version, prompt, negative
  prompt, generation parameters, output paths, and a `status`. `Shot.active_generation_id`
  points at the one currently approved/in-use version.
- `Generation` 1—1 `GenerationJob` — the async wrapper (`QUEUED → PREPARING → RUNNING →
  PROCESSING → COMPLETE/FAILED/CANCELED`) with `created_at/started_at/completed_at`,
  error message, device, provider, and parameters. Keeping job state separate from
  generation/asset state is what makes a crash mid-render non-destructive: on restart,
  completed generations and approved shots are untouched; only `RUNNING` jobs with no
  corresponding completed output need reconciliation (mark as failed, offer retry).
- `AudioAsset` / `VideoAsset` / `ImageAsset` — attached to whichever `Generation`
  produced them; dialogue audio is additionally keyed by a content hash of
  (text, voice, settings) so identical dialogue is never regenerated.
- `ProviderConfiguration` / `ProjectSetting` — no API credentials in the database or
  git history; these tables store which provider is active per capability and
  non-secret settings, credentials come from environment variables (`.env`, never
  committed — `.env.example` documents the keys without values).

## Phased plan

Following the original brief's phase structure, with the deltas from `docs/RESEARCH.md`
folded in:

| Phase | Scope | Delta from original brief |
|---|---|---|
| 0 | Research & architecture | Done — see `docs/RESEARCH.md`, this file |
| 1 | App shell: frontend, FastAPI, SQLite, Series/Character/Episode CRUD, settings | none |
| 2 | Character Bible: references, outfits, voices, locations, props, asset storage | none |
| 3 | Story pipeline: treatment → outline → script → scenes → shots, LLM provider abstraction, manual editing | LLM routing split: creative stages default to cloud, mechanical stages can use local Ollama |
| 4 | Storyboard system: image provider abstraction, generation, approval, regeneration | Pin FLUX.1 `[schnell]` (not `[dev]`) or Qwen-Image as the implemented default |
| 5 | Voice system: provider abstraction, narration, dialogue, audio caching | Default to Chatterbox or CosyVoice2; implement Qwen3-TTS as a second provider, not the only one |
| 6 | Video system: provider interface, mock provider first, then Wan | **LTX dropped from v1 scope entirely.** Wan2.2-TI2V-5B is the only real provider implemented alongside the mock; Wan2.2-Animate-14B is added as a selective provider *after* the pilot proves the simpler path, gated behind a driving-video sourcing step |
| 7 | QC and approvals: preview, approve/reject/regenerate, active version, automated QC | none |
| 8 | Episode assembler: FFmpeg timeline, audio mix, titles, credits, subtitles, export | none |
| 9 | Pilot production: one real 1–3 minute pilot, **using TI2V-5B for every shot type, no Animate** | fix architecture based on findings before touching long-form |
| 10 | Long-form scaling: 30-minute target, batch/overnight queues, multi-episode season management | Introduce Wan-Animate here, once driving-video workflow is established and worth the added VRAM/complexity |

## Hardware guidance

| Workload | Where it runs | Approximate cost |
|---|---|---|
| Pilot (1–3 min), TI2V-5B only | One 24GB consumer GPU (RTX 3090/4090), local or rented | Rented: likely under $5 total, at ~$0.34–0.59/hr for a 4090 |
| Full-episode batch rendering, TI2V-5B | Same 24GB card, run overnight/in batches | Scales with regeneration rate, not just raw clip count |
| Wan-Animate at usable speed | Rented 80GB card (A100 ~$1.39/hr, H100 ~$2.89/hr) | Burst-rented, not owned |
| Storyboard images, voice, lip-sync | Comfortable on the same 24GB card or even smaller | Marginal |

Do not assume the user owns an RTX 4090 — the setup wizard (Phase 1) should detect
hardware and recommend Local vs Cloud GPU mode accordingly, per the original brief.

## Changes from the original brief, summarized

1. **Drop LTX from v1 entirely.** Its actual license (not the version some blogs
   describe) carries a revenue threshold and a non-compete clause relevant to this
   exact kind of product. Wan 2.2 already covers the need.
2. **Wan-Animate is secondary, not a default workhorse.** It requires a driving video;
   TI2V-5B is prompt/image-to-video and is the right default for most shots.
3. **Pin explicit choices for storyboard image (FLUX.1 `[schnell]` or Qwen-Image) and
   lip-sync (MuseTalk default, LatentSync for quality mode)** — the brief left these
   as unnamed provider slots.
4. **Split LLM usage by pipeline stage** (cloud for creative/continuity-sensitive
   stages, optional local for high-volume mechanical stages) rather than treating "the
   LLM" as one interchangeable choice.
5. **The pilot skips Wan-Animate entirely** — TI2V-5B plus a post-process lip-sync pass
   covers every shot type in the brief's suggested pilot (walking, close-up,
   two-character conversation), removing driving-video sourcing from the first
   milestone's critical path.
6. Everything else in the original brief — the Series/Character/Location/Prop Bible
   system, shot/scene/version data model, storyboard-approval gate, Thrifty/Quality
   modes, resumable job queue, mock providers and Demo Mode — is architecturally sound
   and unchanged.
