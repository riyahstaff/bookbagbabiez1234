from app.models import Character, Episode, Location, Scene, Series

SHOT_TYPES = (
    "ESTABLISHING, EXTREME_WIDE, WIDE, MEDIUM, MEDIUM_CLOSE_UP, CLOSE_UP, EXTREME_CLOSE_UP, "
    "OVER_THE_SHOULDER, TWO_SHOT, REACTION_SHOT, INSERT_SHOT, POV, TRACKING, PAN, TILT, STATIC"
)


def _series_bible(series: Series) -> str:
    parts = [f"Series: {series.title} ({series.genre or 'genre unspecified'})"]
    if series.animation_style:
        parts.append(f"Animation style: {series.animation_style}")
    if series.description:
        parts.append(f"Premise: {series.description}")
    if series.world_details:
        parts.append(f"World details: {series.world_details}")
    if series.continuity_rules:
        parts.append(f"Continuity rules you must never break: {series.continuity_rules}")
    return "\n".join(parts)


def build_outline_prompt(episode: Episode, series: Series) -> tuple[str, str]:
    system = (
        f"You are a professional writer for an animated series.\n{_series_bible(series)}\n\n"
        "Write a clear, act-based episode outline (a beat sheet) - not full dialogue yet."
    )
    user = (
        f"Episode {episode.episode_number}: {episode.title}\n\n"
        f"Treatment / premise for this episode:\n{episode.treatment or '(none provided)'}\n\n"
        "Write an episode outline (3-5 short acts/beats) based on this treatment."
    )
    return system, user


def build_script_prompt(episode: Episode, series: Series, characters: list[Character]) -> tuple[str, str]:
    character_lines = "\n".join(
        f"- {c.name}: {c.description or 'no description yet'}" for c in characters
    ) or "(no characters defined yet)"
    system = (
        f"You are a professional writer for an animated series.\n{_series_bible(series)}\n\n"
        "Established characters (only introduce a new one if the story absolutely requires it):\n"
        f"{character_lines}\n\n"
        "Write a screenplay-formatted script: sluglines (INT./EXT. LOCATION - TIME), character names "
        "in caps before their dialogue, and brief action lines."
    )
    user = (
        f"Episode outline:\n{episode.outline or '(none provided)'}\n\n"
        f"Original treatment:\n{episode.treatment or '(none provided)'}\n\n"
        "Write the full script for this episode."
    )
    return system, user


def build_scene_breakdown_prompt(
    episode: Episode, series: Series, characters: list[Character], locations: list[Location]
) -> tuple[str, str]:
    character_names = ", ".join(c.name for c in characters) or "(none defined yet)"
    location_names = ", ".join(l.name for l in locations) or "(none defined yet)"
    system = (
        "You are a script supervisor breaking a finished script into a structured scene list for "
        "animation production. Respond with ONLY valid JSON, no other text, matching exactly this "
        'shape: {"scenes": [{"scene_number": int, "location_name": string or null, "time_of_day": '
        'string or null, "characters_present": [string], "action_description": string or null, '
        '"dialogue": string or null, "narration": string or null, "emotional_tone": string or null, '
        '"estimated_duration_seconds": int or null}]}\n\n'
        f"Known characters: {character_names}\n"
        f"Known locations: {location_names}\n"
        "Prefer these exact names when a scene uses them - do not invent new characters or locations."
    )
    user = f"Script:\n{episode.script or '(none provided)'}\n\nBreak this script into scenes."
    return system, user


def build_shot_breakdown_prompt(
    scene: Scene, series: Series, characters_in_scene: list[Character]
) -> tuple[str, str]:
    character_names = ", ".join(c.name for c in characters_in_scene) or "(none listed for this scene)"
    system = (
        "You are a storyboard artist breaking a single scene into a shot list for animation. Respond "
        'with ONLY valid JSON, no other text, matching exactly this shape: {"shots": [{"shot_number": '
        'int, "shot_type": string, "camera_angle": string or null, "camera_movement": string or null, '
        '"characters_visible": [string], "action": string or null, "dialogue": string or null, '
        '"narration": string or null, "emotion": string or null, "lighting": string or null, '
        '"duration_seconds": int or null}]}\n\n'
        f"Valid shot_type values: {SHOT_TYPES}\n"
        f"Characters in this scene: {character_names}"
    )
    location_name = scene.location.name if scene.location else "unknown location"
    user = (
        f"Scene {scene.scene_number} ({location_name}, {scene.time_of_day or 'time of day unspecified'}):\n"
        f"Action: {scene.action_description or '(none)'}\n"
        f"Dialogue: {scene.dialogue or '(none)'}\n"
        f"Narration: {scene.narration or '(none)'}\n"
        f"Emotional tone: {scene.emotional_tone or '(none)'}\n\n"
        "Break this scene into a shot list."
    )
    return system, user
