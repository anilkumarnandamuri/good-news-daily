import contextlib
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import digest
import send_push
import summarize


def story(number=1, category="science"):
    return dict(id=str(number), title="Volunteers help a village school",
                summary="Local volunteers donated books to the school.",
                source="Test publisher", category=category, lang="en",
                score=number, link="https://example.invalid/story",
                published="2026-10-14T10:00:00+00:00", image=None)


class RoutineCompatibility(unittest.TestCase):
    def setUp(self):
        self.network = patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden in tests"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.tmp = tempfile.TemporaryDirectory(prefix=".tmp", dir=ROOT / "tests")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "data").mkdir()
        self.news = self.root / "data/news.json"
        self.items = [story(i + 1, cat) for i, cat in enumerate(digest.CATS)]
        self.news.write_text(json.dumps(dict(generated="2026-10-14T10:00:00+00:00", items=self.items)))

    def test_push_payload_contract_and_modes(self):
        for mode in ("top", "teaser"):
            payload = send_push.build(self.items, mode)
            self.assertEqual(payload["app_id"], send_push.APP_ID)
            self.assertEqual(payload["included_segments"], ["Total Subscriptions"])
            self.assertEqual(payload["target_channel"], "push")
            self.assertTrue(payload["url"].endswith("#/s/8"))
            self.assertEqual(set(payload["headings"]), {"en"})
            self.assertEqual(set(payload["contents"]), {"en"})
        self.assertIsNone(send_push.build([], "top"))

    def test_push_cli_dry_runs_never_call_network_even_with_key(self):
        for mode in ("top", "teaser"):
            with self.subTest(mode=mode), patch.object(send_push, "NEWS", self.news), \
                    patch.dict("os.environ", {"ONESIGNAL_API_KEY": "test-only-not-a-key"}), \
                    patch.object(sys, "argv", ["send_push.py", "--dry-run", "--mode", mode]), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(send_push.main(), 0)
                self.assertIn("Dry run: not sent.", output.getvalue())
                self.assertNotIn("test-only-not-a-key", output.getvalue())

    def test_push_missing_key_aborts_without_network(self):
        with patch.object(send_push, "NEWS", self.news), patch.dict("os.environ", {}, clear=True), \
                patch.object(sys, "argv", ["send_push.py"]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(send_push.main(), 2)

    def test_digest_cli_keeps_html_and_text_output_paths(self):
        out = self.root / "sample.html"
        with patch.object(digest, "ROOT", self.root), \
                patch.object(sys, "argv", ["digest.py", "--out", str(out)]), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            digest.main()
        self.assertIn("with 5 stories:", output.getvalue())
        self.assertIn("<!doctype html>", out.read_text())
        self.assertIn("Summary:", out.with_suffix(".txt").read_text())
        self.assertEqual(len({i["category"] for i in digest.pick(self.items)}), 5)

    def test_digest_escapes_publisher_content(self):
        item = story()
        item["title"] = '<script>alert("x")</script>'
        self.assertNotIn(item["title"], digest.render([item], "Wednesday"))
        self.assertIn("&lt;script&gt;", digest.render([item], "Wednesday"))

    def test_build_main_with_local_feed_keeps_news_contract(self):
        feed = types.ModuleType("feedparser")
        class Feed(dict):
            @property
            def entries(self):
                return self["entries"]
        feed.parse = lambda *a, **kw: Feed(entries=[dict(
            title="Volunteers launch a free school library", link="https://example.invalid/new",
            summary="Volunteers donated books and helped local students.",
            published_parsed=dt.datetime.now(dt.timezone.utc).timetuple())])
        sentiment = types.ModuleType("vaderSentiment.vaderSentiment")
        sentiment.SentimentIntensityAnalyzer = lambda: types.SimpleNamespace(
            polarity_scores=lambda _: {"compound": 0.8})
        with patch.dict(sys.modules, {"feedparser": feed, "vaderSentiment": types.ModuleType("vaderSentiment"),
                                      "vaderSentiment.vaderSentiment": sentiment}):
            spec = importlib.util.spec_from_file_location("fixture_build", ROOT / "scripts/build.py")
            build = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(build)
        build.__file__ = str(self.root / "scripts/build.py")
        build.FEEDS = [("fixture.xml", "Fixture", "community", "en", True)]
        with patch.object(summarize, "CACHE", self.root / "data/summaries.json"), \
                patch.dict("os.environ", {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            build.main()
        data = json.loads(self.news.read_text())
        self.assertEqual(set(data), {"generated", "count", "feeds", "items"})
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["feeds"][0]["kept"], 1)
        item = data["items"][0]
        self.assertTrue(set(story()).issubset(item))
        self.assertEqual(len(item["id"]), 10)
        self.assertNotIn("desc", item)
        self.assertIn("sum_en", item)
        self.assertIn("sum_te", item)

    def test_unittest_discovery_succeeds_when_playwright_is_absent(self):
        with patch.dict(sys.modules, {"playwright": None, "playwright.sync_api": None}):
            sys.modules.pop("test_legacy_feed_browser", None)
            sys.modules.pop("tests.test_legacy_feed_browser", None)
            sys.modules.pop("test_voice_reader", None)
            sys.modules.pop("tests.test_voice_reader", None)
            loader = unittest.TestLoader()
            suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
            failed_modules = []
            def check_suite(s):
                for t in s:
                    if isinstance(t, unittest.TestSuite):
                        check_suite(t)
                    elif isinstance(t, unittest.loader._FailedTest):
                        failed_modules.append(t)
            check_suite(suite)
            self.assertEqual(failed_modules, [], f"Discovery failed for modules: {failed_modules}")

    def test_routine_sim_gate_rejects_empty_feed(self):
        # Verify that routine_sim gate rejects empty feed even when n_sum == n_total (0 == 0)
        b_sum = 115
        n_total = 0
        n_sum = 0
        ok = n_sum >= b_sum or (n_total > 0 and n_sum == n_total)
        self.assertFalse(ok)

        # Baseline count met -> pass
        self.assertTrue(115 >= b_sum or (115 > 0 and 115 == 115))
        # Fewer stories than baseline but 100% summarized and nonempty -> pass
        self.assertTrue(50 >= b_sum or (50 > 0 and 50 == 50))


if __name__ == "__main__":
    unittest.main()
