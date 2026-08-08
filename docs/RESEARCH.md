# Phase 0 Research

Verified 2026-08-08 against official repositories, Hugging Face model cards, and
license files — not marketing pages. See `docs/LICENSING.md` for the full license
table; this document covers capability, hardware, and workflow implications.

## Video generation

**Wan2.2-TI2V-5B — primary provider.** Apache 2.0, dense 5B model, unified
text-to-video and image-to-video in one checkpoint, 720p @ 24fps. Runs on a single
24GB consumer GPU (RTX 4090/3090); FP8-quantized fits 8–12GB. This is a genuinely good
pick for an indie budget and the brief's instinct to start with the smallest practical
model was correct.

**Wan2.2-Animate-14B — secondary/selective provider.** Also Apache 2.0. This is a
character *performance-transfer* model, not a prompt-to-video model: the pipeline
extracts pose and face keypoints from a **driving video** (via DWPose/ViTPose
whole-body detection), encodes identity from a single reference image, and synthesizes
a video that matches the driving motion while preserving the reference character's
identity. It can also do full character *replacement* in existing footage.

Implication for this project: you need a source of driving video for any shot that
uses Animate — someone (the creator, on webcam) acting out the scene, or a pose
library/mocap source. This is a real workflow requirement the original brief didn't
mention. Recommendation: **do not put Animate on the critical path for the pilot.**
Use TI2V-5B for every shot type in the first milestone (including dialogue — get lip
accuracy from a separate lip-sync pass over the generated audio instead). Introduce
Animate later, specifically for performance-critical close-ups, once a driving-video
source is set up and the simpler pipeline is proven.

Hardware: official guidance is 80GB VRAM; `--offload_model`, `--convert_model_dtype`,
and `--t5_cpu` bring it onto a 24GB card at reduced speed. Practical production
throughput on Animate wants a rented 80GB card (A100/H100).

**Wan 2.5 / 2.6 / 2.7 do not exist as open weights.** Alibaba pre-announced 2.5 as
open; the weights never shipped. 2.6 (Dec 2025) is a commercial API product on
Alibaba Cloud's Bailian platform only. These versions add exactly the features this
project wants most — native audio-video sync and multi-shot character consistency —
and Alibaba is monetizing them exclusively through the paid API rather than
open-sourcing them. Concretely: **the open-weight ecosystem has not solved
multi-shot character consistency**, which is precisely why this project's Character
Bible / reference-conditioning system is doing real work, not just nice-to-have
polish. Don't expect a future open Wan release to make that infrastructure
unnecessary.

**LTX-2 (Lightricks) — not implementing in v1.** See `docs/LICENSING.md` — the
license is proprietary with a revenue threshold and (more relevantly, regardless of
revenue) a clause against use in products that compete with Lightricks' own commercial
offerings. Wan 2.2 already covers the technical need without this ambiguity, so there's
no upside to taking on the licensing risk right now. Keep the `VideoProvider`
abstraction ready for it (or any other provider) in case that changes.

**HunyuanVideo (Tencent) — not recommended as primary.** Technically capable, but its
license excludes the EU, UK, and South Korea entirely and gates large-scale commercial
use behind Tencent's discretionary approval. Mentioned here mainly as an example of
"looks open, isn't unconditionally" — exactly the kind of thing the brief asked to
watch for.

## Voice / TTS

**Qwen3-TTS is real and open** (`QwenLM/Qwen3-TTS`, Apache 2.0, 0.6B and 1.7B variants,
Base/CustomVoice/VoiceDesign configurations, weights on Hugging Face). This was worth
confirming rather than assuming — Alibaba keeps its DashScope TTS API and some Wan
versions closed while open-sourcing this one. It's very new as of 2026 with no long
production track record.

**More battle-tested permissive alternatives exist and are recommended as the initial
default:**
- **Chatterbox** (`resemble-ai/chatterbox`, MIT) — zero-shot voice cloning from ~5
  seconds of reference audio, built-in emotion-exaggeration control, widely used and
  benchmarked against closed competitors. Embeds a PerTh watermark in all output by
  default; disclose this in the app's voice-consent UI.
