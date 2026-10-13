#!/usr/bin/env python3
"""Reel inbox for video-watch.

Three lanes, merged and de-duplicated:
  1. Reminders list "Reels for Claude" (MAIN lane since 2026-10-03). The iPhone "Send to Claude"
     share-sheet shortcut adds each link as a reminder. Reminders sync in seconds; a text file in
     iCloud Drive written by a share-sheet shortcut can sit on the phone as "Waiting…" for hours.
     When a link is marked done/skipped, its reminder is ticked off (completed, never deleted).
  2. Safari's Reading List ("Add to Reading List" in the iPhone share menu).
  3. iCloud Drive > Shortcuts > reels.txt (the older lane; read-only, the phone owns the file).

  inbox.py list                    # links waiting in the inbox
  inbox.py list --saved            # links waiting in the saved-reels backlog
  inbox.py done <url> [--note "<source note title>"]
  inbox.py skip <url> --reason "<why>"
  inbox.py status
  inbox.py setup                   # create the Reminders list if it is missing
  inbox.py import-saved <file>     # Instagram "Export your information" .zip or .json
"""
import argparse
import datetime as dt
import json
import os
import plistlib
import re
import subprocess
import sys
import zipfile

MD = os.path.expanduser("~/Library/Mobile Documents")
INBOX_CANDIDATES = [
    os.path.join(MD, "iCloud~is~workflow~my~workflows/Documents/reels.txt"),
    os.path.join(MD, "iCloud~is~workflow~my~workflows/Documents/Claude/reels.txt"),
    os.path.join(MD, "com~apple~CloudDocs/Shortcuts/Claude/reels.txt"),
    os.path.join(MD, "com~apple~CloudDocs/Claude/reels.txt"),
    os.path.join(MD, "com~apple~CloudDocs/Claude Inbox/reels.txt"),
]
STATE = os.environ.get("VIDEO_WATCH_STATE", os.path.expanduser("~/.local/share/video-watch/state.json"))
URL_RE = re.compile(r"https?://[^\s<>\"']+")
# Second inbox: Safari's Reading List ("Add to Reading List" in the iPhone share menu syncs here
# through iCloud). Only video links are taken; everything else in the Reading List is ignored.
READING_LIST = os.environ.get("VIDEO_WATCH_READING_LIST", os.path.expanduser("~/Library/Safari/Bookmarks.plist"))
VIDEO_URL = re.compile(r"(instagram\.com/(?:[^/?#]+/)?(?:reels?|p|tv)/|youtube\.com/(?:watch|shorts|live)|youtu\.be/|"
                       r"tiktok\.com/|(?:x|twitter)\.com/[^/]+/status/|vimeo\.com/\d|loom\.com/share/)", re.I)
# Main inbox: an Apple Reminders list the share-sheet shortcut adds to (synced through iCloud).
REMINDERS_LIST = os.environ.get("VIDEO_WATCH_REMINDERS_LIST", "Reels for Claude")
FIELD, ROW = "\x1f", "\x1e"  # separators that never appear in a link or a reminder title


def osa(script, timeout=60):
    """Run AppleScript. Returns (ok, stdout, stderr). Never raises."""
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    except Exception as exc:  # timeout = a macOS permission prompt is probably waiting on screen
        return False, "", str(exc)
    return r.returncode == 0, r.stdout.rstrip("\n"), r.stderr.strip()


