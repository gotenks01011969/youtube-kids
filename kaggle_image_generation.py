from pathlib import Path
import json
import os
import subprocess
import sys

def generate_image(
    prompt: str,
    slug: str,
    output_root: str | Path = "kaggle_outputs",
    stage_root: str | Path = ".kaggle_runs",
) -> Path:
    hf_token = os.getenv("HF_TOKEN")
    job = {
        "prompt": prompt,
        "negative_prompt": (
            "text, words, captions, title, label, letters, numbers, watermark, logo, signature, "
            "multiple panels, split screen, collage, many objects, crowded scene, busy background, "
            "realistic photo, scary, dark, blurry, low quality, distorted face, extra limbs, text artifacts"
        ),
        "width": 768,
        "height": 768,
        "num_inference_steps": 4,
        "guidance_scale": 0.0,
        "max_sequence_length": 256,
        "gguf_quant": "Q3_K_S",
    }

    if hf_token:
        job["hf_token"] = hf_token

    output_root = Path(output_root)
    stage_root = Path(stage_root)
    job_path = output_root.parent / "jobs" / f"{slug}.json"
    job_path.parent.mkdir(parents=True, exist_ok=True)
    job_path.write_text(json.dumps(job, indent=2), encoding="utf-8")

    kaggle_python = os.getenv("KAGGLE_PYTHON", sys.executable)
    kaggle_owner = os.getenv("KAGGLE_OWNER") or os.getenv("KAGGLE_USERNAME")
    if not kaggle_owner:
        raise RuntimeError("Set KAGGLE_OWNER or KAGGLE_USERNAME before generating Kaggle images.")

    subprocess.run(
        [
            kaggle_python,
            "kaggle_run_notebook.py",
            "--notebook",
            "kaggle_high_quality_image.ipynb",
            "--owner",
            kaggle_owner,
            "--slug",
            slug,
            "--gpu",
            "--internet",
            "--job-json",
            str(job_path),
            "--output-dir",
            str(output_root),
            "--stage-root",
            str(stage_root),
            "--timeout-seconds",
            "7200",
        ],
        check=True,
    )

    return output_root / slug / "output.png"
