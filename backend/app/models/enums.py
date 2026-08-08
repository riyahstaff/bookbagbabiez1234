import enum


class EpisodeStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCRIPT_READY = "SCRIPT_READY"
    SCENES_READY = "SCENES_READY"
    STORYBOARD_READY = "STORYBOARD_READY"
    RENDERING = "RENDERING"
    QC = "QC"
    COMPLETE = "COMPLETE"


class ProviderCapability(str, enum.Enum):
    VIDEO = "VIDEO"
    VOICE = "VOICE"
    IMAGE = "IMAGE"
    LLM = "LLM"
    UPSCALE = "UPSCALE"
    LIPSYNC = "LIPSYNC"
    COMPUTE = "COMPUTE"
