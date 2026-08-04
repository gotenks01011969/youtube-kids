import os
import shutil
import shlex
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageOps

from utils.logger import logger


OUTPUT_VIDEO = "youtube_kids_video.mp4"
RUNS_DIR = Path("generated/runs")
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 24
SCENE_AUDIO_PADDING_SECONDS = 0.35
PIPER_EXECUTABLE = os.getenv("PIPER_EXECUTABLE", "piper")
PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "voices/en_US-lessac-medium.onnx")
PIPER_LENGTH_SCALE = os.getenv("PIPER_LENGTH_SCALE", "1.15")


def _validate_scenes(script: dict) -> list[dict]:
    scenes = script.get("scenes", [])
    if not scenes:
        raise ValueError("Script must contain at least one scene")

    return scenes


def _build_image_prompt(script: dict, scene: dict, scene_number: int) -> str:
    return "\n".join(
        [
            "Create a YouTube Kids friendly image for a toddler learning video.",
            f"Video title: {script.get('title', 'Untitled')}",
            f"Scene number: {scene_number}",
            "Target age: 1-3 years.",
            "Style: bright, colorful, friendly cartoon, high contrast, rounded shapes, big smiling eyes.",
            "Composition: one large centered main object, simple clean background, easy to understand without text.",
            "Render as one static illustration, not an action sequence.",
            "Avoid text, captions, labels, letters, numbers, signs, logos, watermarks, tiny details, crowded scenes, or complex backgrounds.",
            "Avoid motion blur, multiple panels, before-and-after layouts, or many objects.",
            "Safety: calm, cheerful, no fear, no danger, no conflict, no weapons, no realistic hazards.",
            f"Visual content: {scene.get('visual', '')}",
            f"Spoken narration for context only, do not render text: {scene.get('narration', '')}",
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


def _fit_image_for_video(image_path: Path) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    image = ImageOps.fit(
        image,
        (VIDEO_WIDTH, VIDEO_HEIGHT),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    return image


def _assemble_silent_video(
    image_paths: list[Path],
    scene_durations: list[float],
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
        for image_path, scene_duration in zip(image_paths, scene_durations):
            frames_per_scene = max(1, round(scene_duration * FPS))
            frame = _fit_image_for_video(image_path)
            frame_data = np.asarray(frame)

            for _ in range(frames_per_scene):
                writer.append_data(frame_data)

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

    scenes = _validate_scenes(script)
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

    for index, scene in enumerate(scenes, start=1):
        image_path = scene_image_dir / f"scene_{index:02d}.png"
        audio_path = scene_audio_dir / f"scene_{index:02d}.wav"
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
        audio_paths.append(_generate_scene_audio(scene.get("narration", ""), audio_path))
        scene_durations.append(_wav_duration(audio_path) + SCENE_AUDIO_PADDING_SECONDS)

    combined_audio = _combine_audio(audio_paths, combined_audio_path)
    silent_video = _assemble_silent_video(image_paths, scene_durations, silent_video_path)

    return _mux_audio(silent_video, combined_audio, output_video_path)
