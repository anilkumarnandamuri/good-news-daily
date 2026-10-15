import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import summarize

PAIRS = [
    {"en": "Volunteers opened a library in the village.", "te": "వాలంటీర్లు గ్రామంలో ఒక గ్రంథాలయాన్ని ప్రారంభించారు."},
    {"en": "They donated 500 books for local children.", "te": "వారు స్థానిక పిల్లల కోసం 500 పుస్తకాలను ఇచ్చారు."},
    {"en": "The library is open every Saturday.", "te": "గ్రంథాలయం ప్రతి శనివారం తెరిచి ఉంటుంది."},
    {"en": "Children can borrow the books for free.", "te": "పిల్లలు పుస్తకాలను ఉచితంగా తీసుకోవచ్చు."},
    {"en": "Teachers will help children choose books.", "te": "పిల్లలు పుస్తకాలను ఎంచుకోవడానికి ఉపాధ్యాయులు సహాయం చేస్తారు."},
    {"en": "The school has provided a room for reading.", "te": "పాఠశాల చదవడానికి ఒక గదిని ఇచ్చింది."},
]


def item():
    return dict(id="library", title="Volunteers open a village library", lang="en",
                summary="Volunteers donated books to local children.",
                desc=" ".join(p["en"] for p in PAIRS), link="https://example.invalid/library")


class SummaryContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix=".tmp", dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name) / "summaries.json"
        for mock in (patch.object(summarize, "CACHE", self.cache),
                     patch.dict("os.environ", {}, clear=True),
                     patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden"))):
            mock.start()
            self.addCleanup(mock.stop)

    def run_items(self, items):
        with contextlib.redirect_stdout(io.StringIO()):
            return summarize.run(items)

    def test_four_five_and_six_aligned_pairs(self):
        for count in (4, 5, 6):
            with self.subTest(count=count):
                pairs = summarize.validate_pairs(PAIRS[:count])
                self.assertEqual(len(pairs), count)
                self.assertEqual([p["en"] for p in pairs], [p["en"] for p in PAIRS[:count]])
                self.assertEqual([p["te"] for p in pairs], [p["te"] for p in PAIRS[:count]])

    def test_invalid_lengths_rejected(self):
        for pairs in ([], PAIRS[:1], PAIRS[:3], PAIRS + [PAIRS[0]]):
            with self.subTest(count=len(pairs)), self.assertRaises(ValueError):
                summarize.validate_pairs(pairs)

    def test_missing_translation_multiple_sentences_wrong_language_and_duplicates(self):
        for value in ("", "First sentence. second sentence.", "This is English.", None):
            pairs = copy.deepcopy(PAIRS[:4])
            pairs[1]["te"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                summarize.validate_pairs(pairs)
        with self.assertRaises(ValueError):
            summarize.validate_pairs(PAIRS[:3] + [PAIRS[0]])
        with self.assertRaises(ValueError):
            summarize.legacy_pairs(" ".join(p["en"] for p in PAIRS[:4]), " ".join(p["te"] for p in PAIRS[:5]))

    def test_sentence_boundaries_preserve_numbers_abbreviations_and_telugu(self):
        self.assertEqual(len(summarize.sentences("Dr. Rao gave 3.5 books per pupil. The U.S. team helped.")), 2)
        self.assertEqual(len(summarize.sentences("He said ‘It worked.’ Another fact.")), 2)
        self.assertEqual(len(summarize.sentences("వారు వచ్చారు। పిల్లలు చదివారు॥ అందరూ సంతోషించారు.")), 3)
        self.assertEqual(len(summarize.sentences("One fact. another fact.")), 2)

    def test_translations_cannot_change_numbers_or_move_numbered_facts(self):
        pairs = copy.deepcopy(PAIRS[:4])
        pairs[1]["te"] = pairs[1]["te"].replace("500", "50")
        with self.assertRaises(ValueError):
            summarize.validate_pairs(pairs)
        pairs = copy.deepcopy(PAIRS[:4])
        pairs[0]["te"], pairs[1]["te"] = pairs[1]["te"], pairs[0]["te"]
        with self.assertRaises(ValueError):
            summarize.validate_pairs(pairs)

    def test_hook_configuration_rejects_shell_strings(self):
        with patch.dict("os.environ", {"GOOD_NEWS_LLM_COMMAND": "python3 hook.py"}), \
                patch.object(subprocess, "run", side_effect=AssertionError("Invalid argv must not execute")):
            with self.assertRaises(ValueError):
                summarize.llm_pairs(item())

    def test_extractive_source_order_and_no_fabricated_padding(self):
        source = " ".join(p["en"] for p in PAIRS)
        self.assertEqual(summarize.canonical("Library opens", source), [p["en"] for p in PAIRS])
        self.assertEqual(len(summarize.canonical("Library opens", PAIRS[0]["en"])), 1)
        self.assertEqual(summarize.canonical("Library opens", "An unfinished description…"), ["Library opens."])

    def test_default_and_false_values_never_launch_a_hook(self):
        for value in (None, "0", "false", "true"):
            env = {} if value is None else {"GOOD_NEWS_LLM": value}
            with patch.dict("os.environ", env, clear=True), patch.object(subprocess, "run", side_effect=AssertionError("Hook forbidden")):
                result = self.run_items([item()])[0]
                self.assertEqual(result["summary_status"], "excerpt")
                self.assertEqual(result["sum_en"], result["sum_te"])
                self.assertEqual(result["sum_en"], "")

    def test_offline_results_and_cache_bytes_are_deterministic(self):
        first = self.run_items([item()])
        contents = self.cache.read_bytes()
        self.assertEqual(first, self.run_items([item()]))
        self.assertEqual(contents, self.cache.read_bytes())

    def test_legacy_pairs_migrate_in_order_and_keep_public_strings(self):
        self.cache.write_text(json.dumps({"library": dict(v=5, en=" ".join(p["en"] for p in PAIRS), te=" ".join(p["te"] for p in PAIRS))}))
        result = self.run_items([item()])[0]
        self.assertEqual(result["summary_status"], "paired")
        for lang in ("en", "te"):
            self.assertEqual(summarize.sentences(result["sum_" + lang]), [p[lang] for p in PAIRS])
        self.assertEqual(json.loads(self.cache.read_text())["library"]["pairs"], PAIRS)

    def test_source_change_invalidates_cache(self):
        self.test_legacy_pairs_migrate_in_order_and_keep_public_strings()
        changed = item()
        changed["title"] = "Different event"
        self.assertEqual(self.run_items([changed])[0]["summary_status"], "excerpt")

    def test_full_description_change_invalidates_cache(self):
        self.test_legacy_pairs_migrate_in_order_and_keep_public_strings()
        changed = item()
        changed["desc"] = "The publisher has corrected the facts in its report."
        self.assertEqual(self.run_items([changed])[0]["summary_status"], "excerpt")

    def test_opted_in_executable_uses_json_stdin_and_caches_result(self):
        hook = Path(self.tmp.name) / "hook.py"
        hook.write_text("import json,sys\nr=json.load(sys.stdin)\nassert r['version']==1\nassert '500 books' in r['story']['desc']\nprint(" + repr(json.dumps({"pairs": PAIRS[:4]})) + ")\n")
        with patch.dict("os.environ", {"GOOD_NEWS_LLM": "1", "GOOD_NEWS_LLM_COMMAND": json.dumps([sys.executable, str(hook)])}):
            result = self.run_items([item()])[0]
            self.assertEqual(result["sum_en"], " ".join(p["en"] for p in PAIRS[:4]))
            self.assertEqual(result["sum_te"], " ".join(p["te"] for p in PAIRS[:4]))
            with patch.object(subprocess, "run", side_effect=AssertionError("Cached result must be reused")):
                self.assertEqual(result, self.run_items([item()])[0])

    def test_hook_failure_and_invalid_output_fall_back_without_partial_pairs(self):
        for failure in (subprocess.TimeoutExpired("hook", 20), subprocess.CalledProcessError(1, "hook"),
                        ValueError("Malformed JSON"), OSError("Missing executable")):
            with patch.dict("os.environ", {"GOOD_NEWS_LLM": "1"}), patch.object(summarize, "llm_pairs", side_effect=failure):
                result = self.run_items([item()])[0]
                self.assertEqual((result["sum_en"], result["sum_te"], result["summary_status"]), ("", "", "excerpt"))

    def test_oversized_hook_output_falls_back(self):
        hook = Path(self.tmp.name) / "large_hook.py"
        hook.write_text("print('x' * 100001)\n")
        with patch.dict("os.environ", {"GOOD_NEWS_LLM": "1", "GOOD_NEWS_LLM_COMMAND": json.dumps([sys.executable, str(hook)])}):
            self.assertEqual(self.run_items([item()])[0]["summary_status"], "excerpt")

    def test_corrupt_cache_does_not_break_build(self):
        self.cache.write_text("{broken")
        self.assertEqual(self.run_items([item()])[0]["summary_status"], "excerpt")

    def test_malformed_cache_entry_can_be_replaced_by_valid_hook_output(self):
        self.cache.write_text(json.dumps({"library": None}))
        with patch.dict("os.environ", {"GOOD_NEWS_LLM": "1"}), patch.object(summarize, "llm_pairs", return_value=PAIRS[:4]):
            self.assertEqual(self.run_items([item()])[0]["summary_status"], "paired")

    def test_cache_evicts_departed_stories_older_than_seven_days(self):
        now = time.time()
        initial_cache = {
            "current_live": dict(v=6, pairs=PAIRS[:4], t=now - 10 * 86400, en="en", te="te", n=4),
            "recent_departed": dict(v=6, pairs=PAIRS[:4], t=now - 2 * 86400, en="en", te="te", n=4),
            "old_departed": dict(v=6, pairs=PAIRS[:4], t=now - 8 * 86400, en="en", te="te", n=4),
            "no_timestamp_departed": dict(v=6, pairs=PAIRS[:4], en="en", te="te", n=4),
        }
        self.cache.write_text(json.dumps(initial_cache))
        live_item = item()
        live_item["id"] = "current_live"
        self.run_items([live_item])
        saved_cache = json.loads(self.cache.read_text())
        self.assertIn("current_live", saved_cache)
        self.assertIn("recent_departed", saved_cache)
        self.assertNotIn("old_departed", saved_cache)
        self.assertNotIn("no_timestamp_departed", saved_cache)


if __name__ == "__main__":
    unittest.main()
