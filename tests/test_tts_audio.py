import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import tts_audio as audio


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.model = self.out / 'model.onnx'
        self.model.touch()
        self.items = [dict(id='one', summary_status='summary', sum_te='మంచి   వార్తలు.\n')]
        self.calls = []

    def fake(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        path = Path(argv[argv.index('--output_file') + 1] if '--output_file' in argv else argv[-1])
        path.write_bytes(b'fake audio')

    def build(self, **kwargs):
        with patch.object(audio.shutil, 'which', return_value='fake'), patch.object(audio.subprocess, 'run', side_effect=self.fake):
            return audio.generate(self.items, self.out, 'piper', self.model, 'ffmpeg', **kwargs)

    def test_key_cache_and_manifest(self):
        original = copy.deepcopy(self.items)
        manifest = self.build()
        digest = hashlib.sha256('te_IN-maya-medium\n1.0\nమంచి వార్తలు.'.encode()).hexdigest()[:16]
        self.assertEqual(audio.key(self.items[0]['sum_te']), digest)
        entry = manifest['stories']['one']['te']
        self.assertEqual(entry['file'], f'te/{digest}.mp3')
        self.assertEqual(entry['text'], 'మంచి వార్తలు.')
        self.assertEqual(manifest['version'], 1)
        self.assertEqual(manifest['order'], ['one'])
        self.assertEqual(manifest, json.loads((self.out / 'manifest.json').read_text()))
        self.assertEqual(len(self.calls), 2)
        ffmpeg = self.calls[1][0]
        self.assertEqual(ffmpeg[ffmpeg.index('-ac')+1], '1')
        self.assertEqual(ffmpeg[ffmpeg.index('-ar')+1], '22050')
        self.assertEqual(ffmpeg[ffmpeg.index('-b:a')+1], '32k')
        self.build()
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.items, original)
        self.assertNotEqual(audio.key('మంచి వార్తలు.', rate='1.1'), digest)
        self.assertNotEqual(audio.key('మంచి వార్తలు.', voice='other'), digest)

    def test_changed_text_and_rolling_deletion(self):
        first = self.build()['stories']['one']['te']['file']
        self.items[0]['sum_te'] = 'మరొక వార్త.'
        second = self.build()['stories']['one']['te']['file']
        self.assertNotEqual(first, second)
        old = time.time() - 8 * 86400
        for name in (first, second):
            os.utime(self.out / name, (old, old))
        recent = self.out / 'te' / 'recent.mp3'
        recent.touch()
        manifest = self.build()
        self.assertFalse((self.out / first).exists())
        self.assertTrue((self.out / second).exists())
        self.assertTrue(recent.exists())
        self.items = []
        self.assertEqual(self.build()['stories'], {})
        self.assertFalse((self.out / second).exists())
        self.assertEqual(list(manifest['stories']), ['one'])

    def test_budget_missing_binary_and_cached_reuse(self):
        self.assertEqual(self.build(budget=0)['stories'], {})
        self.assertEqual(self.calls, [])
        self.build()
        with patch.object(audio.shutil, 'which', return_value=None), patch.object(audio.subprocess, 'run') as run:
            manifest = audio.generate(self.items, self.out, 'absent', self.model, 'absent')
            self.assertIn('one', manifest['stories'])
            self.items[0]['sum_te'] = 'కొత్త వార్త.'
            self.assertEqual(audio.generate(self.items, self.out, 'absent', self.model, 'absent')['stories'], {})
            run.assert_not_called()

    def test_failure_isolation_no_partial_target(self):
        self.items.append(dict(id='two', summary_status='paired', sum_te='రెండవ వార్త.'))
        fake = self.fake
        def fail_once(argv, **kwargs):
            if kwargs.get('input') == 'మంచి వార్తలు.':
                raise subprocess.TimeoutExpired(argv, 1)
            return fake(argv, **kwargs)
        self.fake = fail_once
        manifest = self.build()
        self.assertNotIn('one', manifest['stories'])
        self.assertIn('two', manifest['stories'])
        self.assertEqual(len(manifest['errors']), 1)
        self.assertEqual(len(list((self.out / 'te').iterdir())), 1)

    def test_opt_in_and_repository_guard(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(audio, 'generate') as generate:
            audio.run(self.items)
            generate.assert_not_called()
        with self.assertRaises(ValueError):
            audio.generate(self.items, audio.ROOT / 'audio', 'piper', self.model, 'ffmpeg')
        with patch.dict(os.environ, {'GOOD_NEWS_AUDIO': '1'}, clear=True), patch.object(audio, 'generate', side_effect=OSError('disk')):
            audio.run(self.items)  # never fail the news build

    def test_only_eligible_summaries(self):
        self.items += [dict(id='excerpt', summary_status='excerpt', sum_te='వార్త.'),
                       dict(id='blank', summary_status='summary', sum_te='   ')]
        self.assertEqual(list(self.build()['stories']), ['one'])

    def test_enabled_hook_writes_only_host_config_and_passes_settings(self):
        root = self.out / 'site'
        (root / 'data').mkdir(parents=True)
        env = dict(GOOD_NEWS_AUDIO='1', GOOD_NEWS_AUDIO_DIR=str(self.out / 'clips'),
                   GOOD_NEWS_PIPER='fake-piper', GOOD_NEWS_PIPER_MODEL=str(self.model),
                   GOOD_NEWS_FFMPEG='fake-ffmpeg', GOOD_NEWS_AUDIO_BUDGET_S='12',
                   GOOD_NEWS_AUDIO_BASE_URL='https://audio.example/custom')
        with patch.dict(os.environ, env, clear=True), patch.object(audio, 'ROOT', root), patch.object(audio, 'generate') as generate:
            audio.run(self.items)
            generate.assert_called_once_with(self.items, str(self.out / 'clips'), 'fake-piper',
                                             str(self.model), 'fake-ffmpeg', 12.0)
        self.assertEqual(json.loads((root / 'data/audio-config.json').read_text()),
                         {'base_url': 'https://audio.example/custom/'})
        self.assertEqual([p.name for p in (root / 'data').iterdir()], ['audio-config.json'])

    def test_deadline_between_synthesis_and_encoding(self):
        # Start, pre-story, synthesis timeout, then the shared deadline has elapsed.
        with patch.object(audio.time, 'monotonic', side_effect=[0, 0, 0, 11]):
            result = self.build(budget=10)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]['timeout'], 10)
        self.assertEqual(result['stories'], {})
        self.assertFalse(list((self.out / 'te').iterdir()))
