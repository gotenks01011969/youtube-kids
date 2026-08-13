#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SMOKE_MESSAGE = "kaggle automation smoke test ok"
SMOKE_CHECKSUM = hashlib.sha256(SMOKE_MESSAGE.encode("utf-8")).hexdigest()
DEFAULT_POLL_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 60 * 45
MAX_KERNEL_SLUG_LENGTH = 45
TRANSIENT_ERROR_PATTERNS = (
    "Bad Request for url: https://api.kaggle.com/v1/kernels.KernelsApiService/GetKernelSessionStatus",
    "Bad Request for url: https://api.kaggle.com/v1/kernels.KernelsApiService/SaveKernel",
    "ConnectTimeout",
    "Connection to api.kaggle.com timed out",
    "Max retries exceeded",
    "ReadTimeout",
    "Temporary failure",
    "Connection aborted",
    "Remote end closed connection",
)


class KaggleRunError(RuntimeError):
    pass


def normalize_kaggle_auth_env() -> None:
    if not os.environ.get("KAGGLE_API_TOKEN") and os.environ.get("KAGGLE_KEY"):
        os.environ["KAGGLE_API_TOKEN"] = os.environ["KAGGLE_KEY"]


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    normalize_kaggle_auth_env()
    print(f"+ {' '.join(args)}")
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as error:
        raise KaggleRunError(
            f"Command not found: {args[0]}. Install the Kaggle CLI with: "
            f"{sys.executable} -m pip install kaggle"
        ) from error


def require_success(result: subprocess.CompletedProcess[str], action: str) -> str:
    if result.returncode != 0:
        raise KaggleRunError(f"{action} failed with exit code {result.returncode}\n{result.stdout}")
    return result.stdout


def is_transient_cli_error(output: str) -> bool:
    return any(pattern in output for pattern in TRANSIENT_ERROR_PATTERNS)


def run_kaggle_command_with_retries(
    args: list[str],
    action: str,
    attempts: int = 4,
    delay_seconds: int = 20,
) -> str:
    last_output = ""
    for attempt in range(1, attempts + 1):
        result = run_command(args)
        if result.returncode == 0:
            return result.stdout

        last_output = result.stdout
        if attempt < attempts and is_transient_cli_error(last_output):
            print(f"{action} hit a transient Kaggle/API error; retrying in {delay_seconds}s ({attempt}/{attempts})...")
            time.sleep(delay_seconds)
            continue

        return require_success(result, action)

    raise KaggleRunError(f"{action} failed after {attempts} attempts\n{last_output}")


def kaggle_args(*args: str) -> list[str]:
    if shutil.which("kaggle"):
        return ["kaggle", *args]
    return [sys.executable, "-m", "kaggle", *args]


def read_kaggle_username() -> str:
    env_owner = os.environ.get("KAGGLE_OWNER", "").strip()
    if env_owner:
        return env_owner

    env_username = os.environ.get("KAGGLE_USERNAME", "").strip()
    if env_username:
        return env_username

    token_path = Path.home() / ".kaggle" / "kaggle.json"
    if token_path.exists():
        token = json.loads(token_path.read_text(encoding="utf-8"))
        username = str(token.get("username", "")).strip()
        if username:
            return username

    raise KaggleRunError("Could not determine Kaggle username. Set KAGGLE_USERNAME or pass --owner.")


