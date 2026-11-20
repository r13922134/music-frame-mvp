import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from frame import Model, TrackState, ambient_light, make_handler, normalize_spotify


class SpotifyNormalizationTests(unittest.TestCase):
    def test_track_parsing(self):
        payload = {"is_playing": True, "item": {"name": "A track", "artists": [{"name": "A"},{"name": "B"}], "album": {"name": "An album", "images": [{"url": "https://example.org/cover.jpg"}]}}}
        state = normalize_spotify(payload)
        self.assertEqual(state.title, "A track")
        self.assertEqual(state.artist, "A, B")
        self.assertEqual(state.cover_url, "https://example.org/cover.jpg")
        self.assertTrue(state.is_playing)

    def test_missing_track_is_idle(self):
        self.assertEqual(normalize_spotify(None).status, "idle")
        self.assertEqual(normalize_spotify({"item": None}).is_playing, False)

    def test_no_artists_or_images(self):
        state = normalize_spotify({"item": {"name": "Untitled"}, "is_playing": False})
        self.assertEqual(state.artist, "Unknown artist")
        self.assertEqual(state.status, "paused")
        self.assertIsNone(state.cover_url)

    def test_lighting_is_ambient_not_beats(self):
        self.assertEqual(ambient_light(TrackState(is_playing=True))["mode"], "ambient")
        self.assertEqual(ambient_light(TrackState(is_playing=False))["brightness"], 0)
        self.assertEqual(ambient_light(TrackState(is_playing=True))["driver"], "mock")


class HttpSmokeTest(unittest.TestCase):
    def test_demo_routes(self):
        model = Model("demo", "")
        model.poll()
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(model))
        runner = threading.Thread(target=server.serve_forever, daemon=True)
        runner.start()
        try:
            address = f"http://127.0.0.1:{server.server_port}"
            with urlopen(address + "/api/state") as r:
                data = json.load(r)
                self.assertTrue(data["track"]["is_playing"])
                self.assertEqual(data["version"], "0.1.0")
            with urlopen(address + "/") as r:
                self.assertIn(b"Music Frame MVP", r.read())
        finally:
            server.shutdown()
            server.server_close()
            runner.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
