# AI Cartoon Studio

An open-source, budget-conscious production pipeline for generating character-consistent
animated episodes — from treatment to finished MP4 — without betting the whole app on
any single AI model vendor.

## Status: Phase 0 (Research & Architecture) — awaiting approval to begin Phase 1

This repository currently contains **no application code**. It contains the Phase 0
research and architecture deliverables: a verified survey of the current open-weight
model landscape (video, voice, image, lip-sync), the licensing implications of each,
and the proposed system architecture. Implementation begins only after these are
reviewed and approved.

- [`docs/RESEARCH.md`](docs/RESEARCH.md) — current model landscape, verified licenses and hardware requirements
- [`docs/LICENSING.md`](docs/LICENSING.md) — license table for every model/tool under consideration
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — provider interfaces, repo layout, database schema, phased plan

## Design philosophy

1. **Provider-agnostic.** Every AI capability (video, voice, image, upscaling, lip-sync,
   LLM, compute) sits behind an abstract interface with capability detection. No single
   model vendor is load-bearing — this space moves fast enough that betting on one
   model's continued existence is a real risk (see `docs/RESEARCH.md` for a concrete
   example: Alibaba's newest Wan versions are closed API-only).
2. **Local-first, cloud-optional.** The MVP pilot must run end-to-end on a single
   consumer GPU (or a few dollars of rented GPU time). Heavier workloads (batch
   rendering, higher-end models) can burst to rented cloud GPUs, never require them.
2. **Storyboard before video.** Cheap image generation gates expensive video
   generation. This is the single highest-leverage cost control in the whole system
   and is never optional, even in "quality mode."
3. **Series → Episode → Scene → Shot → Version is the fundamental hierarchy.** Nothing
   in the UI, database, or job system should be designed in a way that breaks this.
4. **Human approval before expensive rendering.** Nothing generates video without an
   approved storyboard unless a human explicitly overrides that.
5. **Never lose work.** Every generation is versioned and preserved (including
   rejected ones, until explicit cleanup). Jobs are resumable after a crash.

## License

Repository/application license: **TBD** — to be decided by the project owner before
any public release. This is independent of the licenses on the third-party models the
app talks to (see `docs/LICENSING.md`), which apply regardless of how this repo itself
is licensed.