def as_str(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def reminders_items():
    """[(reminder id, text)] for the list's open reminders, oldest first. [] if the list or access is missing."""
    script = f'''
tell application "Reminders"
  if not (exists list {as_str(REMINDERS_LIST)}) then return ""
  set out to ""
  repeat with r in (reminders of list {as_str(REMINDERS_LIST)} whose completed is false)
    set b to body of r
    if b is missing value then set b to ""
    set out to out & (id of r) & (ASCII character 31) & (name of r) & " " & b & (ASCII character 30)
  end repeat
  return out
end tell'''
    ok, out, _ = osa(script)
    if not ok or not out:
        return []
    items = []
    for row in out.split(ROW):
        if FIELD in row:
            rid, text = row.split(FIELD, 1)
            items.append((rid.strip(), text))
    return items


def reminders_status():
    ok, out, err = osa(f'tell application "Reminders" to exists list {as_str(REMINDERS_LIST)}')
    if not ok:
        return f"NOT READABLE ({err[:120]}) - allow it: System Settings > Privacy & Security > Automation > Reminders"
    return "ready" if out == "true" else "list missing - run: inbox.py setup"


def complete_reminders(key):
    """Tick off (never delete) every open reminder whose link matches this key."""
    done = 0
    for rid, text in reminders_items():
        if any(key_and_clean(u)[0] == key for u in URL_RE.findall(text)):
            ok, _, _ = osa(f'tell application "Reminders" to set completed of (first reminder of list '
                           f'{as_str(REMINDERS_LIST)} whose id is {as_str(rid)}) to true')
            done += ok
    return done


def inbox_files():
    """Every inbox file that exists (the shortcut may write to a slightly different folder)."""
    override = os.environ.get("VIDEO_WATCH_INBOX")
    if override:
        return [override] if os.path.exists(override) else []
    return [p for p in INBOX_CANDIDATES if os.path.exists(p)]


def inbox_path():
    files = inbox_files()
    return ", ".join(files) if files else INBOX_CANDIDATES[0] + " (not created yet)"


def key_and_clean(url):
    url = url.rstrip(").,;!?'\"")
    m = re.search(r"instagram\.com/(?:[^/?#]+/)?(reels?|p|tv)/([A-Za-z0-9_-]+)", url)
    if m:
        kind = "reel" if m.group(1).startswith("reel") else m.group(1)
        return f"ig:{m.group(2)}", f"https://www.instagram.com/{kind}/{m.group(2)}/"
    m = re.search(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if m:
        return f"yt:{m.group(1)}", f"https://www.youtube.com/watch?v={m.group(1)}"
    m = re.search(r"tiktok\.com/.*/video/(\d+)", url)
    if m:
        return f"tt:{m.group(1)}", url.split("?")[0]
    bare = url.split("#")[0].split("?")[0]
    return "url:" + re.sub(r"^https?://(www\.)?", "", bare).rstrip("/"), bare


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"handled": {}, "backlog": []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"), indent=1)
    os.replace(tmp, STATE)


def reading_list_urls():
    """Video links in Safari's Reading List (oldest first). Read-only; never edits Safari data."""
    if not os.path.exists(READING_LIST):
        return []
    try:
        with open(READING_LIST, "rb") as fh:
            root = plistlib.load(fh)
    except Exception:
        return []

    def find(node):
        if node.get("Title") == "com.apple.ReadingList":
            return node.get("Children") or []
        for child in node.get("Children") or []:
            hit = find(child)
            if hit is not None:
                return hit
        return None

    items = find(root) or []
    items.sort(key=lambda it: (it.get("ReadingList") or {}).get("DateAdded") or dt.datetime.min)
    return [it.get("URLString", "") for it in items if VIDEO_URL.search(it.get("URLString", ""))]


def inbox_links():
    seen, out = set(), []
    reminder_urls = [u for _, text in reminders_items() for u in URL_RE.findall(text)]
    for url in reminder_urls + reading_list_urls():
        k, clean = key_and_clean(url)
        if k not in seen:
            seen.add(k)
            out.append((k, clean))
    for path in inbox_files():
        for line in open(path, encoding="utf-8", errors="ignore"):
            for url in URL_RE.findall(line):  # header/comment lines simply contain no URL
                k, clean = key_and_clean(url)
                if k not in seen:
                    seen.add(k)
                    out.append((k, clean))
    return out


def cmd_list(saved):
    state = load_state()
    if saved:
        pending = [(k, u) for k, u in state["backlog"] if k not in state["handled"]]
        label = "saved-reels backlog"
    else:
        pending = [(k, u) for k, u in inbox_links() if k not in state["handled"]]
        label = f"inbox (Reminders '{REMINDERS_LIST}' + Reading List + {inbox_path()})"
    print(f"{len(pending)} waiting in the {label}")
    for i, (_, u) in enumerate(pending, 1):
        print(f"{i:3d}. {u}")
    return 0


def mark(url, result, detail):
    state = load_state()
    k, clean = key_and_clean(url)
    state["handled"][k] = {"url": clean, "result": result, "detail": detail,
                           "date": dt.date.today().isoformat()}
    save_state(state)
    ticked = complete_reminders(k)
    print(f"{result}: {clean}" + (f"  (ticked off {ticked} reminder(s) in '{REMINDERS_LIST}')" if ticked else ""))
    return 0


def cmd_setup():
    if osa(f'tell application "Reminders" to exists list {as_str(REMINDERS_LIST)}')[1] == "true":
        print(f"Reminders list '{REMINDERS_LIST}' already exists")
        return 0
    ok, _, err = osa(f'tell application "Reminders" to make new list with properties {{name:{as_str(REMINDERS_LIST)}}}')
    print(f"created Reminders list '{REMINDERS_LIST}'" if ok else f"could not create the list: {err}")
    return 0 if ok else 1


def cmd_status():
    state = load_state()
    inbox = inbox_links()
    handled = state["handled"]
    print(f"reminders:    '{REMINDERS_LIST}' {reminders_status()}, {len(reminders_items())} open")
    print(f"inbox file(s): {inbox_path()}")
    print(f"reading list: {len(reading_list_urls())} video link(s) in Safari's Reading List")
    print(f"inbox:        {sum(1 for k, _ in inbox if k not in handled)} waiting, {len(inbox)} total")
    print(f"saved backlog:{sum(1 for k, _ in state['backlog'] if k not in handled):4d} waiting, {len(state['backlog'])} total")
    print(f"handled:      {sum(1 for v in handled.values() if v['result'] == 'done')} done, "
          f"{sum(1 for v in handled.values() if v['result'] == 'skipped')} skipped")
    return 0


def cmd_import_saved(path):
    texts = []
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".json") and "saved" in name.lower():
                    texts.append(zf.read(name).decode("utf-8", errors="ignore"))
    else:
        texts.append(open(path, encoding="utf-8", errors="ignore").read())
    found = []
    for text in texts:
        for url in URL_RE.findall(text.replace("\\/", "/")):
            if "instagram.com" in url:
                found.append(key_and_clean(url))
    state = load_state()
    known = {k for k, _ in state["backlog"]}
    added = 0
    for k, u in found:
        if k not in known and k.startswith("ig:"):
            state["backlog"].append([k, u])
            known.add(k)
            added += 1
    save_state(state)
    print(f"imported {added} new saved post(s); backlog now {len(state['backlog'])}. "
          "Photo-only posts are skipped automatically when processed.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--saved", action="store_true")
    p = sub.add_parser("done"); p.add_argument("url"); p.add_argument("--note", default="")
    p = sub.add_parser("skip"); p.add_argument("url"); p.add_argument("--reason", required=True)
    sub.add_parser("status")
    sub.add_parser("setup")
    p = sub.add_parser("import-saved"); p.add_argument("file")
    a = ap.parse_args()
    if a.cmd == "setup":
        return cmd_setup()
    if a.cmd == "list":
        return cmd_list(a.saved)
    if a.cmd == "done":
        return mark(a.url, "done", a.note)
    if a.cmd == "skip":
        return mark(a.url, "skipped", a.reason)
    if a.cmd == "status":
        return cmd_status()
    return cmd_import_saved(a.file)


if __name__ == "__main__":
    sys.exit(main())
