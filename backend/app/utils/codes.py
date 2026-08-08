import re

from sqlalchemy.orm import Session


def slugify_upper(text: str) -> str:
    """Turn a free-text name into an UPPER_SNAKE_CASE slug for use in a code like CHAR_MARCUS_001."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text.strip()).strip("_").upper()
    return slug or "UNTITLED"


def generate_unique_code(db: Session, model: type, column, base: str, width: int = 3) -> str:
    """Find the first unused `{base}_{NNN}` code, e.g. SERIES_001, CHAR_MARCUS_002."""
    sequence = 1
    while True:
        candidate = f"{base}_{sequence:0{width}d}"
        if not db.query(model).filter(column == candidate).first():
            return candidate
        sequence += 1
