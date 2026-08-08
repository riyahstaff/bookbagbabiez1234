import io
import random

from PIL import Image, ImageDraw

from app.providers.video.base import VideoGenerationResult, VideoProvider


class MockVideoProvider(VideoProvider):
    """Animates the given reference image - a real, decodable animated GIF,
    not empty/fake bytes - so the approval workflow has something to
    actually play without a GPU or downloaded model weights. A slow zoom
    across frames stands in for real image-to-video motion; the prompt and
    seed are baked in as a text overlay on every frame, same convention as
    MockImageProvider/MockVoiceProvider.

    GIF rather than mp4/webm: this dev environment has no ffmpeg binary and
    no other video muxer, and Mock providers must work with zero setup. The
    frontend renders .gif via <img> and real providers' mp4/webm via <video>,
    dispatched on Generation.output_path's extension.
    """

    FPS = 6
    ZOOM_AMOUNT = 0.08

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
        seed_used = seed if seed is not None else random.randint(0, 2**31 - 1)
        seconds = max(1.0, min(6.0, duration_seconds or 4.0))
        frame_count = max(2, round(seconds * self.FPS))

        base = Image.open(io.BytesIO(reference_image_bytes)).convert("RGB").resize((width, height))

        frames = []
        for i in range(frame_count):
            zoom = 1.0 + self.ZOOM_AMOUNT * (i / max(1, frame_count - 1))
            cropped_w, cropped_h = int(width / zoom), int(height / zoom)
            left, top = (width - cropped_w) // 2, (height - cropped_h) // 2
            frame = base.crop((left, top, left + cropped_w, top + cropped_h)).resize((width, height))

            draw = ImageDraw.Draw(frame)
            draw.rectangle([8, 8, width - 8, height - 8], outline="white", width=3)
            draw.text((24, 24), "MOCK VIDEO (no real model called)", fill="white")
            draw.text((24, height - 32), f"seed={seed_used} frame={i + 1}/{frame_count}", fill="white")
            frames.append(frame)

        buffer = io.BytesIO()
        frames[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=round(1000 / self.FPS),
            loop=0,
        )
        return VideoGenerationResult(
            video_bytes=buffer.getvalue(),
            model_name="mock-video-v1",
            file_extension="gif",
            duration_seconds=frame_count / self.FPS,
        )
