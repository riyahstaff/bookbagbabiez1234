from app.providers.lipsync.base import LipSyncProvider, LipSyncResult


class MockLipSyncProvider(LipSyncProvider):
    """Zero-cost, zero-setup default. There's no cheap way to actually fake
    lip movement, so this returns the input video byte-for-byte unchanged -
    it exists so the generate-lipsync endpoint and its approval/versioning
    flow are exercisable without a real provider configured, same as every
    other Mock provider in this codebase."""

    def sync_lips(self, video_bytes: bytes, video_file_extension: str, audio_bytes: bytes) -> LipSyncResult:
        return LipSyncResult(
            video_bytes=video_bytes, model_name="mock-lipsync-v1", file_extension=video_file_extension
        )
