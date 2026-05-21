import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from atproto import Client, models
from flask import Flask, render_template, request, redirect, url_for, session

load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")
HANDLE = os.getenv("HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")
EDIT_TOKEN = os.getenv("EDIT_TOKEN")
FLASK_SECRET = os.getenv("FLASK_SECRET")

app = Flask(__name__)
app.secret_key = FLASK_SECRET

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

def get_pds_for_did(did):
    try:
        if did.startswith("did:plc:"):
            response = httpx.get(f"https://plc.directory/{did}")
            if response.status_code == 200:
                doc = response.json()
                for service in doc.get("service", []):
                    if service.get("id") == "#atproto_pds":
                        return service.get("serviceEndpoint")
    except Exception:
        pass
    return PDS_HOST

def fetch_plan(did):
    pds = get_pds_for_did(did)
    response = httpx.get(
        f"{pds}/xrpc/com.atproto.repo.getRecord",
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
        if not plan:
            return None, handle, f"No .plan found for {handle}"
        return plan, handle, None
    except Exception as e:
        return None, handle, str(e)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        handle = request.form.get("handle", "").strip().lstrip("@")
        if handle:
            return redirect(url_for("finger", handle=handle))

    owner_plan, owner_handle, owner_error = get_plan_for_handle(HANDLE)
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

@app.route("/edit", methods=["GET", "POST"])
def edit():
    error = None

    if not session.get("authenticated"):
        if request.method == "POST" and request.form.get("token"):
            if request.form.get("token") == EDIT_TOKEN:
                session["authenticated"] = True
                session.permanent = True
                app.permanent_session_lifetime = __import__("datetime").timedelta(days=30)
            else:
                error = "Invalid token."
        if not session.get("authenticated"):
            return render_template("edit.html", authenticated=False, error=error)

    # Authenticated — fetch current plan
    try:
        did = resolve_handle(HANDLE)
        plan = fetch_plan(did)
    except Exception as e:
        plan = {}

    return render_template("edit.html", authenticated=True, plan=plan, error=error)

@app.route("/save", methods=["POST"])
def save():
    if not session.get("authenticated"):
        return redirect(url_for("edit"))

    status = request.form.get("status", "").strip()
    project = request.form.get("project", "").strip()
    text = request.form.get("text", "").strip()

    try:
        did = resolve_handle(HANDLE)
        existing = fetch_plan(did)
        if not existing:
            existing = {}

        record = {
            "$type": "io.atplan.plan",
            "displayName": existing.get("displayName", ""),
            "status": status,
            "project": project,
            "url": existing.get("url", ""),
            "text": text,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }

        client = Client(base_url=PDS_HOST)
        client.login(HANDLE, APP_PASSWORD)
        client.com.atproto.repo.put_record(
            models.ComAtprotoRepoPutRecord.Data(
                repo=client.me.did,
                collection="io.atplan.plan",
                rkey="self",
                record=record
            )
        )
    except Exception as e:
        try:
            did = resolve_handle(HANDLE)
            plan = fetch_plan(did)
        except:
            plan = {}
        return render_template("edit.html", authenticated=True, plan=plan,
                             error=f"Save failed: {e}")

    return redirect(url_for("finger", handle=HANDLE))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
