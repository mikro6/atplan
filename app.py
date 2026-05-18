import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from atproto import Client, models
from flask import Flask, render_template, request

load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")
HANDLE = os.getenv("HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")

app = Flask(__name__)

def format_timestamp(ts):
    try:
        ts = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%a %b %d %H:%M:%S UTC %Y")
    except Exception:
        return ts

def get_client():
    client = Client(base_url=PDS_HOST)
    client.login(HANDLE, APP_PASSWORD)
    return client

def resolve_handle(client, handle):
    if handle.startswith("did:"):
        return handle
    resolved = client.com.atproto.identity.resolve_handle(
        models.ComAtprotoIdentityResolveHandle.Params(handle=handle)
    )
    return resolved.did

def fetch_plan(did):
    url = f"{PDS_HOST}/xrpc/com.atproto.repo.getRecord"
    params = {
        "repo": did,
        "collection": "io.atplan.plan",
        "rkey": "self"
    }
    response = httpx.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("value", {})
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    plan = None
    handle = None
    error = None

    if request.method == "POST":
        handle = request.form.get("handle", "").strip()
        if handle:
            try:
                client = get_client()
                did = resolve_handle(client, handle)
                plan = fetch_plan(did)
                if not plan:
                    error = f"No .plan found for {handle}"
                else:
                    if plan.get("updatedAt"):
                        plan["updatedAt"] = format_timestamp(plan["updatedAt"])
            except Exception as e:
                error = f"Could not finger {handle}: {e}"

    return render_template("index.html", plan=plan, handle=handle, error=error)

@app.route("/finger/<path:handle>")
def finger(handle):
    plan = None
    error = None

    try:
        client = get_client()
        did = resolve_handle(client, handle)
        plan = fetch_plan(did)
        if not plan:
            error = f"No .plan found for {handle}"
        else:
            if plan.get("updatedAt"):
                plan["updatedAt"] = format_timestamp(plan["updatedAt"])
    except Exception as e:
        error = f"Could not finger {handle}: {e}"

    return render_template("index.html", plan=plan, handle=handle, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
