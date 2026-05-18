import os
import sys
import httpx
import argparse
import tempfile
import subprocess
from datetime import timezone, datetime
from dotenv import load_dotenv
from atproto import Client, models

load_dotenv()

PDS_HOST = os.getenv("PDS_HOST")
HANDLE = os.getenv("HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")
EDITOR = os.getenv("EDITOR", "nano")

def fetch_existing(did):
    url = f"{PDS_HOST}/xrpc/com.atproto.repo.getRecord"
    params = {
        "repo": did,
        "collection": "io.mikehacks.plan",
        "rkey": "self"
    }
    response = httpx.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("value", {})
    return {}

def open_editor(existing_text=""):
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=".plan",
        prefix="atplan_",
        delete=False
    ) as tf:
        tf.write(existing_text)
        tmpfile = tf.name

    subprocess.call([EDITOR, tmpfile])

    with open(tmpfile, 'r') as f:
        content = f.read()

    os.unlink(tmpfile)
    return content.strip()

def prompt_field(label, existing="", required=False):
    display = f" [{existing}]" if existing else ""
    value = input(f"  {label}{display}: ").strip()
    if not value and existing:
        return existing
    if not value and required:
        print(f"  {label} is required.")
        return prompt_field(label, existing, required)
    return value or existing

def publish(client, record):
    response = client.com.atproto.repo.put_record(
        models.ComAtprotoRepoPutRecord.Data(
            repo=client.me.did,
            collection="io.mikehacks.plan",
            rkey="self",
            record=record
        )
    )
    return response

def main():
    parser = argparse.ArgumentParser(description="Update your .plan on ATProto")
    parser.add_argument("--status", help="Short status or availability line")
    parser.add_argument("--project", help="Current project one-liner")
    parser.add_argument("--displayname", help="Display name")
    parser.add_argument("--url", help="Personal or project URL")
    parser.add_argument("--edit", action="store_true", help="Open body in editor only")
    args = parser.parse_args()

    client = Client(base_url=PDS_HOST)
    client.login(HANDLE, APP_PASSWORD)

    # Always fetch existing record first
    existing = fetch_existing(client.me.did)
    if existing:
        print(f"Found existing .plan (last updated {existing.get('updatedAt', 'unknown')})")
    else:
        print("No existing .plan found, creating new one.")

    quick_update = any([args.status, args.project, args.displayname, args.url])

    if quick_update and not args.edit:
        # Patch mode — only update what was passed
        record = {
            "$type": "io.mikehacks.plan",
            "displayName": existing.get("displayName", ""),
            "status": existing.get("status", ""),
            "project": existing.get("project", ""),
            "url": existing.get("url", ""),
            "text": existing.get("text", ""),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        if args.status:
            record["status"] = args.status
        if args.project:
            record["project"] = args.project
        if args.displayname:
            record["displayName"] = args.displayname
        if args.url:
            record["url"] = args.url

        response = publish(client, record)
        print(f"Plan updated.")
        print(f"URI: {response.uri}")

    elif args.edit:
        # Editor only — just open the body
        print("Opening editor for plan body...")
        new_text = open_editor(existing.get("text", ""))
        if not new_text:
            print("No content entered, aborting.")
            sys.exit(0)
        record = {
            "$type": "io.mikehacks.plan",
            "displayName": existing.get("displayName", ""),
            "status": existing.get("status", ""),
            "project": existing.get("project", ""),
            "url": existing.get("url", ""),
            "text": new_text,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        response = publish(client, record)
        print(f"Plan updated.")
        print(f"URI: {response.uri}")

    else:
        # Full interactive mode
        print("\nUpdating your .plan — press enter to keep existing values.\n")

        display_name = prompt_field("Display name", existing.get("displayName", ""))
        status = prompt_field("Status", existing.get("status", ""))
        project = prompt_field("Project", existing.get("project", ""))
        url = prompt_field("URL", existing.get("url", ""))

        print(f"\n  Opening {EDITOR} for plan body...")
        input("  Press enter to continue...")
        text = open_editor(existing.get("text", ""))

        if not text:
            print("No plan body entered, aborting.")
            sys.exit(0)

        record = {
            "$type": "io.mikehacks.plan",
            "displayName": display_name,
            "status": status,
            "project": project,
            "url": url,
            "text": text,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }

        response = publish(client, record)
        print(f"\nPlan updated.")
        print(f"URI: {response.uri}")

if __name__ == "__main__":
    main()
