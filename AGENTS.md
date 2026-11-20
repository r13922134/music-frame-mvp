# Devin: first instruction / first pull request

**Issue to close:** [#1 — Spotify PKCE onboarding for headless Raspberry Pi](https://github.com/r13922134/music-frame-mvp/issues/1).

```text
Clone https://github.com/r13922134/music-frame-mvp. First run:
python3 -m unittest discover -s tests -v
python3 src/frame.py --mode demo
Open a PR titled "feat(auth): Spotify PKCE login and refresh" with "Closes #1".
Implement /auth/start and /auth/callback with PKCE S256, state validation,
persistent refresh-token support, tests, README setup, and an SSH-tunnel
loopback callback for headless Raspberry Pi; do not implement LED GPIO yet.
Keep Spotify callback bound to 127.0.0.1:8765. No public IP/domain.
```

**Headless OAuth callback:** Spotify registered redirect URI `http://127.0.0.1:8765/auth/callback` (not `localhost`). On the user's laptop:

```bash
ssh -N -L 127.0.0.1:8765:127.0.0.1:8765 pi@musicframe.local
# In laptop browser: http://127.0.0.1:8765/auth/start
```

The laptop browser's Spotify redirect reaches its own loopback and is forwarded over SSH to the Pi. Full tests, security details and acceptance criteria are in [Issue #1](https://github.com/r13922134/music-frame-mvp/issues/1). Without a laptop tunnel or Pi-local browser, a phone login cannot directly callback to the Pi using this URI.

---

# Devin implementation brief / acceptance criteria

Context: Raspberry Pi 4-based music artwork display and optional rear WS2812B ambient RGB halo. External speakers are **not** wired to the display. Prototype currently contains a local runnable demo and metadata adapter; it has **not** been deployed to physical hardware.

**First task:** Run `python3 -m unittest discover -s tests -v` from project root and `python3 src/frame.py --mode demo`; inspect `http://127.0.0.1:8765` and `/api/state`.

**Milestone A — claim $50 software execution budget:**
1. Implement Spotify OAuth Authorization Code + PKCE with a simple local onboarding UI and secure token storage/refresh (never commit secrets). See official Spotify docs and comply with policy.
2. Connect authenticated playback metadata to this frame: track/artist/album/cover/play/pause/idle with robust 401, 429, timeout handling and configurable polling.
3. Adapt layout for 1:1 and 3:4 Pi HDMI screens; create practical Raspberry Pi kiosk setup notes.
4. Supply automated tests for expired tokens, empty playback, bad images, network disconnection, and state transitions.
5. Deliver runnable code, short local screen recording/screenshot, test output, and explicit list of unimplemented hardware functions.

**Milestone B — only if resources remain and hardware is available:**
1. Implement a configurable, safe LED driver for GPIO18 WS2812B behind 74AHCT125, with default brightness limit and all-off on shutdown.
2. Document real hardware test; include electrical safety caveats.
3. Make a systemd service and kiosk startup configuration with logs, restart behavior, and a documented teardown procedure.
4. Propose/measure a real audio signal acquisition path for beat-reactive lighting; do NOT implement fake 'reactive' lights driven only by track metadata and label them as synchronized.

**Acceptance / ethics:** No fake repos, no invented device tests, no exposed tokens. The current frontend glow and `lighting.driver=mock` are software previews only. Feature status must remain accurate.
