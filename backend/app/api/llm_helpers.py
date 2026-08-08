from fastapi import HTTPException

from app.pipeline.structured import StructuredGenerationError


def run_llm_stage(fn, *args, **kwargs):
    """Translate LLM/provider failures into a clean API error instead of a raw 500,
    per the "translate technical failures into understandable messages" principle."""
    try:
        return fn(*args, **kwargs)
    except StructuredGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The AI provider failed to respond: {exc}") from exc
