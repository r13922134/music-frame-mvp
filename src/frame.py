"""Music Frame MVP v0.1: working local browser demo and Spotify metadata adapter.

No hardware GPIO writes or audio beat extraction are implemented in this version.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
SPOTIFY_CURRENTLY_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing"
DEMO_TRACKS = [
    {"title": "First Light", "artist": "Demo Artist", "album": "Paper Skies", "color": "#d9a18f"},
    {"title": "Evening Transit", "artist": "Demo Artist", "album": "Night Shapes", "color": "#8a9bb7"},
    {"title": "Blue Hour", "artist": "Demo Artist", "album": "Still Water", "color": "#89afa5"},
]


@dataclass(frozen=True)
class TrackState:
    title: str = "Nothing playing"
    artist: str = "Music Frame"
    album: str = "Waiting for music"
    cover_url: str | None = None
    color: str = "#a0a7b0"
    is_playing: bool = False
    source: str = "demo"
    status: str = "idle"
    updated_at: str = ""


def normalize_spotify(data: dict[str, Any] | None) -> TrackState:
    """Translate an official Spotify 'currently-playing' response to display state."""
    if not data or not data.get("item"):
        return TrackState(source="spotify", status="idle")
    item = data["item"]
    album = item.get("album") or {}
    images = album.get("images") or item.get("images") or []
    artists = item.get("artists") or []
    artist = ", ".join(a.get("name", "") for a in artists if a.get("name"))
    return TrackState(
        title=item.get("name") or "Untitled",
        artist=artist or "Unknown artist",
        album=album.get("name") or "Unknown album",
        cover_url=images[0].get("url") if images else None,
        is_playing=bool(data.get("is_playing", False)),
        source="spotify",
        status="playing" if data.get("is_playing") else "paused",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


def spotify_fetch(access_token: str, timeout: float = 8.0) -> TrackState:
    if not access_token:
        raise ValueError("Missing SPOTIFY_ACCESS_TOKEN. Obtain an OAuth user token with user-read-currently-playing scope.")
    req = Request(SPOTIFY_CURRENTLY_PLAYING, headers={"Authorization": "Bearer " + access_token, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            if response.status == 204:
                return normalize_spotify(None)
            return normalize_spotify(json.load(response))
    except HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError("Spotify token expired or invalid; reauthorize the account.") from exc
        if exc.code == 429:
            retry_after = exc.headers.get("Retry-After", "unknown")
            raise RuntimeError(f"Spotify rate limited; Retry-After={retry_after}s") from exc
        raise RuntimeError(f"Spotify HTTP error {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Spotify network error: {exc.reason}") from exc


def ambient_light(state: TrackState) -> dict[str, Any]:
    """LED control INTENT, not a hardware driver. Not an audio-reactive effect."""
    return {"mode": "ambient" if state.is_playing else "off", "color": state.color, "brightness": 0.30 if state.is_playing else 0.0, "driver": "mock"}


class Model:
    def __init__(self, mode: str, token: str, demo_switch_seconds: int = 12):
        self.mode = mode
        self.token = token
        self.start_time = time.monotonic()
        self.demo_switch_seconds = demo_switch_seconds
        self._lock = threading.Lock()
        self._state = TrackState(source=mode)
        self._error: str | None = None

    def poll(self) -> None:
        if self.mode == "demo":
            index = int((time.monotonic() - self.start_time) / self.demo_switch_seconds) % len(DEMO_TRACKS)
            sample = DEMO_TRACKS[index]
            next_state = TrackState(**sample, is_playing=True, source="demo", status="playing", updated_at=datetime.now(timezone.utc).isoformat())
            error = None
        else:
            try:
                next_state = spotify_fetch(self.token)
                error = None
            except (ValueError, RuntimeError) as exc:
                next_state = TrackState(source="spotify", status="error")
                error = str(exc)
        with self._lock:
            self._state, self._error = next_state, error

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            state, error = self._state, self._error
        return {"track": asdict(state), "lighting": ambient_light(state), "error": error, "version": "0.1.0"}


def make_handler(model: Model):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/state":
                payload = json.dumps(model.snapshot(), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
            elif path in ("/", "/index.html"):
                payload = (ROOT / "src" / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
            else:
                self.send_error(404, "Not found")
                return
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            logging.info("http: " + fmt, *args)

    return Handler


def worker(model: Model, stop: threading.Event, interval: float) -> None:
    while not stop.is_set():
        model.poll()
        stop.wait(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Frame local display service")
    parser.add_argument("--mode", choices=["demo", "spotify"], default="demo")
    parser.add_argument("--host", default="127.0.0.1", help="Local-only by default")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--poll-seconds", type=float, default=10, help="Spotify polling interval; don't hammer the API")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    model = Model(mode=args.mode, token=os.environ.get("SPOTIFY_ACCESS_TOKEN", ""))
    stop = threading.Event()
    thread = threading.Thread(target=worker, args=(model, stop, args.poll_seconds if args.mode == "spotify" else 1.0), daemon=True)
    thread.start()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(model))
    print(f"Music Frame {args.mode} mode: http://{args.host}:{args.port} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
