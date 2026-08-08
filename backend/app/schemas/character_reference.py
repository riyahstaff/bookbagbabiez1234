from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CharacterReferenceCategory


class CharacterReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    character_id: int
    category: CharacterReferenceCategory
    image_path: str
    notes: str | None = None
    created_at: datetime
