from dataclasses import dataclass


@dataclass
class QCResult:
    """Advisory only - never blocks approve/reject/activate. Surfaced to a
    human reviewer so they don't have to open every generation to spot an
    obvious failure."""

    score: float  # 1.0 = no issues found, down to 0.0 = clear problem detected
    notes: str
