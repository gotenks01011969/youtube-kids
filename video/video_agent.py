import os
import shutil
import shlex
import subprocess
import wave
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import imageio_ffmpeg
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from utils.logger import logger


OUTPUT_VIDEO = "youtube_kids_video.mp4"
RUNS_DIR = Path("generated/runs")
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 24
SCENE_AUDIO_PADDING_SECONDS = 0.35
CHANNEL_LOGO_BACKGROUND = Path(os.getenv("CHANNEL_LOGO_BACKGROUND", "channel/logo.png"))
CONTENT_SAFE_WIDTH = int(VIDEO_WIDTH * 0.82)
CONTENT_SAFE_HEIGHT = int(VIDEO_HEIGHT * 0.72)
PIPER_EXECUTABLE = os.getenv("PIPER_EXECUTABLE", "piper")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "voices/en_US-amy-medium.onnx")
PIPER_LENGTH_SCALE = os.getenv("PIPER_LENGTH_SCALE", "1.35")
CAPTIONS_ENABLED = os.getenv("CAPTIONS_ENABLED", "1") != "0"
CAPTION_FONT_SIZE = int(os.getenv("CAPTION_FONT_SIZE", "92"))
CAPTION_FONT_VARIATION = os.getenv("CAPTION_FONT_VARIATION", "Bold")
CAPTION_FONT_WEIGHT = int(os.getenv("CAPTION_FONT_WEIGHT", "700"))
CAPTION_FONT_WIDTH = int(os.getenv("CAPTION_FONT_WIDTH", "110"))
CAPTION_TEXT_COLOR = os.getenv("CAPTION_TEXT_COLOR", "#FFE64D")
CAPTION_STROKE_COLOR = os.getenv("CAPTION_STROKE_COLOR", "#5B2EFF")
CAPTION_BOX_COLOR = os.getenv("CAPTION_BOX_COLOR", "#FFFFFF")
CAPTION_FONT_PATHS = [
    os.getenv("CAPTION_FONT_PATH", ""),
    "assets/fonts/fredoka/Fredoka.ttf",
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "/System/Library/Fonts/Supplemental/Chalkboard.ttc",
    "/System/Library/Fonts/Noteworthy.ttc",
]


def _validate_scenes(script: dict) -> list[dict]:
    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("Script must contain at least one scene")

    return scenes


def _is_fixed_background_scene(scene: dict) -> bool:
    scene_type = scene.get("scene_type", "").strip().lower()
    visual = scene.get("visual", "").strip().lower()
    return scene_type in {"opening", "closing"} or visual == "channel logo background"


def _topic_for_intro(script: dict) -> str:
    title = script.get("title", "").strip()
    return title or "today's lesson"


def _normalize_script_scenes(script: dict, scenes: list[dict]) -> list[dict]:
    normalized = [dict(scene) for scene in scenes]
    topic = _topic_for_intro(script)

    if not normalized or normalized[0].get("scene_type", "").strip().lower() != "opening":
        normalized.insert(
            0,
            {
                "scene_type": "opening",
                "visual": "Channel logo background",
                "narration": f"Hi friends. Today we learn about {topic}.",
            },
        )

    if normalized[-1].get("scene_type", "").strip().lower() != "closing":
        normalized.append(
            {
                "scene_type": "closing",
                "visual": "Channel logo background",
                "narration": "Great job friends. See you next time.",
            }
        )

    return normalized


def _build_image_prompt(script: dict, scene: dict, scene_number: int) -> str:
    visual = scene.get("visual", "").strip()
    narration = scene.get("narration", "").strip()
    return "\n".join(
        [
            "Single toddler cartoon illustration.",
            f"Draw exactly this: {visual}",
            "One main object only, large and centered, full object visible.",
            "Leave clear empty margin on all sides so nothing touches the image border.",
            "Do not crop the object, do not cut off any part of the object.",
            "Cute simple sticker style, rounded shape, big shiny eyes, rosy cheeks, happy smile.",
            "Bright colorful playful background, simple soft dots, stars, bubbles, clouds, or rainbow colors.",
            "Background must be colorful but simple, with no extra main objects.",
            "Use clean bold outlines and high contrast colors.",
            "No text, no letters, no numbers, no labels, no captions, no logo, no watermark.",
            "No people, no hands, no room, no table, no road, no complex scene.",
            "No multiple panels, no before and after, no action sequence.",
            "If the object is a square, make it a true square with four equal straight sides, not round.",
            "If the object is a circle, make it clearly round.",
            "If the object is a triangle, make it clearly triangular.",
            "Do not change the object into a different object.",
            f"Narration context only, do not render words: {narration}",
        ]
    )


