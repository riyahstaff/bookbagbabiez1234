from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import characters, episodes, series
from app.api.routers import settings as settings_router
from app.config import get_settings

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
