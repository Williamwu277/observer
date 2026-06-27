---
name: changelog-publisher
description: Summarize git commits made since the last published changelog and post a short bullet-point update to the Discord changelog channel. Use when the user asks to publish a changelog, post an update to Discord, or announce recent changes.
disable-model-invocation: true
---

# Changelog Publisher

Posts a concise, bullet-point summary of recent commits to the Discord changelog
channel, then records the commit it published up to so each run only covers new work.

There is NO pre-made script. Write the sending code inline each time, following the
template below.

## Critical: environment variable

Send the message using the webhook URL in the **`CHANGELOG_WEBHOOK_URL`** environment
variable (it lives in the repo `.env`).

- ALWAYS use `CHANGELOG_WEBHOOK_URL`.
- NEVER use `DISCORD_WEBHOOK_URL` — that is a different webhook for internship alerts
  and must not receive changelog posts.
- Do not invent, rename, or guess any other variable name.

## Baseline file

The last published commit is stored (one commit hash, no newline noise) in:

```
.cursor/skills/changelog-publisher/.last_commit
```

This file is git-ignored (per-machine). Read it to find the baseline; overwrite it
with the new HEAD only after a successful Discord post.

If the file is missing or empty, **stop immediately** — warn the user before doing
anything else (no commit collection, no summary, no Discord post). Tell them the
baseline is unset and that publishing without one could re-announce old commits.
Wait for explicit confirmation before continuing; only then may you use a fallback
range (e.g. the last 20 commits) that the user approves.

## Workflow

```
- [ ] Step 1: Read the baseline and collect new commits
- [ ] Step 2: Write the changelog bullets
- [ ] Step 3: Send to Discord using CHANGELOG_WEBHOOK_URL
- [ ] Step 4: Update the baseline file to HEAD
```

**Step 1: Read the baseline and collect new commits**

Check the baseline file **first**, before running `git log` or any later step:

```bash
BASELINE_FILE=.cursor/skills/changelog-publisher/.last_commit
if [ ! -s "$BASELINE_FILE" ]; then echo "MISSING_BASELINE"; fi
```

If the file is missing or empty (`MISSING_BASELINE`):

1. Warn the user immediately — do not collect commits, write bullets, or send to Discord.
2. Explain that without a baseline, the publish range is unknown and old commits could be re-posted.
3. Stop and wait for explicit confirmation. Suggest initializing with
   `git rev-parse HEAD > .cursor/skills/changelog-publisher/.last_commit` if this
   machine has never published, or approving a specific fallback (e.g. last 20 commits).
4. Only after the user confirms, proceed with their chosen range and continue to Step 2.

If the baseline exists, collect new commits:

```bash
BASELINE=$(cat "$BASELINE_FILE")
git log --pretty=format:'%h %s' "$BASELINE"..HEAD
```

Use `git log "$BASELINE"..HEAD --pretty=format:'%h%n%s%n%n%b'` if you need full commit
bodies. If there are no commits in the range, tell the user there is nothing to
publish and stop.

**Step 2: Write the changelog bullets**

Summarize the commits into short, concise bullet points:

- One bullet per meaningful user-facing change; group trivial commits together.
- Start each line with `- `.
- No emojis. No headers, no preamble, no closing remarks.
- Plain language, not raw commit subjects.

Example:

```
- Added retry logic to Discord webhook delivery
- Fixed expired jobs not being marked correctly in the spreadsheet
- Sped up scraping by reusing browser contexts
```

**Step 3: Send to Discord using `CHANGELOG_WEBHOOK_URL`**

Write the code inline (do not save a reusable script). Template:

```python
import os
from dotenv import load_dotenv
import requests

load_dotenv()

webhook_url = os.getenv("CHANGELOG_WEBHOOK_URL")  # never DISCORD_WEBHOOK_URL
if not webhook_url:
    raise SystemExit("CHANGELOG_WEBHOOK_URL is not set in the environment or .env")

message = """- Added retry logic to Discord webhook delivery
- Fixed expired jobs not being marked correctly in the spreadsheet"""

resp = requests.post(webhook_url, json={"content": message}, timeout=10)
resp.raise_for_status()
```

Discord `content` is capped at 2000 characters; if the summary is longer, split it on
line boundaries and send multiple posts. Do not add role pings.

**Step 4: Update the baseline file to HEAD**

Only after the post succeeds:

```bash
git rev-parse HEAD > .cursor/skills/changelog-publisher/.last_commit
```

This ensures a failed send never advances the baseline (no lost commits).
