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


class CharacterReferenceCategory(str, enum.Enum):
    FRONT = "FRONT"
    SIDE = "SIDE"
    THREE_QUARTER = "THREE_QUARTER"
    FULL_BODY = "FULL_BODY"
    CLOSE_UP = "CLOSE_UP"
    HAPPY = "HAPPY"
    ANGRY = "ANGRY"
    SAD = "SAD"
    TALKING = "TALKING"
    SITTING = "SITTING"
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    ADDITIONAL = "ADDITIONAL"


class LocationReferenceCategory(str, enum.Enum):
    WIDE_ESTABLISHING = "WIDE_ESTABLISHING"
    MEDIUM = "MEDIUM"
    CLOSE_BACKGROUND = "CLOSE_BACKGROUND"
    INTERIOR_NORTH = "INTERIOR_NORTH"
    INTERIOR_SOUTH = "INTERIOR_SOUTH"
    INTERIOR_EAST = "INTERIOR_EAST"
    INTERIOR_WEST = "INTERIOR_WEST"
    ADDITIONAL = "ADDITIONAL"


class SceneStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SHOTS_READY = "SHOTS_READY"


class ShotType(str, enum.Enum):
    ESTABLISHING = "ESTABLISHING"
    EXTREME_WIDE = "EXTREME_WIDE"
    WIDE = "WIDE"
    MEDIUM = "MEDIUM"
    MEDIUM_CLOSE_UP = "MEDIUM_CLOSE_UP"
    CLOSE_UP = "CLOSE_UP"
    EXTREME_CLOSE_UP = "EXTREME_CLOSE_UP"
    OVER_THE_SHOULDER = "OVER_THE_SHOULDER"
    TWO_SHOT = "TWO_SHOT"
    REACTION_SHOT = "REACTION_SHOT"
    INSERT_SHOT = "INSERT_SHOT"
    POV = "POV"
    TRACKING = "TRACKING"
    PAN = "PAN"
    TILT = "TILT"
    STATIC = "STATIC"


class GenerationType(str, enum.Enum):
    IMAGE = "IMAGE"  # storyboard (Phase 4)
    VIDEO = "VIDEO"  # Phase 6 - same table, not built yet


class GenerationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
