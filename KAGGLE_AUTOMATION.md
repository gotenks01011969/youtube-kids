# Kaggle Automation Test Flow

This repo now has a CPU-only smoke notebook and an automation script for running notebooks on Kaggle.

## Prerequisites

Install and authenticate the Kaggle CLI in a local virtual environment. Avoid installing into the system Python because partial global installs can leave the Kaggle package broken.

```bash
python3 -m venv .venv-kaggle
.venv-kaggle/bin/python -m pip install --upgrade pip
.venv-kaggle/bin/python -m pip install --no-cache-dir -r requirements-kaggle-cli.txt
.venv-kaggle/bin/python -m kaggle --version
```

Then either export a Kaggle API token:

```bash
export KAGGLE_API_TOKEN="your-fresh-kaggle-token"
```

or place the token in:

```text
~/.kaggle/access_token
```

The automation script also needs your Kaggle username for the kernel id. Either pass `--owner` on each run or export:

```bash
export KAGGLE_USERNAME="your-kaggle-username"
```

Older Kaggle credentials also work if you place `kaggle.json` at:

```text
~/.kaggle/kaggle.json
```

or export both:

```bash
export KAGGLE_USERNAME="your-kaggle-username"
export KAGGLE_KEY="your-kaggle-api-key"
```

## Smoke Test

Run the minimal CPU-only notebook on Kaggle:

```bash
.venv-kaggle/bin/python kaggle_run_notebook.py \
  --notebook kaggle_smoke_test.ipynb \
  --owner your-kaggle-username \
  --internet \
  --validate-smoke
```

Expected local result:

```text
Smoke output validated.
Done. Outputs downloaded to: kaggle_outputs/<slug>
```

Expected downloaded files:

```text
smoke_result.json
smoke_output.txt
```

## Real Text-to-Video Run

After the smoke test passes, trigger the real notebook with GPU and internet enabled:

```bash
.venv-kaggle/bin/python kaggle_run_notebook.py \
  --notebook kaggle_text_to_video.ipynb \
  --owner your-kaggle-username \
  --gpu \
  --internet \
  --extra-file job.json \
  --timeout-seconds 7200
```

Expected downloaded file:

```text
output.mp4
```

The script stages a temporary Kaggle kernel directory under `.kaggle_runs/`, pushes it with `kaggle kernels push`, polls `kaggle kernels status`, downloads outputs with `kaggle kernels output`, and validates the smoke-test JSON when requested.
