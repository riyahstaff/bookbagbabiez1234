import json
import time
import uuid
from pathlib import Path

import httpx

from app.providers.video.base import VideoGenerationResult, VideoProvider

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "workflows"


class ComfyUIVideoProvider(VideoProvider):
    """Calls a running ComfyUI server's HTTP API for image-to-video
    generation (Wan2.2-TI2V-5B via a ComfyUI video node pack - see
    workflows/README.md). Unlike ComfyUIImageProvider, this also uploads the
    reference image via ComfyUI's documented /upload/image endpoint before
    submitting the prompt, since the workflow starts from a LoadImage node
    fed by that upload rather than a blank latent.

    IMPORTANT: same caveat as ComfyUIImageProvider, plus one more - this
    follows ComfyUI's documented /prompt, /history, /upload/image, /view API
    contract, but has not been exercised against a live GPU-backed server (no
    GPU in this environment). The exact node graph for a Wan2.2 video model
    varies more than the image case does, depending on which community video
    node pack is installed (e.g. kijai's ComfyUI-WanVideoWrapper) and which
    node saves the output (VHS_VideoCombine, SaveAnimatedWEBP, or a native
    SaveVideo node depending on ComfyUI version) - _poll_for_result checks a
    few plausible output keys, but verify the bundled workflow JSON against
    your actual installation before relying on it.
    """

    def __init__(self, base_url: str, workflow_path: Path | None = None):
        self.base_url = base_url.rstrip("/")
        self.workflow_path = workflow_path or (WORKFLOWS_DIR / "video_generation.v1.json")
        self.model_name = self.workflow_path.stem

    def generate_video(
        self,
        prompt: str,
        reference_image_bytes: bytes,
        negative_prompt: str | None = None,
        seed: int | None = None,
        duration_seconds: float | None = None,
        width: int = 1280,
        height: int = 720,
    ) -> VideoGenerationResult:
        seed_used = seed if seed is not None else int(time.time() * 1000) % (2**31 - 1)
        fps = 24
        frame_count = max(16, round((duration_seconds or 4.0) * fps))
        workflow = json.loads(self.workflow_path.read_text())

        with httpx.Client(timeout=600) as client:
            reference_image_name = self._upload_reference_image(client, reference_image_bytes)
            _fill_workflow_placeholders(
                workflow,
                prompt=prompt,
                negative_prompt=negative_prompt or "",
                seed=seed_used,
                width=width,
                height=height,
                frame_count=frame_count,
                reference_image_name=reference_image_name,
            )

            client_id = str(uuid.uuid4())
            response = client.post(
                f"{self.base_url}/prompt", json={"prompt": workflow, "client_id": client_id}
            )
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]

            video_info = self._poll_for_result(client, prompt_id)
            video_response = client.get(
                f"{self.base_url}/view",
                params={
                    "filename": video_info["filename"],
                    "subfolder": video_info.get("subfolder", ""),
                    "type": video_info.get("type", "output"),
                },
            )
            video_response.raise_for_status()
            extension = Path(video_info["filename"]).suffix.lstrip(".") or "mp4"
            return VideoGenerationResult(
                video_bytes=video_response.content,
                model_name=self.model_name,
                file_extension=extension,
                duration_seconds=frame_count / fps,
            )

    def _upload_reference_image(self, client: httpx.Client, image_bytes: bytes) -> str:
        filename = f"{uuid.uuid4().hex}.png"
        response = client.post(
            f"{self.base_url}/upload/image",
            files={"image": (filename, image_bytes, "image/png")},
            data={"type": "input", "overwrite": "true"},
        )
        response.raise_for_status()
        payload = response.json()
        subfolder = payload.get("subfolder")
        return f"{subfolder}/{payload['name']}" if subfolder else payload["name"]

    def _poll_for_result(self, client: httpx.Client, prompt_id: str, timeout_seconds: int = 600) -> dict:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            history_response = client.get(f"{self.base_url}/history/{prompt_id}")
            history_response.raise_for_status()
            entry = history_response.json().get(prompt_id)
            if entry:
                for node_output in entry.get("outputs", {}).values():
                    for key in ("videos", "gifs", "images"):
                        media = node_output.get(key)
                        if media:
                            return media[0]
            time.sleep(3)
        raise TimeoutError(f"ComfyUI did not finish prompt {prompt_id} within {timeout_seconds}s")


def _fill_workflow_placeholders(
    workflow: dict,
    prompt: str,
    negative_prompt: str,
    seed: int,
    width: int,
    height: int,
    frame_count: int,
    reference_image_name: str,
) -> None:
    """Fills the {{PROMPT}} / {{NEGATIVE_PROMPT}} / {{SEED}} / {{WIDTH}} /
    {{HEIGHT}} / {{FRAME_COUNT}} / {{REFERENCE_IMAGE}} placeholders the
    bundled workflow JSON uses, wherever they appear in any node's inputs."""
    replacements: dict[str, object] = {
        "{{PROMPT}}": prompt,
        "{{NEGATIVE_PROMPT}}": negative_prompt,
        "{{SEED}}": seed,
        "{{WIDTH}}": width,
        "{{HEIGHT}}": height,
        "{{FRAME_COUNT}}": frame_count,
        "{{REFERENCE_IMAGE}}": reference_image_name,
    }
    for node in workflow.values():
        inputs = node.get("inputs", {})
        for key, value in list(inputs.items()):
            if isinstance(value, str) and value in replacements:
                inputs[key] = replacements[value]
