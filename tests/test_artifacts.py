import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import summarize


def luminance(color):
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    values = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    values = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in values]
    return sum(c * w for c, w in zip(values, (.2126, .7152, .0722)))


class ArtifactContracts(unittest.TestCase):
    def test_routine_and_push_files_are_byte_identical_to_baseline(self):
        hashes = {
            "push.js": "ed65256d7b87639055061218785d79aeb93a7130ceabe105e0f9ff05fd2b223d",
            "OneSignalSDKWorker.js": "7c5c1ccc7b9a59a36a93c15f99e3d335468452ab4d6278fab5ed233bfa786621",
            "scripts/build.py": "2df880547d86bb68c37088688e4328b310e8d52ebee0e80015bb0a1d29bd94f0",
            "scripts/send_push.py": "0d42a1808ec2fbba36efe567f46b2e8bb0653daba58effb1b09e096a01be4a58",
            "scripts/digest.py": "6c7edee40b1bf9760a07dc1115b0b6c8d981b7f692289d660d3d1005432ede5a",
        }
        for name, digest in hashes.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_published_summaries_have_four_to_six_pairs_or_explicit_excerpt(self):
        data = json.loads((ROOT / "data/news.json").read_text())
        cache = json.loads((ROOT / "data/summaries.json").read_text())
        self.assertEqual(data["count"], len(data["items"]))
        complete = 0
        for item in data["items"]:
            with self.subTest(story=item["id"]):
                if "summary_status" not in item:
                    has_en = isinstance(item.get("sum_en"), str) and bool(item.get("sum_en"))
                    has_te = isinstance(item.get("sum_te"), str) and bool(item.get("sum_te"))
                    self.assertEqual(has_en, has_te)
                    if has_en and has_te:
                        complete += 1
                    else:
                        self.assertEqual((item.get("sum_en", ""), item.get("sum_te", "")), ("", ""))
                elif item["summary_status"] == "paired":
                    pairs = summarize.legacy_pairs(item["sum_en"], item["sum_te"])
                    self.assertEqual(pairs, cache[item["id"]]["pairs"])
                    complete += 1
                else:
                    self.assertEqual(item["summary_status"], "excerpt")
                    self.assertEqual((item["sum_en"], item["sum_te"]), ("", ""))
        self.assertGreater(complete, 0)

    def test_text_palette_meets_aa_contrast_in_both_themes(self):
        css = (ROOT / "styles.css").read_text()
        rules = {}
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            rules.setdefault(selector.strip(), {}).update(dict(
                (k.strip(), v.strip()) for k, v in
                (part.split(":", 1) for part in body.split(";") if ":" in part)))
        light = rules[":root"]
        dark = light | rules["[data-theme=dark]"]
        combinations = []
        for theme in (light, dark):
            for ink in ("--ink", "--mute", "--acc", "--health"):
                for bg in ("--bg", "--bg2"):
                    combinations.append((theme[ink], theme[bg]))
        for selector in (".pill", ".push-btn,.r-cta", ".r-wa", ".t5-ok"):
            combinations.append((rules[selector]["color"], rules[selector]["background"]))
        combinations += [("#2a1608", "#ff7a8a"), (rules[".th-k"]["color"], "#ffe9d6"),
                         (rules["[data-theme=dark] .th-k"]["color"], "#2b2114")]
        for foreground, background in combinations:
            a, b = sorted((luminance(foreground), luminance(background)))
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual((b + .05) / (a + .05), 4.5)

    def test_local_font_license_and_static_assets_exist(self):
        self.assertGreater((ROOT / "fonts/NotoSansTelugu-Regular.ttf").stat().st_size, 1000)
        self.assertIn("SIL Open Font License", (ROOT / "fonts/OFL.txt").read_text())
        page = (ROOT / "index.html").read_text()
        self.assertNotIn("fonts.googleapis.com", page)
        for asset in re.findall(r'(?:src|href)="([^"#?:]+\.(?:css|js|png|webmanifest))"', page):
            self.assertTrue((ROOT / asset).exists(), asset)


if __name__ == "__main__":
    unittest.main()
