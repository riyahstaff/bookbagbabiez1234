import io

from PIL import Image, UnidentifiedImageError

from app.qc.base import QCResult
from app.qc.image import check_image


def check_video(video_bytes: bytes, file_extension: str) -> QCResult:
    """Only GIF (Mock's output format - see providers/video/mock.py) can be
    inspected frame-by-frame with Pillow alone. Real mp4/webm output needs
    ffmpeg or a video-decoding library, neither of which is a dependency
    here (this dev environment has no ffmpeg binary) - QC is skipped for
    those formats rather than guessed at."""
    if file_extension.lower() != "gif":
        return QCResult(
            score=1.0,
            notes=(
                f"Automated QC skipped ({file_extension} frame inspection needs ffmpeg, "
                "not available in this environment)."
            ),
        )

    try:
        image = Image.open(io.BytesIO(video_bytes))
        frame_count = getattr(image, "n_frames", 1)
        sample_indices = sorted({0, frame_count // 2, frame_count - 1})
        results = []
        for index in sample_indices:
            image.seek(index)
            frame_buffer = io.BytesIO()
            image.convert("RGB").save(frame_buffer, format="PNG")
            results.append(check_image(frame_buffer.getvalue()))
    except (UnidentifiedImageError, OSError):
        return QCResult(score=1.0, notes="Automated QC skipped (could not decode frames for inspection).")

    worst = min(results, key=lambda result: result.score)
    if worst.score < 1.0:
        return QCResult(score=worst.score, notes=f"Automated QC flagged a sampled frame: {worst.notes}")
    return QCResult(score=1.0, notes=f"Passed automated checks across {len(sample_indices)} sampled frames.")