def _image_slug(script: dict, run_id: str, scene_number: int) -> str:
    title = script.get("title", "youtube-kids-video").lower()
    safe_title = "".join(
        character if character.isalnum() else "-"
        for character in title
    )
    safe_title = "-".join(part for part in safe_title.split("-") if part)
    safe_title = safe_title[:48] or "youtube-kids-video"
    return f"{safe_title}-{run_id}-scene-{scene_number:02d}"


def _generate_image_with_kaggle(
    prompt: str,
    slug: str,
    output_path: Path,
    kaggle_output_root: Path,
    kaggle_stage_root: Path,
) -> bool:
    """
    Generates an image through kaggle_image_generation.generate_image and copies
    the resulting Kaggle output into the scene image path used by the video step.
    """
    try:
        from kaggle_image_generation import generate_image
    except ImportError:
        return False

    generated_path = Path(
        generate_image(
            prompt=prompt,
            slug=slug,
            output_root=kaggle_output_root,
            stage_root=kaggle_stage_root,
        )
    )
    if not generated_path.exists():
        raise RuntimeError(f"Kaggle image generation did not create {generated_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if generated_path.resolve() != output_path.resolve():
        shutil.copyfile(generated_path, output_path)

    return True


def _generate_image_with_command(prompt: str, output_path: Path) -> bool:
    """
    Optional command integration.

    Set TEXT_TO_IMAGE_COMMAND to a command that accepts {prompt} and {output}.
    Example:
      TEXT_TO_IMAGE_COMMAND='python local_t2i.py --prompt {prompt} --output {output}'
    """
    command_template = os.getenv("TEXT_TO_IMAGE_COMMAND")
    if not command_template:
        return False

    command = command_template.format(
        prompt=shlex.quote(prompt),
        output=shlex.quote(str(output_path)),
    )
    subprocess.run(shlex.split(command), check=True)
    return True


def _generate_scene_image(
    prompt: str,
    slug: str,
    output_path: Path,
    kaggle_output_root: Path,
    kaggle_stage_root: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating scene image -> {output_path}")

    generated = (
        _generate_image_with_kaggle(
            prompt,
            slug,
            output_path,
            kaggle_output_root,
            kaggle_stage_root,
        )
        or _generate_image_with_command(prompt, output_path)
    )

    if not generated:
        raise RuntimeError(
            "No text-to-image backend configured. Add kaggle_image_generation.generate_image(prompt, slug) "
            "or set TEXT_TO_IMAGE_COMMAND."
        )

    if not output_path.exists():
        raise RuntimeError(f"Text-to-image backend did not create {output_path}")

    return output_path


def _generate_scene_audio(narration: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not narration:
        raise ValueError("Scene narration cannot be empty")

    model_path = Path(PIPER_MODEL_PATH)
    if not model_path.exists():
        raise RuntimeError(
            f"Piper voice model not found: {model_path}. "
            "Set PIPER_MODEL_PATH to a local .onnx voice model."
        )

    logger.info(f"Generating scene narration with Piper -> {output_path}")

    command = [
        PIPER_EXECUTABLE,
        "--model",
        str(model_path),
        "--output_file",
        str(output_path),
        "--length_scale",
        PIPER_LENGTH_SCALE,
    ]
    subprocess.run(
        command,
        input=narration,
        text=True,
        check=True,
        capture_output=True,
    )

    if not output_path.exists():
        raise RuntimeError(f"Piper did not create {output_path}")

    return output_path


def _wav_duration(audio_path: Path) -> float:
    with wave.open(str(audio_path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


@lru_cache(maxsize=8)
def _load_caption_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in CAPTION_FONT_PATHS:
        if not font_path:
            continue
        try:
            font = ImageFont.truetype(font_path, size=size)
            try:
                font.set_variation_by_name(CAPTION_FONT_VARIATION)
            except OSError:
                try:
                    font.set_variation_by_axes([CAPTION_FONT_WEIGHT, CAPTION_FONT_WIDTH])
                except OSError:
                    pass
            return font
        except OSError:
            continue

    logger.warning("Caption font not found; falling back to default Pillow font")
    return ImageFont.load_default()


def _caption_segments(narration: str, audio_duration: float) -> list[tuple[float, float, str]]:
    caption = narration.strip()
    if not caption:
        return []
    return [(0.0, audio_duration, caption)]


def _caption_at_time(
    segments: list[tuple[float, float, str]],
    elapsed_seconds: float,
) -> str | None:
    for start, end, text in segments:
        if start <= elapsed_seconds < end:
            return text
    return None


def _text_bbox(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int, int, int]:
    return draw.textbbox((0, 0), text, font=font, stroke_width=5)


def _wrap_caption_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        left, _, right, _ = _text_bbox(draw, candidate, font)
        if right - left <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _draw_caption(image: Image.Image, caption: str, scene_number: int) -> Image.Image:
    if not CAPTIONS_ENABLED or not caption:
        return image

    frame = image.convert("RGBA")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    max_text_width = int(VIDEO_WIDTH * 0.78)
    font_size = CAPTION_FONT_SIZE
    font = _load_caption_font(font_size)
    lines = _wrap_caption_text(draw, caption, font, max_text_width)

    while lines and len(lines) > 2 and font_size > 56:
        font_size -= 6
        font = _load_caption_font(font_size)
        lines = _wrap_caption_text(draw, caption, font, max_text_width)

    line_gap = int(font_size * 0.16)
    line_boxes = [_text_bbox(draw, line, font) for line in lines]
    text_width = max((right - left for left, _, right, _ in line_boxes), default=0)
    text_height = sum(bottom - top for _, top, _, bottom in line_boxes)
    text_height += max(0, len(lines) - 1) * line_gap

    padding_x = 54
    padding_y = 28
    box_width = text_width + padding_x * 2
    box_height = text_height + padding_y * 2
    box_left = (VIDEO_WIDTH - box_width) // 2
    box_top = VIDEO_HEIGHT - box_height - 58
    box_right = box_left + box_width
    box_bottom = box_top + box_height

    shadow_offset = 10
    draw.rounded_rectangle(
        (
            box_left + shadow_offset,
            box_top + shadow_offset,
            box_right + shadow_offset,
            box_bottom + shadow_offset,
        ),
        radius=38,
        fill=(70, 40, 130, 130),
    )
    draw.rounded_rectangle(
        (box_left, box_top, box_right, box_bottom),
        radius=38,
        fill=(*ImageColor.getrgb(CAPTION_BOX_COLOR), 210),
    )

    color_cycle = ["#FFE64D", "#7CFBFF", "#FF8BE8", "#9CFF67"]
    text_color = CAPTION_TEXT_COLOR or color_cycle[(scene_number - 1) % len(color_cycle)]
    stroke_color = CAPTION_STROKE_COLOR
    y = box_top + padding_y
    for line, bbox in zip(lines, line_boxes):
        left, top, right, bottom = bbox
        line_width = right - left
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text(
            (x - left, y - top),
            line,
            font=font,
            fill=text_color,
            stroke_width=5,
            stroke_fill=stroke_color,
        )
        y += (bottom - top) + line_gap

    return Image.alpha_composite(frame, overlay).convert("RGB")


def _combine_audio(audio_paths: list[Path], output_path: Path) -> Path:
    logger.info(f"Combining narration audio -> {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(audio_paths[0]), "rb") as first:
        params = first.getparams()
        audio_format = (
            first.getnchannels(),
            first.getsampwidth(),
            first.getframerate(),
            first.getcomptype(),
            first.getcompname(),
        )
        silence_frame_count = round(SCENE_AUDIO_PADDING_SECONDS * first.getframerate())
        silence = b"\x00" * silence_frame_count * first.getnchannels() * first.getsampwidth()

    with wave.open(str(output_path), "wb") as combined:
        combined.setparams(params)

        for audio_path in audio_paths:
            with wave.open(str(audio_path), "rb") as scene_audio:
                scene_audio_format = (
                    scene_audio.getnchannels(),
                    scene_audio.getsampwidth(),
                    scene_audio.getframerate(),
                    scene_audio.getcomptype(),
                    scene_audio.getcompname(),
                )
                if scene_audio_format != audio_format:
                    raise RuntimeError(f"Audio format mismatch in {audio_path}")

                combined.writeframes(scene_audio.readframes(scene_audio.getnframes()))
                combined.writeframes(silence)

    return output_path


def _cover_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(
        image,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def _contained_image(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    contained = image.copy()
    contained.thumbnail(max_size, Image.Resampling.LANCZOS)
    return contained


def _fit_image_for_video(image_path: Path, fixed_background: bool = False) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    background = _cover_image(image, (VIDEO_WIDTH, VIDEO_HEIGHT))
    background = background.filter(ImageFilter.GaussianBlur(radius=24))
    background = Image.blend(
        background,
        Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), "#FFF3A6"),
        0.22,
    )

    if fixed_background:
        foreground_size = (int(VIDEO_WIDTH * 0.70), int(VIDEO_HEIGHT * 0.62))
        foreground_y = int(VIDEO_HEIGHT * 0.10)
    else:
        foreground_size = (CONTENT_SAFE_WIDTH, CONTENT_SAFE_HEIGHT)
        foreground_y = 34

    foreground = _contained_image(image, foreground_size)
    x = (VIDEO_WIDTH - foreground.width) // 2
    y = foreground_y + max(0, (foreground_size[1] - foreground.height) // 2)

    shadow = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_margin = 18
    shadow_draw.rounded_rectangle(
        (
            x - shadow_margin,
            y - shadow_margin,
            x + foreground.width + shadow_margin,
            y + foreground.height + shadow_margin,
        ),
        radius=42,
        fill=(90, 55, 150, 70),
    )

    frame = Image.alpha_composite(background.convert("RGBA"), shadow).convert("RGB")
    frame.paste(foreground, (x, y))
    return frame


def _assemble_silent_video(
    image_paths: list[Path],
    scene_durations: list[float],
    scene_audio_durations: list[float],
    narrations: list[str],
    fixed_background_flags: list[bool],
    output_path: Path,
) -> Path:
    logger.info(f"Assembling silent video -> {output_path}")

    with imageio.get_writer(
        str(output_path),
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=None,
    ) as writer:
        for scene_number, (
            image_path,
            scene_duration,
            audio_duration,
            narration,
            fixed_background,
        ) in enumerate(
            zip(
                image_paths,
                scene_durations,
                scene_audio_durations,
                narrations,
                fixed_background_flags,
            ),
            start=1,
        ):
            frames_per_scene = max(1, round(scene_duration * FPS))
            frame = _fit_image_for_video(image_path, fixed_background=fixed_background)
            frame_data = np.asarray(frame)
            caption_frame_cache = {}
            segments = _caption_segments(narration, audio_duration)

            for frame_index in range(frames_per_scene):
                elapsed_seconds = frame_index / FPS
                caption = _caption_at_time(segments, elapsed_seconds)
                if not caption:
                    writer.append_data(frame_data)
                    continue

                if caption not in caption_frame_cache:
                    captioned_frame = _draw_caption(frame, caption, scene_number)
                    caption_frame_cache[caption] = np.asarray(captioned_frame)

                writer.append_data(caption_frame_cache[caption])

    return output_path


def _mux_audio(video_path: Path, audio_path: Path, output_path: Path) -> str:
    logger.info(f"Muxing narration into video -> {output_path}")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(command, check=True)

    return str(output_path)


def generate_video(script: dict) -> str:
    """
    Converts structured script scenes into generated images, generates narration,
    and assembles everything into a local MP4 video.
    """
    logger.info("Generating video locally from scene images and Piper narration")

    scenes = _normalize_script_scenes(script, _validate_scenes(script))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    run_dir = RUNS_DIR / run_id
    scene_image_dir = run_dir / "scenes"
    scene_audio_dir = run_dir / "audio"
    kaggle_output_root = run_dir / "kaggle_outputs"
    kaggle_stage_root = run_dir / "kaggle_runs"
    combined_audio_path = run_dir / "narration.wav"
    silent_video_path = run_dir / "silent_video.mp4"
    output_video_path = run_dir / OUTPUT_VIDEO
    image_paths = []
    audio_paths = []
    scene_durations = []
    scene_audio_durations = []
    narrations = []
    fixed_background_flags = []

    for index, scene in enumerate(scenes, start=1):
        image_path = scene_image_dir / f"scene_{index:02d}.png"
        audio_path = scene_audio_dir / f"scene_{index:02d}.wav"
        fixed_background = _is_fixed_background_scene(scene)

        if fixed_background:
            if not CHANNEL_LOGO_BACKGROUND.exists():
                raise RuntimeError(
                    f"Channel logo background not found: {CHANNEL_LOGO_BACKGROUND}"
                )
            image_paths.append(CHANNEL_LOGO_BACKGROUND)
        else:
            prompt = _build_image_prompt(script, scene, index)
            slug = _image_slug(script, run_id, index)
            image_paths.append(
                _generate_scene_image(
                    prompt,
                    slug,
                    image_path,
                    kaggle_output_root,
                    kaggle_stage_root,
                )
            )

        narration = scene.get("narration", "")
        audio_paths.append(_generate_scene_audio(narration, audio_path))
        audio_duration = _wav_duration(audio_path)
        scene_audio_durations.append(audio_duration)
        scene_durations.append(audio_duration + SCENE_AUDIO_PADDING_SECONDS)
        narrations.append(narration)
        fixed_background_flags.append(fixed_background)

    combined_audio = _combine_audio(audio_paths, combined_audio_path)
    silent_video = _assemble_silent_video(
        image_paths,
        scene_durations,
        scene_audio_durations,
        narrations,
        fixed_background_flags,
        silent_video_path,
    )

    return _mux_audio(silent_video, combined_audio, output_video_path)
