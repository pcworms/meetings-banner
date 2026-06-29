#!/usr/bin/env python3
"""
Live preview server for pcworms meeting template.
Watches template/ and data.json, re-renders on change, serves on localhost:8000

Requirements:
    pip install chevron watchdog
"""

import os
import sys
import shutil
import json
import time
import threading
import http.server
import socketserver
import chevron
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent.resolve()
TMPL_DIR   = BASE_DIR / "template"
DATA_FILE  = BASE_DIR / "data.json"
OUT_DIR    = BASE_DIR / "tmp"
PORT       = 8000

TEMPLATES = {
    "template.mustache": "index.html",
    "preview.mustache":  "preview.html",
}

# ── Renderer ──────────────────────────────────────────────────────────────────

def render_all():
    OUT_DIR.mkdir(exist_ok=True)

    # Load data
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [error] data.json: {e}")
        return

    # Mustache falsy: null, false, [], ""  →  treat null subject as missing
    if data.get("subject") is None:
        data.pop("subject", None)

    # Render each template
    for src_name, out_name in TEMPLATES.items():
        src = TMPL_DIR / src_name
        if not src.exists():
            print(f"  [warn] {src_name} not found, skipping")
            continue
        try:
            with open(src, encoding="utf-8") as f:
                rendered = chevron.render(f, data)
            out_path = OUT_DIR / out_name
            out_path.write_text(rendered, encoding="utf-8")
            print(f"  [ok] rendered {out_name}")
        except Exception as e:
            print(f"  [error] {src_name}: {e}")

    # Copy static files (css, assets, …) — everything except mustache templates
    for item in TMPL_DIR.iterdir():
        if item.suffix == ".mustache":
            continue
        dest = OUT_DIR / item.name
        try:
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        except Exception as e:
            print(f"  [warn] copy {item.name}: {e}")

    print(f"  → http://localhost:{PORT}/  |  http://localhost:{PORT}/preview.html")


# ── File watcher ──────────────────────────────────────────────────────────────

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self._debounce = None
        self._lock = threading.Lock()

    def _schedule(self):
        with self._lock:
            if self._debounce:
                self._debounce.cancel()
            self._debounce = threading.Timer(0.25, self._run)
            self._debounce.start()

    def _run(self):
        print("\n[change detected] re-rendering…")
        render_all()

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule()

    def on_created(self, event):
        if not event.is_directory:
            self._schedule()


# ── HTTP server ───────────────────────────────────────────────────────────────

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT_DIR), **kwargs)

    def log_message(self, fmt, *args):
        # Only log non-200 responses to keep output clean
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    # Check dependencies
    try:
        import chevron   # noqa: F401
        from watchdog.observers import Observer  # noqa: F401
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run:  pip install chevron watchdog")
        sys.exit(1)

    print("=" * 52)
    print("  pcworms live preview server")
    print("=" * 52)
    print(f"  template dir : {TMPL_DIR}")
    print(f"  data file    : {DATA_FILE}")
    print(f"  output dir   : {OUT_DIR}")
    print(f"  address      : http://localhost:{PORT}/")
    print("=" * 52)

    # Initial render
    print("\n[startup] rendering…")
    render_all()

    # Watch template dir + data.json
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, str(TMPL_DIR), recursive=True)
    observer.schedule(handler, str(BASE_DIR),  recursive=False)  # catches data.json
    observer.start()
    print("\n[watching] Ctrl+C to stop\n")

    # Start HTTP server in a daemon thread
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[stop] shutting down…")
            observer.stop()
            httpd.shutdown()

    observer.join()


if __name__ == "__main__":
    main()
