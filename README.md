# atplan

A reimagining of the Unix `.plan` file tradition for the [ATProto](https://atproto.com) ecosystem.

🌐 [atplan.io](https://atplan.io)
📦 Lexicon: `io.atplan.plan`

## What is this?

In the early days of the internet, the `finger` protocol let you query what any user on a networked system was up to. Users maintained a `.plan` file — freeform text describing their current projects, status, or thoughts. It was proto-blogging before blogging existed.

`atplan` reimagines that tradition for ATProto — federated, user-owned, and linkable.

## Lexicon

Records are stored under `io.atplan.plan` with the key `self`, meaning one plan per user, always updated in place.

## Components

- `plan_write.py` — CLI tool to create or update your `.plan` interactively or via flags
- `plan_read.py` — CLI tool to finger any ATProto user by handle
- `app.py` — Flask web app: public reader, man page landing, and mobile-friendly editor

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install atproto python-dotenv flask httpx gunicorn
cp .env.example .env
# edit .env with your credentials
```

## Usage

```bash
# Full interactive update
python3 plan_write.py

# Quick status update
python3 plan_write.py --status "back Friday"

# Finger someone from the CLI
python3 plan_read.py handle.bsky.social

# Run the web app
python3 app.py
# then browse to http://localhost:5000
```

## Credentials

`.env` requires the following variables:

    PDS_HOST=https://your.pds.host        # your PDS URL
    HANDLE=you.your.pds.host              # your ATProto handle
    APP_PASSWORD=your-app-password        # app password for writing records
    EDIT_TOKEN=your-edit-token            # token for the web editor at /edit
    FLASK_SECRET=your-flask-secret        # secret key for session signing

Never commit `.env` to version control. It is listed in `.gitignore`.
If deploying via Docker, reference your env file in `compose.yaml` via `env_file`.

If you are deploying the web reader only (no `/edit` route), you can omit
`APP_PASSWORD`, `EDIT_TOKEN`, and `FLASK_SECRET`.

## Web App Routes

- `/` — man page landing with live plan example
- `/finger/<handle>` — finger any ATProto user by handle
- `/edit` — token-protected mobile-friendly plan editor
