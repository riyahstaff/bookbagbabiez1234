# Licensing

Verified 2026-08-08 by checking official repositories and license files directly
(not third-party summaries — several blog posts about this space are out of date or
simply wrong; two examples are called out below). **Re-verify before any commercial
release** — this space changes fast, and licenses can change between minor model
versions from the same vendor.

Do not assume "open weights" means unrestricted commercial use. Several entries below
look permissive from a distance and are not.

| Software / Model | Repository | License | Commercial use | Revenue / scale restrictions | Attribution required | Redistribution | Notes |
|---|---|---|---|---|---|---|---|
| Wan2.2-TI2V-5B | `Wan-Video/Wan2.2` (GitHub), `Wan-AI` (Hugging Face) | Apache 2.0 | Yes, unrestricted | None | Standard Apache notice | Yes | **Primary video provider.** Runs on one 24GB consumer GPU (RTX 4090/3090) at 720p/24fps; FP8-quantized fits 8–12GB. |
| Wan2.2-Animate-14B | `Wan-Video/Wan2.2` | Apache 2.0 | Yes, unrestricted | None | Standard Apache notice | Yes | Secondary/selective video provider. **Requires a driving video** (pose + face extraction from footage of a performance) plus a reference image — it is not prompt-to-video. Official guidance: 80GB VRAM; runs on 24GB with `--offload_model`/`--convert_model_dtype`/`--t5_cpu` at reduced speed. |
| LTX-2 | `Lightricks/LTX-2` | **LTX-2 Community License** (proprietary, not open-source despite "open weights" framing) | Restricted | Entities with ≥$10,000,000 annual revenue must obtain a **paid** commercial license from Lightricks | Required | Restricted | Also **prohibits use in any product/service that competes with Lightricks' own commercial offerings** (e.g. LTX Studio) — this clause is relevant to this project regardless of revenue. Violation penalty is 2x owed license fees. Some SEO blog posts claim a newer "LTX-2.3" shipped Apache 2.0; the actual `LICENSE` file in the official repo does not say that. **Not implemented in v1.** |
| Qwen3-TTS (0.6B / 1.7B, Base/CustomVoice/VoiceDesign) | `QwenLM/Qwen3-TTS` (official Qwen org), weights on Hugging Face | Apache 2.0 | Yes | None | Standard | Yes | Open weights confirmed real (this was worth double-checking — Alibaba keeps some Qwen audio products API-only). Very new as of 2026 with no long production track record — implement as a **secondary** voice provider, not the only one. |
| CosyVoice2 (0.5B) | `FunAudioLLM/CosyVoice` | Apache 2.0 | Yes | None | Standard | Yes | Alibaba FunAudioLLM team. ~150ms streaming latency, strong multilingual + cross-lingual voice cloning. |
| Chatterbox | `resemble-ai/chatterbox` | MIT | Yes | None | Not required | Yes | **Recommended default voice provider.** Zero-shot cloning from ~5s audio, built-in emotion-exaggeration control, well battle-tested. Embeds a PerTh watermark in output by default — disclose this to users. |
| MuseTalk | `TMElyralab/MuseTalk` | MIT | Yes | None | Not required | Yes | **Recommended default lip-sync provider.** Fast, lightweight. |
| LatentSync | `bytedance/LatentSync` | Apache 2.0 | Yes | None | Standard | Yes | Higher-fidelity lip-sync alternative to MuseTalk; diffusion-based, heavier. |
| FLUX.1 `[schnell]` | `black-forest-labs/FLUX.1-schnell` | Apache 2.0 | Yes | None | Standard | Yes | **Recommended storyboard/image provider.** |
| FLUX.1 `[dev]` | `black-forest-labs/FLUX.1-dev` | Non-Commercial license | **No** | N/A — commercial use not permitted without a separate agreement with Black Forest Labs | Required | Restricted | **Do not use for commercial output.** Same "FLUX" family name as schnell, different rights — common trap, flagged explicitly so nobody grabs the wrong one later. |
| Qwen-Image | `Qwen/Qwen-Image` (Hugging Face) | Apache 2.0 | Yes | None | Standard | Yes | Alt storyboard provider; notably strong at rendering legible in-image text (title cards, signage props). |
| HunyuanVideo | `Tencent-Hunyuan/HunyuanVideo` | Tencent Hunyuan Community License | Conditional | Large-scale commercial use (>100M MAU) requires Tencent's discretionary sign-off | Required, must disclose Tencent is not affiliated with/endorsing the service | Restricted | **Territory explicitly excludes the EU, UK, and South Korea entirely.** Not recommended as a primary provider — Wan already covers the need without this restriction. |
| Wan 2.5 / 2.6 / 2.7 | — | Proprietary, hosted API only (Alibaba Bailian) | N/A | N/A | N/A | N/A | **No open weights published, ever, for these versions** — 2.5 was pre-announced as open and the weights never appeared. Alibaba is monetizing exactly the features this project wants most (multi-shot narrative consistency, native audio-video sync) exclusively through the paid API. Don't plan around these becoming open. |
| ComfyUI | `Comfy-Org/ComfyUI` (formerly `comfyanonymous/ComfyUI`) | GPL-3.0 | Yes, if used as an external service | None | N/A (not distributing modified ComfyUI source) | N/A | Code that lives inside `custom_nodes/` and modifies ComfyUI directly is a GPL derivative. An independent application that only calls a running ComfyUI instance over its HTTP API is **not** bound by GPL. Workflow `.json` files are data, not code, and carry no license obligation either way. **Architecture requirement: never vendor/fork ComfyUI's Python source into this app.** |
| FFmpeg | ffmpeg.org | LGPL/GPL, depends on build configuration | Yes | None | Depends on build | Depends on build | Use the system `ffmpeg` binary via subprocess (standard practice); avoid statically linking GPL-only-configured builds into anything redistributed as a single binary. |
| Next.js / React / Tailwind CSS / FastAPI / SQLAlchemy | — | MIT / BSD (standard OSS) | Yes | None | Standard | Yes | Application framework layer — no concerns. |

## Two corrections worth flagging explicitly

1. **LTX licensing is more restrictive than the original brief assumed, and more
   restrictive than several current blog posts claim.** The brief said "verify current
   license" before implementation — doing so surfaced both a revenue threshold and a
   non-compete clause that specifically names the kind of product this repository is
   building. Recommendation: don't implement LTX at all in v1. Wan 2.2 already covers
   the technical need.
2. **Qwen3-TTS turned out to be real and open**, which was worth confirming rather than
   assuming — Alibaba keeps some of its audio/video lineup (Wan 2.5/2.6, the DashScope
   TTS API) closed while open-sourcing adjacent models under the same brand. License
   status has to be checked per-model, not per-vendor.
