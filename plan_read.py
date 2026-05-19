import os
import sys
import httpx
from dotenv import load_dotenv
from atproto import Client, models
from datetime import datetime, timezone

def format_timestamp(ts):
    try:
        ts = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%a %b %d %H:%M:%S UTC %Y")
    except Exception:
        return ts
load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")
HANDLE = os.getenv("HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")

client = Client(base_url=PDS_HOST)
client.login(HANDLE, APP_PASSWORD)

target = sys.argv[1] if len(sys.argv) > 1 else HANDLE

print(f"fingering {target}...\n")

# Resolve handle to DID
if target.startswith("did:"):
    did = target
else:
    resolved = client.com.atproto.identity.resolve_handle(
        models.ComAtprotoIdentityResolveHandle.Params(handle=target)
    )
    did = resolved.did

# Fetch record directly via HTTP
url = f"{PDS_HOST}/xrpc/com.atproto.repo.getRecord"
params = {
    "repo": did,
    "collection": "io.atplan.plan",
    "rkey": "self"
}

response = httpx.get(url, params=params)

if response.status_code != 200:
    print(f"No .plan found for {target}")
    print(f"Status: {response.status_code}")
    print(f"Detail: {response.text}")
else:
    p = response.json().get("value", {})

    print(f"{'─' * 50}")
    if p.get('displayName'):
        print(f"  Name:    {p['displayName']}")
    print(f"  Handle:  {target}")
    if p.get('status'):
        print(f"  Status:  {p['status']}")
    if p.get('project'):
        print(f"  Project: {p['project']}")
    if p.get('url'):
        print(f"  URL:     {p['url']}")
    print(f"  Updated: {format_timestamp(p['updatedAt'])}")
    print(f"{'─' * 50}")
    print()
    print(p.get('text', ''))
    print()
