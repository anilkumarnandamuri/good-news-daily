"""Offline runner contract tests; all publishing/build commands are local stubs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / 'scripts/routine_run.sh'
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
if name == 'python3':
    step = 'build' if args == ['scripts/build.py'] else 'send_push'
elif name == 'audio-stub':
    step = 'publish_audio'
else:
    step = args[0]
with open(os.environ['CALLS'], 'a') as f:
    f.write(json.dumps([step, args, os.environ.get('GOOD_NEWS_AUDIO'),
                        os.environ.get('GOOD_NEWS_AUDIO_DIR')]) + '\n')
# Deliberately noisy commands must never leak their output through the runner.
print(os.environ['ONESIGNAL_API_KEY'], file=sys.stderr)
if step not in ('symbolic-ref', 'status'):
    print('https://user:secret-token@example.invalid/auth-file')
if step == os.environ.get('FAIL_STEP'):
    sys.exit(2)
if step == 'symbolic-ref':
    print(os.environ.get('BRANCH', 'main'))
elif step == 'status':
    print(' M data/audio-config.json' if os.environ.get('CONFIG_CHANGED') else '', end='')
elif step == 'diff':
    sys.exit(0 if os.environ.get('NO_CHANGES') else 1)
'''


class RoutineRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'scripts').mkdir()
        shutil.copy2(RUNNER, self.root / 'scripts/routine_run.sh')
        (self.root / 'scripts/publish_audio.sh').write_text('audio-stub "$@"\n')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        # Use an absolute interpreter so the python3 stub cannot recurse.
        import sys
        fake = FAKE.replace('#!/usr/bin/env python3', '#!' + sys.executable, 1)
        for name in ('git', 'python3', 'audio-stub'):
            path = self.bin / name
            path.write_text(fake)
            path.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                        CALLS=str(self.root / 'calls'), ONESIGNAL_API_KEY='private-key-fixture')
        for key in ('FAIL_STEP', 'BRANCH', 'CONFIG_CHANGED', 'NO_CHANGES',
                    'BASH_ENV', 'SHELLOPTS', 'BASHOPTS'):
            self.env.pop(key, None)

    def run_script(self, **env):
        result = subprocess.run(['/bin/bash', str(self.root / 'scripts/routine_run.sh')],
                                cwd='/tmp', env=dict(self.env, **env),
                                capture_output=True, text=True)
        calls = [json.loads(line) for line in (self.root / 'calls').read_text().splitlines()]
        output = result.stdout + result.stderr
        for secret in ('private-key-fixture', 'secret-token', 'auth-file'):
            self.assertNotIn(secret, output)
        self.assertEqual(len(result.stdout.splitlines()), 6)
        self.assertEqual(result.stderr, '')
        return result, calls

    def test_order_environment_and_commit_scope(self):
        result, calls = self.run_script(CONFIG_CHANGED='1')
        self.assertEqual(result.returncode, 0)
        self.assertEqual([c[0] for c in calls], [
            'symbolic-ref', 'pull', 'build', 'publish_audio', 'status',
            'add', 'diff', 'commit', 'push', 'send_push'])
        self.assertEqual(calls[1][1], ['pull', '--ff-only', 'origin', 'main'])
        self.assertEqual(calls[2][2], '1')
        self.assertEqual(calls[3][1:], [['--push'], None, '/workspace/good-news-audio'])
        paths = ['data/news.json', 'data/audio-config.json']
        self.assertEqual(calls[5][1], ['add', '--'] + paths)
        self.assertEqual(calls[7][1], ['commit', '--only', '-m', 'Refresh daily good news', '--'] + paths)
        self.assertEqual(calls[8][1], ['push', 'origin', 'main'])
        self.assertNotIn('data/summaries.json', str(calls))

    def test_unchanged_audio_config_excluded(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0)
        for step, args, *_ in calls:
            if step in ('add', 'diff', 'commit'):
                self.assertNotIn('data/audio-config.json', args)

    def test_audio_failure_is_nonfatal(self):
        result, calls = self.run_script(FAIL_STEP='publish_audio')
        self.assertEqual(result.returncode, 0)
        self.assertIn('publish_audio: fail', result.stdout)
        self.assertEqual([c[0] for c in calls][-3:], ['commit', 'push', 'send_push'])

    def test_failures_stop_dependent_steps(self):
        for failure in ('pull', 'build', 'status', 'add', 'diff', 'commit', 'push', 'send_push'):
            with self.subTest(step=failure):
                (self.root / 'calls').unlink(missing_ok=True)
                result, calls = self.run_script(FAIL_STEP=failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls[-1][0], failure)
                if failure != 'send_push':
                    self.assertNotIn('send_push', [c[0] for c in calls])
                    self.assertIn('send_push: skip', result.stdout)

    def test_no_changes_still_pushes_and_notifies(self):
        result, calls = self.run_script(NO_CHANGES='1')
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('commit', [c[0] for c in calls])
        self.assertEqual([c[0] for c in calls][-2:], ['push', 'send_push'])
        self.assertIn('commit: ok (no changes)', result.stdout)

    def test_refuses_job_branch(self):
        result, calls = self.run_script(BRANCH='job/GN-7')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([c[0] for c in calls], ['symbolic-ref'])

    def test_real_git_excludes_pre_staged_cache_and_unrelated_files(self):
        real_git = shutil.which('git')

        def git(*args):
            return subprocess.check_output([real_git, *args], cwd=self.root, text=True,
                                           stderr=subprocess.PIPE)

        git('init', '-b', 'main')
        git('config', 'user.email', 'offline@example.invalid')
        git('config', 'user.name', 'Offline Test')
        git('config', 'commit.gpgsign', 'false')
        git('config', 'core.hooksPath', '/dev/null')
        (self.root / 'data').mkdir()
        originals = ('data/news.json', 'data/audio-config.json', 'data/summaries.json', 'other.txt')
        for name in originals:
            (self.root / name).write_text('original\n')
        git('add', '--', *originals)
        git('commit', '-m', 'fixture')
        for name in originals:
            (self.root / name).write_text('changed\n')
        git('add', '--', 'data/summaries.json', 'other.txt')
        # Only transport is stubbed; staging/commit use an isolated real repo.
        fake = (self.bin / 'git').read_text()
        fake = fake.replace('# Deliberately noisy commands',
                            "if step not in ('pull', 'push'):\n"
                            f"    os.execv({real_git!r}, [{real_git!r}] + args)\n"
                            '# Deliberately noisy commands')
        (self.bin / 'git').write_text(fake)
        result, _ = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()),
                         {'data/news.json', 'data/audio-config.json'})
        self.assertEqual(git('show', 'HEAD:data/summaries.json'), 'original\n')
        self.assertEqual(set(git('diff', '--cached', '--name-only').splitlines()),
                         {'data/summaries.json', 'other.txt'})

    def test_runner_is_executable(self):
        self.assertTrue(os.access(RUNNER, os.X_OK))


if __name__ == '__main__':
    unittest.main()
