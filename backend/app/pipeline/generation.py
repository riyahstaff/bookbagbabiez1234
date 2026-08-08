from app.models import Character, Episode, Location, Scene, Series
from app.pipeline.prompts import (
    build_outline_prompt,
    build_scene_breakdown_prompt,
    build_script_prompt,
    build_shot_breakdown_prompt,
)
from app.pipeline.schemas import SceneBreakdown, ShotBreakdown
from app.pipeline.structured import generate_structured
from app.providers.llm.base import LLMProvider


def generate_episode_outline(llm: LLMProvider, episode: Episode, series: Series) -> str:
    system, user = build_outline_prompt(episode, series)
    return llm.generate(system, user)


def generate_episode_script(
    llm: LLMProvider, episode: Episode, series: Series, characters: list[Character]
) -> str:
    system, user = build_script_prompt(episode, series, characters)
    return llm.generate(system, user)


def generate_scene_breakdown(
    llm: LLMProvider,
    episode: Episode,
    series: Series,
    characters: list[Character],
    locations: list[Location],
) -> SceneBreakdown:
    system, user = build_scene_breakdown_prompt(episode, series, characters, locations)
    result = generate_structured(llm, system, user, SceneBreakdown)
    assert isinstance(result, SceneBreakdown)
    return result


def generate_shot_breakdown(
    llm: LLMProvider, scene: Scene, series: Series, characters_in_scene: list[Character]
) -> ShotBreakdown:
    system, user = build_shot_breakdown_prompt(scene, series, characters_in_scene)
    result = generate_structured(llm, system, user, ShotBreakdown)
    assert isinstance(result, ShotBreakdown)
    return result
