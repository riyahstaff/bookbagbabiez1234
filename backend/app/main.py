from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    character_outfits,
    character_references,
    characters,
    episodes,
    locations,
    props,
    scenes,
    series,
    shots,
    voices,
)
from app.api.routers import settings as settings_router
from app.config import DATA_DIR, get_settings

app_settings = get_settings()

app = FastAPI(title="AI Cartoon Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(series.router)
app.include_router(characters.router)
app.include_router(episodes.router)
app.include_router(settings_router.router)
app.include_router(character_references.router)
app.include_router(character_outfits.router)
app.include_router(voices.router)
app.include_router(locations.router)
app.include_router(props.router)
app.include_router(scenes.router)
app.include_router(shots.router)

# Uploaded reference images/audio live under data/series/... Mounted at /media
# rather than serving all of data/ directly, so the sqlite file (a sibling of
# series/, not inside it) is never reachable over HTTP.
media_root = DATA_DIR / "series"
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_root)), name="media")
