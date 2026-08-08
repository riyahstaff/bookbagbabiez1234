import io

from PIL import Image, ImageStat

from app.qc.base import QCResult

# Cheap heuristics only - no aesthetic/content model. These catch the kind of
# hard failure a broken pipeline actually produces (a blank/solid frame, or
# one that's essentially all-black or all-white), not subjective quality.
BLANK_STDDEV_THRESHOLD = 5.0
DARK_MEAN_THRESHOLD = 10.0
BRIGHT_MEAN_THRESHOLD = 245.0


def check_image(image_bytes: bytes) -> QCResult:
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    stat = ImageStat.Stat(image)
    stddev = stat.stddev[0]
    mean = stat.mean[0]

    if stddev < BLANK_STDDEV_THRESHOLD:
        return QCResult(
            score=0.2,
            notes=f"Automated QC flagged: image appears blank or a solid color (stddev={stddev:.1f}).",
        )
    if mean < DARK_MEAN_THRESHOLD:
        return QCResult(
            score=0.3, notes=f"Automated QC flagged: image appears almost entirely black (mean={mean:.1f})."
        )
    if mean > BRIGHT_MEAN_THRESHOLD:
        return QCResult(
            score=0.3,
            notes=f"Automated QC flagged: image appears almost entirely white/blown out (mean={mean:.1f}).",
        )
    return QCResult(score=1.0, notes="Passed automated checks (no blank or blown-out frame detected).")
