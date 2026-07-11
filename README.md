# atplan

A reimagining of the Unix `.plan` file tradition for the [ATProto](https://atproto.com) ecosystem.

🌐 [atplan.io](https://atplan.io) 📦 Lexicon: `io.atplan.plan`

## What is this?

In the early days of the internet, the `finger` protocol let you query what any user on a networked system was up to. Users maintained a `.plan` file — freeform text describing their current projects, status, or thoughts. It was proto-blogging before blogging existed.

`atplan` reimagines that tradition for ATProto — federated, user-owned, and linkable.

## Publishing your .plan

The easiest way to publish a plan is at [atplan.io/edit](https://atplan.io/edit). Sign in with your ATProto handle, fill in your plan, and save. No account, no setup, no self-hosting required. Your plan is stored as a record on your own PDS under the `io.atplan.plan` Lexicon.

To finger anyone's plan, visit [atplan.io/finger/handle](https://atplan.io/finger/handle) or use the form on the landing page.

## Lexicon

Records are stored under `io.atplan.plan` with the key `self`, meaning one plan per user, always updated in place.

**Just want to publish your plan?** Go to [atplan.io/edit](https://atplan.io/edit) — 
no setup required. Sign in with your ATProto handle and start writing.

## Components

- `plan_write.py` — CLI tool to create or update your `.plan` interactively or via flags
- `plan_read.py` — CLI tool to finger any ATProto user by handle
- `app.py` — Flask web app: public reader, man page landing, and ATProto OAuth editor

## Self-hosting

If you want to run your own instance of the web app:

```bash
python3 -m venv venv
source venv/bin/activate
pip install atproto python-dotenv flask httpx gunicorn
cp .env.example .env
# edit .env with your credentials
python3 app.py
# then browse to http://localhost:5000
```

`.env` requires:
PDS_HOST=https://your.pds.host        # your PDS URL
HANDLE=you.your.pds.host              # your ATProto handle for the landing page example

Never commit `.env` to version control. It is listed in `.gitignore`.
If deploying via Docker, reference your env file in `compose.yaml` via `env_file`.

## CLI Usage

```bash
# Full interactive update
python3 plan_write.py

# Quick status update
python3 plan_write.py --status "back Friday"

# Finger someone from the CLI
python3 plan_read.py handle.bsky.social
```

The CLI writer requires additional credentials in `.env`:
APP_PASSWORD=your-app-password        # app password for writing records

## Web App Routes

- `/` — man page landing with live plan example
- `/finger/<handle>` — finger any ATProto user by handle
- `/edit` — ATProto OAuth editor, open to any ATProto user
- `/client-metadata.json` — OAuth client metadata
