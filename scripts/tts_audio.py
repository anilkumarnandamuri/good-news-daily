"""Optional local Telugu narration; public MP3s live in a separate checkout."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://anilkumarnandamuri.github.io/good-news-audio/'
VOICE = 'te_IN-maya-medium'
RATE = '1.0'  # Piper length_scale (1 = normal)


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def key(text, voice=VOICE, rate=RATE):
    return hashlib.sha256(f'{voice}\n{rate}\n{normalize(text)}'.encode()).hexdigest()[:16]


def atomic_json(path, data):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as staged:
        name = Path(staged.name)
        try:
            json.dump(data, staged, ensure_ascii=False, indent=2)
            staged.close()
            name.replace(path)
        finally:
            name.unlink(missing_ok=True)


def generate(items, out, piper, model, ffmpeg, budget=300):
    """Generate atomically, isolate failures, and retain unreferenced clips for 7 days."""
    out = Path(out).resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError('Audio output must be outside the site repository')
    deadline = time.monotonic() + max(0, budget)
    available = bool(shutil.which(piper) and shutil.which(ffmpeg) and Path(model).is_file())
    if not available:
        print('audio skipped: missing Piper, model, or ffmpeg (cached clips still usable)')
    (out / 'te').mkdir(parents=True, exist_ok=True)
    manifest = dict(version=1, order=[], stories={}, intros={}, errors=[])
    referenced = set()
    for story in items:
        text = story.get('sum_te')
        status = story.get('summary_status')
        legacy = status is None and isinstance(story.get('sum_en'), str) and normalize(story['sum_en'])
        if (status not in ('paired', 'summary') and not legacy) or not isinstance(text, str) or not normalize(text):
            continue
        text = normalize(text)
        sid = str(story['id'])
        digest = key(text)
        filename = f'te/{digest}.mp3'
        referenced.add(filename)
        target = out / filename
        try:
            if not target.is_file() or target.stat().st_size == 0:
                if not available:
                    continue
                if time.monotonic() >= deadline:
                    print('audio skipped: time budget exhausted')
                    continue
                with tempfile.TemporaryDirectory(dir=out) as tmp:
                    wav = Path(tmp) / 'speech.wav'
                    mp3 = Path(tmp) / 'speech.mp3'
                    subprocess.run([piper, '--model', str(model), '--length-scale', RATE, '--output_file', str(wav)],
                                   input=text, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   check=True, timeout=max(.001, deadline - time.monotonic()))
                    if time.monotonic() >= deadline:
                        raise TimeoutError('audio time budget exhausted')
                    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav),
                                    '-ac', '1', '-ar', '22050', '-b:a', '32k', str(mp3)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
                                   timeout=max(.001, deadline - time.monotonic()))
                    if not mp3.stat().st_size:
                        raise ValueError('empty MP3')
                    mp3.replace(target)
            manifest['order'].append(sid)
            manifest['stories'][sid] = {'te': dict(file=filename, text=text,
                text_hash=hashlib.sha256(text.encode()).hexdigest(), cache_key=digest, voice=VOICE, rate=RATE)}
        except Exception as exc:
            message = f'{sid}: {type(exc).__name__}'
            manifest['errors'].append(message)
            print('audio failed:', message)
    cutoff = time.time() - 7 * 86400
    for clip in (out / 'te').glob('*.mp3'):
        if clip.relative_to(out).as_posix() not in referenced and clip.stat().st_mtime < cutoff:
            clip.unlink()
    atomic_json(out / 'manifest.json', manifest)
    return manifest


def run(items):
    """Default-off build hook. No audio error may prevent publishing news."""
    if os.environ.get('GOOD_NEWS_AUDIO') != '1':
        return
    try:
        generate(items, os.environ.get('GOOD_NEWS_AUDIO_DIR', str(ROOT.parent / 'good-news-audio')),
                 os.environ.get('GOOD_NEWS_PIPER', '/workspace/tools/piper/venv/bin/piper'),
                 os.environ.get('GOOD_NEWS_PIPER_MODEL', '/workspace/tools/piper/models/te_IN-maya-medium.onnx'),
                 os.environ.get('GOOD_NEWS_FFMPEG', 'ffmpeg'),
                 float(os.environ.get('GOOD_NEWS_AUDIO_BUDGET_S', '300')))
        atomic_json(ROOT / 'data' / 'audio-config.json',
                    {'base_url': os.environ.get('GOOD_NEWS_AUDIO_BASE_URL', BASE_URL).rstrip('/') + '/'})
    except Exception as exc:
        print('audio skipped:', type(exc).__name__, str(exc))
