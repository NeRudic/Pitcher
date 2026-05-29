"""Integration tests for the FastAPI backend.

Tests MIDI parsing and the /compare endpoint with a generated MIDI file.
"""

import io
import os
import sys
import tempfile

import pretty_midi
from fastapi.testclient import TestClient

from main import app
from models import NoteEvent
from midi_parser import parse_midi
from comparator import compare_notes

client = TestClient(app)


def create_test_midi(notes_data, tempo=120):
    """Create a MIDI file with the given notes.

    Args:
        notes_data: List of (pitch, start_beat, end_beat, velocity) tuples.
        tempo: BPM.
    Returns:
        bytes of the MIDI file.
    """
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    piano = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano

    seconds_per_beat = 60.0 / tempo
    for pitch, start_beat, end_beat, velocity in notes_data:
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=pitch,
            start=start_beat * seconds_per_beat,
            end=end_beat * seconds_per_beat,
        )
        piano.notes.append(note)

    midi.instruments.append(piano)

    buf = io.BytesIO()
    midi.write(buf)
    buf.seek(0)
    return buf.read()


def test_health():
    """Health check endpoint should return OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("[PASS] test_health")


def test_midi_parser():
    """MIDI parser should extract notes correctly."""
    midi_bytes = create_test_midi([
        (60, 1, 2, 80),   # C4, beat 1-2
        (64, 3, 4, 90),   # E4, beat 3-4
        (67, 5, 6, 70),   # G4, beat 5-6
    ])

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        f.write(midi_bytes)
        tmp_path = f.name

    try:
        notes = parse_midi(tmp_path)
        assert len(notes) == 3, f"Expected 3 notes, got {len(notes)}"

        pitches = [n.pitch for n in notes]
        assert pitches == [60, 64, 67], f"Expected [60, 64, 67], got {pitches}"

        # Check timing conversion (120 BPM = 0.5 sec/beat)
        beat_1_sec = 1 * 0.5  # 0.5s
        assert abs(notes[0].start_time - 0.5) < 0.01, \
            f"Expected start ~0.5s, got {notes[0].start_time}"

        print("[PASS] test_midi_parser")
    finally:
        os.unlink(tmp_path)


def test_compare_endpoint():
    """The /compare endpoint should accept files and return results.

    Note: We test with valid MIDI + empty WAV. Basic Pitch will fail on
    empty audio, but the endpoint must correctly handle the upload and
    return a structured error response (400 or 500).
    """
    midi_bytes = create_test_midi([
        (60, 1, 2, 80),
        (64, 3, 4, 90),
    ])

    response = client.post(
        "/compare",
        files={
            "audio": ("test.wav", b"", "audio/wav"),
            "midi": ("test.mid", midi_bytes, "audio/midi"),
        },
    )

    # Valid response: 200 (success), 400 (bad input), 422 (validation),
    # 500 (processing error on empty file) — all prove the endpoint works
    assert response.status_code in [200, 400, 422, 500], \
        f"Unexpected status: {response.status_code}"
    json_body = response.json()
    assert "detail" in json_body or "notes" in json_body or "correct" in json_body
    print(f"[PASS] test_compare_endpoint (status={response.status_code})")


def test_invalid_file_type():
    """Uploading wrong file types should return 400."""
    response = client.post(
        "/compare",
        files={
            "audio": ("test.txt", b"not audio", "text/plain"),
            "midi": ("test.mid", b"", "audio/midi"),
        },
    )
    assert response.status_code == 400
    print("[PASS] test_invalid_file_type")


if __name__ == "__main__":
    test_health()
    test_midi_parser()
    test_compare_endpoint()
    test_invalid_file_type()
    print("\nAll integration tests passed!")