def slugify(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    slug = "-".join(part for part in slug.split("-") if part)
    return slug[:MAX_KERNEL_SLUG_LENGTH].strip("-") or "notebook-run"


def make_kernel_slug(notebook_path: Path, suffix: str | None) -> str:
    base = slugify(notebook_path.stem)
    if suffix:
        return slugify(f"{base}-{suffix}")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return slugify(f"{base}-{timestamp}")


def stage_kernel(
    notebook_path: Path,
    stage_dir: Path,
    owner: str,
    slug: str,
    title: str,
    enable_gpu: bool,
    enable_internet: bool,
    extra_files: list[Path],
    job_json: Path | None = None,
) -> str:
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    staged_notebook = stage_dir / notebook_path.name
    shutil.copy2(notebook_path, staged_notebook)

    for extra_file in extra_files:
        if not extra_file.exists():
            raise KaggleRunError(f"Extra file does not exist: {extra_file}")
        if extra_file.is_dir():
            shutil.copytree(extra_file, stage_dir / extra_file.name)
        else:
            shutil.copy2(extra_file, stage_dir / extra_file.name)

    if job_json is not None:
        if not job_json.exists():
            raise KaggleRunError(f"Job JSON file does not exist: {job_json}")
        shutil.copy2(job_json, stage_dir / "job.json")

    injectable_files = [extra_file for extra_file in extra_files if extra_file.is_file()]
    if job_json is not None:
        injectable_files.append(stage_dir / "job.json")
    if injectable_files:
        inject_files_into_notebook(staged_notebook, injectable_files)
    else:
        normalize_notebook_cell_ids(staged_notebook)

    kernel_id = f"{owner}/{slug}"
    metadata = {
        "id": kernel_id,
        "title": title,
        "code_file": notebook_path.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": enable_gpu,
        "enable_internet": enable_internet,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }
    (stage_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return kernel_id


def normalize_notebook_cell_ids(notebook_path: Path) -> None:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        cell.setdefault("id", f"cell-{index:04d}")
    notebook_path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def inject_files_into_notebook(notebook_path: Path, files: list[Path]) -> None:
    """Embed small sidecar files into the staged notebook so Kaggle can recreate them."""
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    embedded_files = []

    for file_path in files:
        relative_name = file_path.name
        encoded_content = base64.b64encode(file_path.read_bytes()).decode("ascii")
        embedded_files.append((relative_name, encoded_content))

    lines = [
        "from pathlib import Path\n",
        "import base64\n",
        "\n",
        "print(\"Preparing staged input files...\")\n",
    ]
    for relative_name, encoded_content in embedded_files:
        lines.extend(
            [
                f"Path({relative_name!r}).write_bytes(base64.b64decode({encoded_content!r}))\n",
                f"print(\"Prepared {relative_name}\")\n",
            ]
        )

    setup_cell = {
        "id": "cell-0000-staged-inputs",
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }
    notebook["cells"].insert(0, setup_cell)
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        cell.setdefault("id", f"cell-{index:04d}")
    notebook_path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def push_kernel(stage_dir: Path) -> str | None:
    output = run_kaggle_command_with_retries(
        kaggle_args("kernels", "push", "-p", str(stage_dir)),
        "Kaggle kernel push",
        attempts=5,
        delay_seconds=60,
    )
    print(output)
    match = re.search(r"https://www\.kaggle\.com/code/([^/\s]+)/([^/\s]+)", output)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None


def get_status(kernel_id: str) -> str:
    output = run_kaggle_command_with_retries(
        kaggle_args("kernels", "status", kernel_id),
        "Kaggle kernel status",
    )
    print(output.strip())
    return output.lower()


def wait_for_kernel(kernel_id: str, poll_seconds: int, timeout_seconds: int) -> None:
    start_time = time.monotonic()
    while True:
        status_output = get_status(kernel_id)
        if "complete" in status_output:
            return
        if "error" in status_output or "failed" in status_output or "canceled" in status_output:
            raise KaggleRunError(f"Kaggle kernel did not complete successfully:\n{status_output}")
        if time.monotonic() - start_time > timeout_seconds:
            raise KaggleRunError(f"Timed out waiting for {kernel_id}.")
        time.sleep(poll_seconds)


def download_output(kernel_id: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = run_kaggle_command_with_retries(
        kaggle_args("kernels", "output", kernel_id, "-p", str(output_dir)),
        "Kaggle kernel output download",
        attempts=5,
        delay_seconds=30,
    )
    print(output)


def copy_failure_artifacts(output_dir: Path, slug: str) -> None:
    if not output_dir.exists():
        return

    failure_dir = Path("logs") / "kaggle_failures" / slug
    if failure_dir.exists():
        shutil.rmtree(failure_dir)
    failure_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(output_dir, failure_dir)
    print(f"Copied Kaggle failure artifacts to: {failure_dir}")


def print_failure_log_tail(output_dir: Path, lines: int = 120) -> None:
    log_paths = sorted(output_dir.glob("*.log"))
    if not log_paths:
        return

    for log_path in log_paths:
        print(f"--- Last {lines} lines from {log_path} ---", file=sys.stderr)
        content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in content[-lines:]:
            print(line, file=sys.stderr)


def download_failure_output(kernel_id: str, output_dir: Path, slug: str) -> None:
    try:
        download_output(kernel_id, output_dir)
    except Exception as download_error:
        print(f"Could not download failed Kaggle output: {download_error}", file=sys.stderr)
        return

    copy_failure_artifacts(output_dir, slug)
    print_failure_log_tail(output_dir)


def validate_smoke_output(output_dir: Path) -> None:
    result_path = output_dir / "smoke_result.json"
    if not result_path.exists():
        raise KaggleRunError(f"Smoke output missing: {result_path}")

    payload: dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
    if payload.get("ok") is not True:
        raise KaggleRunError(f"Smoke output ok flag is invalid: {payload}")
    if payload.get("message") != SMOKE_MESSAGE:
        raise KaggleRunError(f"Smoke output message mismatch: {payload}")
    if payload.get("checksum") != SMOKE_CHECKSUM:
        raise KaggleRunError(f"Smoke output checksum mismatch: {payload}")

    print("Smoke output validated.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Push, run, poll, download, and optionally validate a Kaggle notebook."
    )
    parser.add_argument(
        "--notebook",
        type=Path,
        default=Path("kaggle_smoke_test.ipynb"),
        help="Notebook file to run on Kaggle.",
    )
    parser.add_argument(
        "--owner",
        default="",
        help="Kaggle username/owner for the kernel id. Defaults to KAGGLE_OWNER, KAGGLE_USERNAME, or ~/.kaggle/kaggle.json.",
    )
    parser.add_argument("--slug", default="", help="Kernel slug. Defaults to notebook name plus timestamp.")
    parser.add_argument(
        "--kernel-id",
        default="",
        help="Existing Kaggle kernel id to resume polling/downloading, for example owner/slug. Skips staging and push.",
    )
    parser.add_argument("--title", default="", help="Kernel title. Defaults to notebook filename.")
    parser.add_argument("--gpu", action="store_true", help="Enable Kaggle GPU for this run.")
    parser.add_argument("--internet", action="store_true", help="Enable internet for this run.")
    parser.add_argument(
        "--extra-file",
        type=Path,
        action="append",
        default=[],
        help="Extra file or directory to stage next to the notebook, for example job.json.",
    )
    parser.add_argument(
        "--job-json",
        type=Path,
        default=None,
        help="Convenience alias for staging a job.json file next to the notebook.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("kaggle_outputs"),
        help="Local directory for downloaded Kaggle outputs.",
    )
    parser.add_argument(
        "--stage-root",
        type=Path,
        default=Path(".kaggle_runs"),
        help="Local staging directory for generated kernel files.",
    )
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--validate-smoke",
        action="store_true",
        help="Validate smoke_result.json after downloading outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebook_path = args.notebook.resolve()
    if not args.kernel_id.strip() and not notebook_path.exists():
        print(f"Notebook does not exist: {notebook_path}", file=sys.stderr)
        return 2

    kernel_id = ""
    slug = ""
    output_dir = Path("")

    try:
        if args.kernel_id.strip():
            kernel_id = args.kernel_id.strip()
            slug = kernel_id.split("/", 1)[1] if "/" in kernel_id else slugify(kernel_id)
            output_dir = args.output_dir / slug
            print(f"Resuming kernel: {kernel_id}")
        else:
            owner = args.owner.strip() or read_kaggle_username()
            slug = slugify(args.slug.strip()) if args.slug.strip() else make_kernel_slug(notebook_path, suffix=None)
            title = args.title.strip() or slug
            stage_dir = args.stage_root / slug
            output_dir = args.output_dir / slug

            kernel_id = stage_kernel(
                notebook_path=notebook_path,
                stage_dir=stage_dir,
                owner=owner,
                slug=slug,
                title=title,
                enable_gpu=args.gpu,
                enable_internet=args.internet,
                extra_files=[path.resolve() for path in args.extra_file],
                job_json=args.job_json.resolve() if args.job_json is not None else None,
            )

            print(f"Kernel: {kernel_id}")
            print(f"Staged files: {stage_dir}")
            pushed_kernel_id = push_kernel(stage_dir)
            if pushed_kernel_id and pushed_kernel_id != kernel_id:
                print(f"Kaggle returned kernel id: {pushed_kernel_id}")
                kernel_id = pushed_kernel_id
        wait_for_kernel(kernel_id, args.poll_seconds, args.timeout_seconds)
        download_output(kernel_id, output_dir)

        if args.validate_smoke:
            validate_smoke_output(output_dir)

        print(f"Done. Outputs downloaded to: {output_dir}")
        return 0
    except Exception as error:
        print(f"Run failed: {error}", file=sys.stderr)
        if kernel_id and output_dir != Path(""):
            download_failure_output(kernel_id, output_dir, slug)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
