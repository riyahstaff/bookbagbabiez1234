# Workflows

ComfyUI node graphs, kept as versioned data files separate from the provider
code that submits them (`app/providers/image/comfyui.py`). Never edit a
workflow file that's in active use - copy it to a new version number instead,
per the "don't silently overwrite working workflows" principle in
`docs/ARCHITECTURE.md`.

Placeholders a provider fills in before submitting: `{{PROMPT}}`,
`{{NEGATIVE_PROMPT}}`, `{{SEED}}`, `{{WIDTH}}`, `{{HEIGHT}}`.

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
