import json
import time
import uuid
from pathlib import Path

import httpx

from app.providers.image.base import ImageGenerationResult, ImageProvider

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "workflows"


class ComfyUIImageProvider(ImageProvider):
    """Calls a running ComfyUI server's HTTP API. The workflow graph itself
    lives in workflows/storyboard_generation.v1.json, not in this file -
    swap models/nodes by editing that file, not this code.

    IMPORTANT: this client follows ComfyUI's documented /prompt, /history,
    /view API contract, but has not been exercised against a live GPU-backed
    ComfyUI server in this environment (no GPU here). Before real use, verify
    the bundled workflow JSON's node graph actually matches your installed
    checkpoint - see the comment at the top of that file.
    """

    def __init__(self, base_url: str, workflow_path: Path | None = None):
        self.base_url = base_url.rstrip("/")
        self.workflow_path = workflow_path or (WORKFLOWS_DIR / "storyboard_generation.v1.json")
        self.model_name = self.workflow_path.stem

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        width: int = 1024,
        height: int = 576,
        reference_image_bytes: bytes | None = None,
    ) -> ImageGenerationResult:
        seed_used = seed if seed is not None else int(time.time() * 1000) % (2**31 - 1)
        workflow = json.loads(self.workflow_path.read_text())
        _fill_workflow_placeholders(workflow, prompt, negative_prompt or "", seed_used, width, height)

        client_id = str(uuid.uuid4())
        with httpx.Client(timeout=300) as client:
            response = client.post(
                f"{self.base_url}/prompt", json={"prompt": workflow, "client_id": client_id}
            )
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]

            image_info = self._poll_for_result(client, prompt_id)
            image_response = client.get(
                f"{self.base_url}/view",
                params={
                    "filename": image_info["filename"],
                    "subfolder": image_info.get("subfolder", ""),
                    "type": image_info.get("type", "output"),
                },
            )
            image_response.raise_for_status()
            return ImageGenerationResult(
                image_bytes=image_response.content, seed_used=seed_used, model_name=self.model_name
            )

    def _poll_for_result(self, client: httpx.Client, prompt_id: str, timeout_seconds: int = 300) -> dict:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            history_response = client.get(f"{self.base_url}/history/{prompt_id}")
            history_response.raise_for_status()
            entry = history_response.json().get(prompt_id)
            if entry:
                for node_output in entry.get("outputs", {}).values():
                    images = node_output.get("images")
                    if images:
                        return images[0]
            time.sleep(2)
        raise TimeoutError(f"ComfyUI did not finish prompt {prompt_id} within {timeout_seconds}s")


def _fill_workflow_placeholders(
    workflow: dict, prompt: str, negative_prompt: str, seed: int, width: int, height: int
) -> None:
    """Fills the {{PROMPT}} / {{NEGATIVE_PROMPT}} / {{SEED}} / {{WIDTH}} /
    {{HEIGHT}} placeholders the bundled workflow JSON uses, wherever they
    appear in any node's inputs."""
    replacements: dict[str, object] = {
        "{{PROMPT}}": prompt,
        "{{NEGATIVE_PROMPT}}": negative_prompt,
        "{{SEED}}": seed,
        "{{WIDTH}}": width,
        "{{HEIGHT}}": height,
    }
    for node in workflow.values():
        inputs = node.get("inputs", {})
        for key, value in list(inputs.items()):
            if isinstance(value, str) and value in replacements:
                inputs[key] = replacements[value]
