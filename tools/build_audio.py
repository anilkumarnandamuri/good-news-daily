#!/usr/bin/env python3
"""Generate cached Telugu/English MP3s for a Good News Daily news.json feed."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_VOICES = {"te": "te-IN-ShrutiNeural", "en": "en-IN-NeerjaNeural"}
INTROS = {"te": "మంచి వార్తలు. ఇప్పుడు వార్త వినండి.",
          "en": "Manchi Vaarthalu. Here is your next story."}


def clean_text(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", str(value or ""))).strip()


def story_text(story, lang):
    return clean_text(story.get(f"sum_{lang}") or
                      (story.get("summary") if str(story.get("lang", "")).split("-")[0] == lang else ""))


def select_stories(data, limit=5):
    items = data if isinstance(data, list) else data.get("items", [])
    if not isinstance(items, list):
        raise ValueError("Expected a JSON array or an object with an items array")
    selected = items[:limit] if limit else items
    seen = set()
    for story in selected:
        if not isinstance(story, dict) or not str(story.get("id", "")).strip():
            raise ValueError("Each selected story must have a nonempty id")
        sid = str(story["id"])
        if sid in seen:
            raise ValueError(f"Duplicate story id: {sid}")
        seen.add(sid)
    return selected


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_key(text, voice, rate):
    return digest(json.dumps([text, voice, rate, 1], ensure_ascii=False))


def duration(path):
    if not shutil.which("ffprobe"):
        return None
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                                capture_output=True, text=True, check=True, timeout=15)
        return round(float(result.stdout), 3)
    except (ValueError, subprocess.SubprocessError):
        return None


def atomic_json(path, data):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_voices(value):
    voices = DEFAULT_VOICES.copy()
    for item in value.split(","):
        lang, sep, voice = item.partition("=")
        if not sep or lang not in voices or not voice.strip():
            raise argparse.ArgumentTypeError("Use te=te-IN-ShrutiNeural,en=en-IN-NeerjaNeural")
        voices[lang] = voice.strip()
    return voices


async def build(args):
    import edge_tts
    data = json.loads(args.input.read_text(encoding="utf-8"))
    stories = select_stories(data, 0 if args.all else args.limit)
    args.out.mkdir(parents=True, exist_ok=True)
    gate = asyncio.Semaphore(args.concurrency)
    errors = []
    manifest = {"version": 1, "generated": datetime.now(timezone.utc).isoformat(),
                "order": [str(s["id"]) for s in stories], "stories": {}, "intros": {}}

    async def generate(label, lang, text):
        voice = args.voices[lang]
        key = cache_key(text, voice, args.rate)
        safe_label = re.sub(r"[^a-zA-Z0-9_-]", "_", label)[:60]
        filename = f"{safe_label}-{digest(label)[:8]}-{lang}-{key[:16]}.mp3"
        target = args.out / filename
        async with gate:
            if not target.exists() or target.stat().st_size < 256 or args.force:
                for attempt in range(args.retries + 1):
                    temporary = target.with_suffix(".mp3.tmp")
                    try:
                        communicate = edge_tts.Communicate(text, voice, rate=args.rate,
                                                          connect_timeout=15, receive_timeout=45)
                        await asyncio.wait_for(communicate.save(str(temporary)), timeout=args.timeout)
                        if temporary.stat().st_size < 256:
                            raise RuntimeError("TTS returned an empty audio file")
                        temporary.replace(target)
                        print(f"BUILT {filename}", flush=True)
                        break
                    except Exception as exc:
                        temporary.unlink(missing_ok=True)
                        if attempt == args.retries:
                            errors.append(f"{label}/{lang}: {type(exc).__name__}: {exc}")
                            print(f"FAILED {errors[-1]}", file=sys.stderr, flush=True)
                            return None
                        print(f"RETRY {label}/{lang} ({attempt + 1}): {exc}", file=sys.stderr, flush=True)
                        await asyncio.sleep(min(2 ** attempt, 8))
            else:
                print(f"CACHED {filename}", flush=True)
            return {"file": filename, "duration": await asyncio.to_thread(duration, target),
                    "text": text, "text_hash": digest(text), "cache_key": key,
                    "voice": voice, "rate": args.rate}

    async def story_job(story):
        sid = str(story["id"])
        entries = {}
        for lang in args.languages:
            text = story_text(story, lang)
            if not text:
                print(f"SKIP {sid}/{lang}: no summary in this language", flush=True)
                continue
            entry = await generate(sid, lang, text)
            if entry:
                entries[lang] = entry
        manifest["stories"][sid] = entries

    async def intro_job(lang):
        entry = await generate("intro", lang, INTROS[lang])
        if entry:
            manifest["intros"][lang] = entry

    await asyncio.gather(*(story_job(s) for s in stories),
                         *(intro_job(lang) for lang in args.languages if not args.no_intros))
    if args.radio:
        if not shutil.which("ffmpeg"):
            errors.append("--radio requires ffmpeg")
        else:
            manifest["radio"] = {}
            for lang in args.languages:
                clips = []
                for sid in manifest["order"]:
                    entry = manifest["stories"][sid].get(lang)
                    if not entry:
                        continue
                    if lang in manifest["intros"]:
                        clips.append(manifest["intros"][lang]["file"])
                    clips.append(entry["file"])
                if not clips:
                    continue
                radio_key = digest(json.dumps(clips))[:16]
                output = args.out / f"radio-{lang}-{radio_key}.mp3"
                # Relative filenames are generated above and contain only safe characters.
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", dir=args.out, delete=False) as handle:
                    handle.write("\n".join(f"file '{name}'" for name in clips))
                    listing = Path(handle.name)
                try:
                    await asyncio.to_thread(subprocess.run,
                        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
                         "-safe", "1", "-i", str(listing), "-c", "copy", str(output)],
                        check=True, timeout=90)
                    manifest["radio"][lang] = {"file": output.name, "duration": duration(output),
                                               "order": [sid for sid in manifest["order"] if lang in manifest["stories"][sid]]}
                except (subprocess.SubprocessError, OSError) as exc:
                    errors.append(f"radio/{lang}: {exc}")
                finally:
                    listing.unlink(missing_ok=True)
    manifest["errors"] = errors
    atomic_json(args.out / "manifest.json", manifest)
    print(f"Manifest: {args.out / 'manifest.json'} ({len(stories)} stories, {len(errors)} errors)")
    return 1 if errors else 0


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, required=True)
    cli.add_argument("--out", type=Path, default=Path("demo/audio"))
    cli.add_argument("--limit", type=int, default=5, help="First N in feed order; 0 means all (default: 5)")
    cli.add_argument("--all", action="store_true", help="Generate every story")
    cli.add_argument("--voices", type=parse_voices, default=DEFAULT_VOICES,
                     help="te=te-IN-ShrutiNeural,en=en-IN-NeerjaNeural")
    cli.add_argument("--languages", nargs="+", choices=["te", "en"], default=["te", "en"])
    cli.add_argument("--rate", default="+0%", help="Synthesis rate, e.g. --rate=-10%%; UI defaults to 0.9x")
    cli.add_argument("--concurrency", type=int, default=2)
    cli.add_argument("--retries", type=int, default=2, help="Retries after the initial attempt")
    cli.add_argument("--timeout", type=float, default=90, help="Seconds per synthesis attempt")
    cli.add_argument("--force", action="store_true")
    cli.add_argument("--no-intros", action="store_true")
    cli.add_argument("--radio", action="store_true", help="Also concatenate one radio MP3 per language (ffmpeg)")
    return cli


def main():
    cli = parser()
    args = cli.parse_args()
    if args.limit < 0 or args.concurrency < 1 or args.retries < 0 or args.timeout <= 0:
        cli.error("limit/retries must be nonnegative; concurrency/timeout must be positive")
    if not re.fullmatch(r"[+-]\d+%", args.rate):
        cli.error("rate must look like +0% or -10%; use --rate=-10%")
    try:
        return asyncio.run(build(args))
    except (ValueError, OSError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
