import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def cleanup(path, missing_ok=True):
    if os.path.isdir(path):
        shutil.rmtree(path)
        print(f"{path} deleted successfully.")
    elif os.path.exists(path):
        os.remove(path)
        print(f"{path} deleted successfully.")
    elif not missing_ok:
        print(f"{path} does not exist.")


def _kaggle_owner():
    return os.getenv("KAGGLE_OWNER") or os.getenv("KAGGLE_USERNAME")


def _delete_kaggle_kernels(stage_roots):
    owner = _kaggle_owner()
    if not owner:
        return

    kaggle_python = os.getenv("KAGGLE_PYTHON", sys.executable)
    slugs = []

    for stage_root in stage_roots:
        stage_root = Path(stage_root)
        if not stage_root.exists():
            continue

        for stage_dir in sorted(path for path in stage_root.iterdir() if path.is_dir()):
            metadata_path = stage_dir / "kernel-metadata.json"
            kernel_id = f"{owner}/{stage_dir.name}"

            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    kernel_id = metadata.get("id", kernel_id)
                except Exception:
                    pass

            slugs.append(kernel_id)

    for kernel_id in dict.fromkeys(slugs):
        print(f"Deleting Kaggle kernel {kernel_id}")
        try:
            subprocess.run(
                [
                    kaggle_python,
                    "-m",
                    "kaggle",
                    "kernels",
                    "delete",
                    kernel_id,
                    "--yes",
                ],
                check=True,
            )
        except Exception as error:
            print(f"Failed to delete Kaggle kernel {kernel_id}: {error}")


def cleanup_run_artifacts(video_path=None):
    """
    Remove files and directories produced by one pipeline run.
    This is intentionally scoped to generated/transient artifacts.
    """
    stage_roots = [".kaggle_runs"]
    generated_runs = Path("generated/runs")
    if generated_runs.exists():
        stage_roots.extend(generated_runs.glob("*/kaggle_runs"))

    paths = [
        "generated/runs",
        "generated",
        ".kaggle_runs",
        "kaggle_outputs",
        "job.json",
        "__pycache__",
        "agents/__pycache__",
        "orchestrator/__pycache__",
        "uploader/__pycache__",
        "utils/__pycache__",
        "video/__pycache__",
    ]

    if video_path:
        video_parent = Path(video_path).parent
        if video_parent != Path("."):
            stage_roots.insert(0, video_parent / "kaggle_runs")
            paths.insert(0, str(video_parent))
        else:
            paths.append(video_path)

    _delete_kaggle_kernels(stage_roots)

    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        cleanup(path)

    for mp4_path in Path(".").glob("*.mp4"):
        cleanup(str(mp4_path))
