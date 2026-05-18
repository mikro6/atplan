# atplan

A revival of the Unix `.plan` file tradition for the [ATProto](https://atproto.com) ecosystem.

🌐 [atplan.io](https://atplan.io)
📦 Lexicon: `io.atplan.plan`

## What is this?

In the early days of the internet, the `finger` protocol let you query what any user on a networked system was up to. Users maintained a `.plan` file — freeform text describing their current projects, status, or thoughts. It was proto-blogging before blogging existed.

`atplan` brings that tradition to ATProto — federated, user-owned, and linkable.

## Lexicon

Records are stored under `io.atplan.plan` with the key `self`, meaning one plan per user, always updated in place.

## Components

- `plan_write.py` — CLI tool to create or update your `.plan`
- `plan_read.py` — CLI tool to finger any ATProto user by handle
- `app.py` — Flask web reader with direct URL routing

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install atproto python-dotenv flask httpx
cp .env.example .env
# edit .env with your PDS host, handle, and app password
```

## Usage

```bash
# Full interactive update
python3 plan_write.py

# Quick status update
python3 plan_write.py --status "back Friday"

# Finger someone from the CLI
python3 plan_read.py handle.bsky.social

# Web reader
python3 app.py
# then browse to http://localhost:5000
```
## Credentials

The web reader (`app.py`) is fully unauthenticated — it only needs `PDS_HOST` 
in your environment.

The CLI writer (`plan_write.py`) requires credentials to publish records to 
your PDS. Your `.env` should contain:

    PDS_HOST=https://your.pds.host
    HANDLE=you.your.pds.host
    APP_PASSWORD=your-app-password

Never commit `.env` to version control. It is listed in `.gitignore`.
If you are deploying the web reader, only `PDS_HOST` is required in your 
server environment.

## Web Reader

Direct URL routing:

https://yourserver/finger/handle.bsky.social

