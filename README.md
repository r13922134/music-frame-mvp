# Music Frame MVP — actual starter repository v0.1

> **Status: runnable software prototype, NOT an existing completed project or physically verified device.** Generated to provide inspectable work to a Devin credit reviewer. No real device, Spotify authorization, GPIO output, or acoustic beat tracking has been tested.

## What it does today

- Serves a kiosk-style album-art UI in a browser (works offline with 3 fictitious demo tracks).
- Provides an HTTP JSON state endpoint (`/api/state`) and demo state switching.
- Can query Spotify's `GET /v1/me/player/currently-playing` endpoint **only if** an already-authorized access token is supplied with `user-read-currently-playing` scope. OAuth login/refresh is **not** yet built.
- Uses an explicitly **mock** ambient-light policy. The on-screen glow is not a GPIO LED driver or genuine audio-reactive synchronization.
- Has unit tests and a local HTTP smoke test.

## Run on a PC or Raspberry Pi 4 (no third-party Python dependencies)

```bash
python3 -m unittest discover -s tests -v
python3 src/frame.py --mode demo
# open http://127.0.0.1:8765
# for Pi full-screen: start Chromium in kiosk mode against http://127.0.0.1:8765
```

Spotify test with a real user OAuth access token **created outside this repo**:

```bash
export SPOTIFY_ACCESS_TOKEN='a-short-lived-user-oauth-access-token'
python3 src/frame.py --mode spotify
```

The access token expires and will not be refreshed in v0.1. Never paste the token in a committed file. For production, Devin must implement OAuth PKCE and a secure refresh flow, not use a permanently shared token.

## Repository contents

```text
src/frame.py                   Local service, API, demo and Spotify adapter
src/index.html                Album-art browser/kiosk UI
src/                         No Python external packages required
tests/test_frame.py           Unit and local HTTP smoke tests
docs/architecture.mmd         Editable Mermaid architecture diagram
docs/architecture.md          Interfaces, phase boundaries, feasibility caveats
docs/wiring.md                Proposed Pi 4 + WS2812B circuit sketch
deploy/music-frame.service.example   Example systemd background service
AGENTS.md                     Concrete Devin tasks and acceptance criteria
```

## System constraints

- RPi 4 connects to a small 1:1 or 3:4 HDMI display; exact model not selected.
- Rear RGB halo proposed using external-power WS2812B LED strip with 74AHCT125 level conversion; wiring is a draft and not physically tested.
- Speaker architecture remains a separate decision; no wire should run between frame and external speakers.
- Spotify metadata is **not an audio stream**. Real music-reactive lights require an audio capture/analysis source and must be evaluated separately.
- Spotify integration and distribution are subject to Spotify API scope/access and developer-policy restrictions.

Read `AGENTS.md` for the budget-specific, testable development plan.

## Continuous integration

GitHub Actions runs five unittest / local HTTP smoke checks on Python 3.11 and 3.12 for pushes and pull requests. No Spotify credentials are required for the demo/tests. Real Raspberry Pi / LED validation is outside CI scope.

## Visual diagram

- [`docs/architecture.md`](docs/architecture.md) — GitHub-rendered Mermaid system diagram and integration notes.
- [`docs/architecture.mmd`](docs/architecture.mmd) / [`docs/architecture.dot`](docs/architecture.dot) — editable diagram sources.
