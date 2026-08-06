# GitHub Actions Pipeline Setup

The workflow at `.github/workflows/pipeline.yml` runs the full video pipeline twice per day:

- `03:30 UTC`
- `15:30 UTC`

It can also be started manually from the GitHub Actions UI with `workflow_dispatch`.

## Required GitHub Secrets

Add these in GitHub under `Settings > Secrets and variables > Actions > Repository secrets`.

```text
GROQCLOUD_API_KEY
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
KAGGLE_USERNAME
KAGGLE_KEY
HF_TOKEN
```

Instead of `GROQCLOUD_API_KEY`, you may set `GROQCLOUD_KEYS` to a comma-separated list of keys.

## What The Workflow Does

1. Checks out the repo.
2. Installs Python dependencies.
3. Downloads the Piper Amy voice if it is not already in the checkout.
4. Runs `python run_pipeline.py`.
5. Uploads the generated video publicly to YouTube.
6. Deletes generated local files and Kaggle notebooks through the pipeline cleanup.
7. Commits updated topic/format memory files back to the repo after a successful run.

## Notes

- Videos are uploaded as `public` by default.
- The YouTube refresh token must have upload permission.
- The Hugging Face token must have access to the gated FLUX model used by the Kaggle notebook.
- The Kaggle account must have internet and GPU notebook access available.

## Add Secrets With GitHub CLI

Run these from the repo after logging in with `gh auth login`.

```bash
gh secret set GROQCLOUD_API_KEY --body "YOUR_GROQ_API_KEY"
gh secret set YOUTUBE_CLIENT_ID --body "YOUR_YOUTUBE_CLIENT_ID"
gh secret set YOUTUBE_CLIENT_SECRET --body "YOUR_YOUTUBE_CLIENT_SECRET"
gh secret set YOUTUBE_REFRESH_TOKEN --body "YOUR_YOUTUBE_REFRESH_TOKEN"
gh secret set KAGGLE_USERNAME --body "YOUR_KAGGLE_USERNAME"
gh secret set KAGGLE_KEY --body "YOUR_KAGGLE_KEY"
gh secret set HF_TOKEN --body "YOUR_HUGGING_FACE_TOKEN"
```

`KAGGLE_KEY` should be the Kaggle API token value. The workflow maps it to `KAGGLE_API_TOKEN` for the Kaggle CLI.

Then trigger a test run:

```bash
gh workflow run "YouTube Kids Pipeline"
```

Watch it:

```bash
gh run watch
```
