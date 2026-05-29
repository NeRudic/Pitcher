"""Preprocess reference MIDI and test WAV files into JSON for fast test loading.

Run this script ONCE to parse all files and cache the results.
Tests then load the JSON files directly instead of re-parsing every time.

Usage:
    py -3.11 tests/preprocess.py
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path so we can import project modules
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from midi_parser import parse_midi
from audio_parser import parse_audio
from models import NoteEvent

# -- Paths ------------------------------------------------------------
TESTS_DIR = ROOT / "tests"
REFERENCE_MID = TESTS_DIR / "Reference.mid"
WAV_FILES = {
    "done": TESTS_DIR / "Done.wav",
    "failnote": TESTS_DIR / "FailNote.wav",
    "failtempo": TESTS_DIR / "FailTempo.wav",
}
OUTPUT_DIR = TESTS_DIR / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _notes_to_json(notes: list[NoteEvent]) -> list[dict]:
    """Convert NoteEvent list to a list of JSON-serializable dicts."""
    return [n.model_dump() for n in notes]


def _save_json(data: list[dict], name: str) -> None:
    """Save notes data as formatted JSON."""
    path = OUTPUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Saved {len(data)} notes -> {path}")


def main() -> None:
    print("=" * 60)
    print("Preprocessing -- parse once, test many times")
    print("=" * 60)

    # 1. Parse reference MIDI
    print("\n[1/4] Parsing Reference.mid ...")
    ref_notes = parse_midi(str(REFERENCE_MID))
    _save_json(_notes_to_json(ref_notes), "reference")
    print(f"       Reference has {len(ref_notes)} notes")
    for i, n in enumerate(ref_notes):
        print(f"       #{i+1}: pitch={n.pitch}, start={n.start_time:.3f}s, "
              f"end={n.end_time:.3f}s, velocity={n.velocity}")

    # 2-4. Parse each test WAV file
    for label, wav_path in WAV_FILES.items():
        idx = list(WAV_FILES.keys()).index(label) + 2
        print(f"\n[{idx}/4] Parsing {wav_path.name} ...")
        notes = parse_audio(str(wav_path))
        _save_json(_notes_to_json(notes), label)
        print(f"       Extracted {len(notes)} notes:")
        for i, n in enumerate(notes):
            amp_str = f"{n.amplitude:.3f}" if n.amplitude is not None else "N/A"
            print(f"       #{i+1}: pitch={n.pitch:.1f}, start={n.start_time:.3f}s, "
                  f"end={n.end_time:.3f}s, amp={amp_str}")

    print("\n" + "=" * 60)
    print("All files preprocessed. Tests can now use tests/data/*.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