- **CosyVoice2** (`FunAudioLLM/CosyVoice`, Apache 2.0) — ~150ms streaming latency,
  strong multilingual and cross-lingual cloning.

Recommendation: implement Chatterbox (or CosyVoice2) as the default `VoiceProvider`,
and add Qwen3-TTS as a second implementation behind the same interface for
side-by-side evaluation, rather than betting the whole voice pipeline on the newest
option.

## Storyboard / image generation

Not named in the original brief — needed a pick. Both of these are genuinely Apache
2.0 with no caveats:
- **FLUX.1 `[schnell]`** (`black-forest-labs/FLUX.1-schnell`) — recommended default.
- **Qwen-Image** (`Qwen/Qwen-Image`) — strong alternative, notably good at rendering
  legible in-image text (useful for title cards, signage props).

**Trap to avoid:** FLUX.1 `[dev]` — the higher-quality sibling of `schnell` that most
tutorials recommend — is under a **non-commercial** license from Black Forest Labs.
Same "FLUX" family name, different rights. Make sure whichever engineer/config picks
the FLUX variant knows this; it's an easy way to accidentally ship a non-commercial
model in a commercial pipeline.

## Lip-sync

Also not named in the brief.
- **MuseTalk** (`TMElyralab/MuseTalk`, MIT) — recommended default. Fast, lightweight,
  no commercial restrictions.
- **LatentSync** (`bytedance/LatentSync`, Apache 2.0) — higher-fidelity diffusion-based
  alternative, heavier compute cost. Good "quality mode" option.

## Orchestration — ComfyUI

GPL-3.0, confirmed. The license only reaches code that modifies ComfyUI directly
(anything living in `custom_nodes/`); an independent application that calls a running
ComfyUI instance over its HTTP API is not a derivative work and isn't bound by GPL.
Workflow `.json` files are data, not code, and carry no license obligation. This
matches the brief's own plan (treat ComfyUI as an external backend service, never
expose its raw complexity to the user) — that plan happens to also be the
license-safe architecture, so no change needed, just confirmed.

## LLM orchestration

The brief's request (configurable provider, support Anthropic API / OpenAI-compatible
/ local Ollama) is architecturally right, but treating "the LLM" as one interchangeable
slot for every pipeline stage is a mistake worth correcting before coding:

- **Creative stages** (treatment → series/season/episode outline → screenplay) need to
  track the Series Bible and Character Bible for continuity over long context, and
  creative-writing quality differences between a frontier cloud model and a local 7–30B
  model are large and visible in the output. Call volume here is low (a handful of
  calls per episode). Recommendation: default these stages to a cloud LLM (Anthropic
  or an OpenAI-compatible frontier model).
- **Mechanical stages** (turning an approved scene into structured shot-list JSON,
  assembling per-shot prompts from bible data) are a much easier task with much higher
  call volume. A local model via Ollama is a reasonable default here if the user wants
  zero marginal cost, and quality differences matter less.

Implement one `LLMProvider` interface either way — this is a routing/config decision
(which provider handles which pipeline stage), not a second abstraction.

## GPU / cost reality

Rented GPU pricing as of 2026 (RunPod on-demand; Vast.ai marketplace is often cheaper
for the same hardware):
- RTX 4090: ~$0.34–0.59/hr
- A100 (80GB): ~$1.39/hr
- H100: ~$2.89/hr

**Pilot (1–3 minutes):** fully coverable on one 24GB consumer GPU locally, or a few
hours of rented 4090 time — likely under $5 total including retries, if Animate is
kept off the critical path as recommended above.

**Full episode / season production:** TI2V-5B stays comfortable on a 24GB card.
Wan-Animate at usable throughput wants a rented 80GB card, used in bursts for
batch/overnight rendering rather than owned outright.

These are order-of-magnitude planning numbers, not guarantees — actual generation time
per shot depends on step count, resolution, and settings, and should be measured
directly once the pipeline exists rather than assumed from a spec.

The bigger cost lever in practice is **regeneration count from rejected shots**, not
raw per-clip compute — which is why the storyboard-approval gate is load-bearing for
the budget, not optional polish.
