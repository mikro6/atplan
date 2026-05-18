import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")
OWNER_HANDLE = os.getenv("OWNER_HANDLE")

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

def get_plan_for_handle(handle):
    try:
        did = resolve_handle(handle)
        plan = fetch_plan(did)
        if plan and plan.get("updatedAt"):
            plan["updatedAt"] = format_timestamp(plan["updatedAt"])
        return plan, handle, None
    except Exception as e:
        return None, handle, str(e)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        handle = request.form.get("handle", "").strip().lstrip("@")
        plan, handle, error = get_plan_for_handle(handle) if handle else (None, None, None)
        return render_template("finger.html", plan=plan, handle=handle, error=error)

    # GET — load landing page with owner's plan as example
    owner_plan, owner_handle, owner_error = get_plan_for_handle(OWNER_HANDLE)
    return render_template("landing.html",
        owner_plan=owner_plan,
        owner_handle=owner_handle,
        owner_error=owner_error
    )

@app.route("/finger/<path:handle>")
def finger(handle):
    handle = handle.lstrip("@")
    plan, handle, error = get_plan_for_handle(handle)
    return render_template("finger.html", plan=plan, handle=handle, error=error)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
