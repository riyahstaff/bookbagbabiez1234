# Workflows

ComfyUI node graphs, kept as versioned data files separate from the provider
code that submits them (`app/providers/image/comfyui.py`). Never edit a
workflow file that's in active use - copy it to a new version number instead,
per the "don't silently overwrite working workflows" principle in
`docs/ARCHITECTURE.md`.

Placeholders a provider fills in before submitting: `{{PROMPT}}`,
`{{NEGATIVE_PROMPT}}`, `{{SEED}}`, `{{WIDTH}}`, `{{HEIGHT}}`, and (video only)
`{{FRAME_COUNT}}`, `{{REFERENCE_IMAGE}}`.

## storyboard_generation.v1.json

A standard checkpoint-based Stable-Diffusion-family text-to-image graph
(`CheckpointLoaderSimple` → `CLIPTextEncode` x2 → `EmptyLatentImage` →
`KSampler` → `VAEDecode` → `SaveImage`). The sampler settings (4 steps, cfg 1.0,
euler/simple) match FLUX.1-schnell's fast-inference recommendation.

**Verify before real use, not yet tested against a live ComfyUI server:**

- Set `ckpt_name` to a checkpoint file actually present in your ComfyUI
  `models/checkpoints/` directory.
- This graph assumes a single merged checkpoint file loadable via
  `CheckpointLoaderSimple`. If your FLUX.1-schnell (or Qwen-Image) download is
  split into separate UNET/CLIP/VAE files - the more common Hugging Face
  packaging - replace node `4` with `UNETLoader` + `DualCLIPLoader` and wire
  the model/clip/vae outputs to nodes `3`/`6`/`7`/`8` accordingly. ComfyUI's
  own example workflow for your specific model is the most reliable source
  for the exact node names and parameters.
- This repo's dev environment has no GPU, so this workflow has only been
  checked for valid JSON structure and correct placeholder substitution -
  not run against real inference. Everything else in this phase (versioning,
  approval, the mock-backed workflow) has been.

## video_generation.v1.json

An image-to-video graph for Wan2.2-TI2V-5B, modeled on kijai's
`ComfyUI-WanVideoWrapper` node naming (`WanVideoModelLoader` →
`WanVideoTextEncode` + `WanVideoImageToVideoEncode` → `WanVideoSampler` →
`WanVideoDecode` → `VHS_VideoCombine`), the most widely-used community
integration for Wan video models in ComfyUI as of when this was written.
`ComfyUIVideoProvider` (`app/providers/video/comfyui.py`) uploads the shot's
approved storyboard image via ComfyUI's `/upload/image` endpoint and wires
the resulting filename into node `1`'s `image` input before submitting.

**Verify before real use - this is the least certain workflow in the repo:**

- Set both `REPLACE_WITH_YOUR_WAN2.2_TI2V_5B_CHECKPOINT.safetensors` (node
  `2`) and `REPLACE_WITH_YOUR_WAN_VAE.safetensors` (node `3`) to files
  actually present in your ComfyUI install.
- Node names/params for Wan video wrappers change faster and vary more than
  the standard Stable-Diffusion-family nodes the image workflow uses -
  `WanVideoWrapper` is not the only community package, versions drift, and a
  node pack update can rename inputs. Cross-check against the example
  workflow shipped with whichever node pack you actually install.
- `VHS_VideoCombine` (from `ComfyUI-VideoHelperSuite`) is assumed for the
  final encode step; if you use a different combine/save node, the output
  may land under a different history key than `videos`/`gifs`/`images` -
  `ComfyUIVideoProvider._poll_for_result` checks those three, but a
  non-standard node might use another one entirely.
- Like the image workflow, this has only been checked for valid JSON
  structure and correct placeholder substitution in this GPU-less
  environment, not run against real inference.
