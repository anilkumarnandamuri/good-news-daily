"""Offline validation of feed mapping and the delivered real audio manifest."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_audio as audio
ROOT = Path(__file__).resolve().parents[1]


class BuildAudioTests(unittest.TestCase):
    def test_selection_and_mapping(self):
        stories = [{'id': str(i)} for i in range(8)]
        self.assertEqual(audio.select_stories({'items': stories}), stories[:5])
        self.assertEqual(audio.select_stories(stories, 0), stories)
        with self.assertRaises(ValueError):
            audio.select_stories([{'id': 'same'}, {'id': 'same'}])
        self.assertEqual(audio.story_text({'lang': 'en-IN', 'summary': '<p>Hello</p>'}, 'en'), 'Hello')
        self.assertEqual(audio.story_text({'lang': 'en', 'summary': 'Hello'}, 'te'), '')

    def test_cache_invalidates_for_text_voice_and_rate(self):
        key = audio.cache_key('Hello', 'voice', '+0%')
        for args in [('Hi', 'voice', '+0%'), ('Hello', 'other', '+0%'), ('Hello', 'voice', '-10%')]:
            self.assertNotEqual(key, audio.cache_key(*args))
        self.assertEqual(audio.parse_voices('te=te-IN-MohanNeural')['en'], audio.DEFAULT_VOICES['en'])

    def test_delivered_manifest_matches_sample(self):
        manifest = json.loads((ROOT / 'demo/audio/manifest.json').read_text())
        feed = json.loads((ROOT / 'sample/news.json').read_text())
        selected = audio.select_stories(feed)
        self.assertEqual(manifest['order'], [s['id'] for s in selected])
        self.assertEqual(manifest['errors'], [])
        for story in selected:
            for lang in ['te', 'en']:
                entry = manifest['stories'][story['id']][lang]
                text = audio.story_text(story, lang)
                self.assertEqual(entry['text'], text)
                self.assertEqual(entry['text_hash'], hashlib.sha256(text.encode()).hexdigest())
                path = ROOT / 'demo/audio' / entry['file']
                self.assertGreater(path.stat().st_size, 256)
                self.assertGreater(audio.duration(path), 1)
        for lang, entry in manifest['intros'].items():
            self.assertEqual(entry['text'], audio.INTROS[lang])
        for entry in manifest.get('radio', {}).values():
            self.assertTrue((ROOT / 'demo/audio' / entry['file']).is_file())


if __name__ == '__main__':
    unittest.main()
