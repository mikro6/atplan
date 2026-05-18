import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")

app = Flask(__name__)

def format_timestamp(ts):
    try:
        ts = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime("%a %b %d %H:%M:%S UTC %Y")
    except Exception:
        return ts

def resolve_handle(handle):
    if handle.startswith("did:"):
        return handle
    response = httpx.get(
        f"{PDS_HOST}/xrpc/com.atproto.identity.resolveHandle",
        params={"handle": handle}
    )
    if response.status_code != 200:
        raise Exception(f"Could not resolve handle: {handle}")
    return response.json().get("did")

def fetch_plan(did):
    response = httpx.get(
        f"{PDS_HOST}/xrpc/com.atproto.repo.getRecord",
        params={
            "repo": did,
            "collection": "io.atplan.plan",
            "rkey": "self"
        }
    )
    if response.status_code == 200:
        return response.json().get("value", {})
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    plan = None
    handle = None
    error = None

    if request.method == "POST":
        handle = request.form.get("handle", "").strip().lstrip("@")
        if handle:
            try:
                did = resolve_handle(handle)
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
    handle = handle.lstrip("@")

    try:
        did = resolve_handle(handle)
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
