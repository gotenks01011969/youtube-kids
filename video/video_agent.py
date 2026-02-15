import requests
import time
import os
from utils.logger import logger
from utils.secrets import get_heygen_key

HEYGEN_POLL_INTERVAL = 300  # seconds

def _get_video_status(video_id):
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "accept": "application/json",
        "x-api-key": get_heygen_key(),
    }
    response = requests.get(url, headers=headers)
    return response.json()


def _handle_filename(filename):
    base, ext = os.path.splitext(filename)
    new_filename = filename
    counter = 1

    while os.path.exists(new_filename):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1

    return new_filename


def _download_video_file(url, filename):
    filename = _handle_filename(filename)

    logger.info(f"Downloading video → {filename}")

    response = requests.get(url)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename


def _create_video(prompt: str) -> str:
    url = "https://api.heygen.com/v1/video_agent/generate"

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": get_heygen_key(),
    }

    payload = {"prompt": prompt}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()
    return data.get("data", {}).get("video_id")

def _format_narration(narration_text):
    """
    Slow narration by adding small pauses between words.
    """
    if not narration_text:
        return "No narration."

    words = narration_text.strip().split()
    # return " ... ".join(words)
    return " ".join(words)


def generate_video(script: dict) -> str:
    """
    Converts structured script → HeyGen video.
    Returns path to final video file.
    """

    logger.info("Generating video via HeyGen")

    prompt_parts = []

    # Global visual rendering direction (DO NOT repeat script logic)
    prompt_parts.append(
        f"Create a YouTube Kids friendly animated video using the provided scenes.\n"
        f"Title: {script.get('title', 'Untitled')}\n"
        f"Target age: 1–3 years\n"
        f"Language: English\n\n"
    )


    # Scene-by-scene instructions
    for scene in script.get("scenes", []):
        narration_text = _format_narration(scene.get("narration", []))

        scene_block = [
            f"Visual: {scene.get('visual')}",
            f"Narration: {narration_text}"
        ]
        prompt_parts.append("\n".join(scene_block))

    final_prompt = "\n\n".join(prompt_parts)

    video_id = _create_video(final_prompt)

    if not video_id:
        raise RuntimeError("HeyGen did not return a video_id")

    logger.info(f"HeyGen video_id: {video_id}")

    start_time = time.time()
    timeout = 3600  # 1 hour in seconds

    # Polling loop
    while True:
        # Check if 1 hour has passed
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            print("1 hour timeout exceeded - raising exception")
            raise RuntimeError(f"Video generation took too much time")
        
        status_response = _get_video_status(video_id)
        status = status_response.get("data", {}).get("status")

        logger.info(f"Video status: {status}")

        if status == "completed":
            video_url = status_response["data"].get("video_url")
            if not video_url:
                raise RuntimeError("Video completed but URL missing")

            return _download_video_file(video_url, "youtube_kids_video.mp4")

        if status in ("failed", "error"):
            raise RuntimeError(f"Video generation failed: {status_response}")

        time.sleep(HEYGEN_POLL_INTERVAL)
