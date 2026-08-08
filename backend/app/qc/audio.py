import io
import math
import struct
import wave

from app.qc.base import QCResult

# Out of a max possible 16-bit amplitude of 32767. Cheap heuristic only -
# flags near-total silence, the signature of a TTS call that technically
# succeeded but produced nothing usable.
SILENCE_RMS_THRESHOLD = 200


def check_audio(audio_bytes: bytes) -> QCResult:
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        sample_width = wav_file.getsampwidth()
        raw = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2 or not raw:
        return QCResult(
            score=1.0, notes="Automated QC skipped (only 16-bit PCM WAV audio is inspected)."
        )

    samples = struct.unpack(f"<{len(raw) // 2}h", raw[: len(raw) - (len(raw) % 2)])
    if not samples:
        return QCResult(score=0.1, notes="Automated QC flagged: audio file contains no samples.")

    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    if rms < SILENCE_RMS_THRESHOLD:
        return QCResult(
            score=0.2, notes=f"Automated QC flagged: audio appears to be near-silent (RMS={rms:.0f})."
        )
    return QCResult(score=1.0, notes="Passed automated checks (audio is not silent).")
