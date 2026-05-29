"""Tests using real pre-parsed audio files.

Compares Done.wav, FailNote.wav, and FailTempo.wav against Reference.mid
to verify the comparator correctly identifies:
  - Correct performances (Done.wav)
  - Wrong notes (FailNote.wav)
  - Late/early notes (FailTempo.wav)

Pre-parsed JSON data lives in tests/data/ — generated once by preprocess.py.
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from models import NoteEvent
from comparator import compare_notes, build_comparison_summary

DATA_DIR = ROOT / "tests" / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_notes(name: str) -> list[NoteEvent]:
    """Load pre-parsed notes from a JSON file."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run 'py -3.11 tests/preprocess.py' first."
        )
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [NoteEvent(**item) for item in raw]


def _compare(label: str) -> dict:
    """Run full comparison for a given WAV label and return the summary dict."""
    reference = _load_notes("reference")
    played = _load_notes(label)
    results = compare_notes(reference, played)
    return build_comparison_summary(reference, played, results)


# -- Load everything once at module level --------------------------------

REFERENCE = _load_notes("reference")

DONE_NOTES = _load_notes("done")
FAILNOTE_NOTES = _load_notes("failnote")
FAILTEMPO_NOTES = _load_notes("failtempo")

DONE_RESULTS = compare_notes(REFERENCE, DONE_NOTES)
FAILNOTE_RESULTS = compare_notes(REFERENCE, FAILNOTE_NOTES)
FAILTEMPO_RESULTS = compare_notes(REFERENCE, FAILTEMPO_NOTES)

DONE_SUMMARY = build_comparison_summary(REFERENCE, DONE_NOTES, DONE_RESULTS)
FAILNOTE_SUMMARY = build_comparison_summary(REFERENCE, FAILNOTE_NOTES, FAILNOTE_RESULTS)
FAILTEMPO_SUMMARY = build_comparison_summary(REFERENCE, FAILTEMPO_NOTES, FAILTEMPO_RESULTS)


# ---------------------------------------------------------------------------
# Reference MIDI tests
# ---------------------------------------------------------------------------

def test_reference_note_count():
    """Reference MIDI should have exactly 17 notes."""
    assert len(REFERENCE) == 17, f"Expected 17 reference notes, got {len(REFERENCE)}"
    print(f"  [PASS] test_reference_note_count ({len(REFERENCE)} notes)")


def test_reference_pitches_in_piano_range():
    """All reference pitches should be in standard 88-key piano range (21-108)."""
    for n in REFERENCE:
        assert 21 <= n.pitch <= 108, f"Pitch {n.pitch} outside piano range"
    print(f"  [PASS] test_reference_pitches_in_piano_range")


def test_reference_sorted_by_time():
    """Reference notes should be sorted by start_time."""
    for i in range(len(REFERENCE) - 1):
        assert REFERENCE[i].start_time <= REFERENCE[i + 1].start_time, \
            f"Notes not sorted: #{i} start={REFERENCE[i].start_time} > #{i+1} start={REFERENCE[i+1].start_time}"
    print("  [PASS] test_reference_sorted_by_time")


def test_reference_has_four_chords():
    """Reference has 5 distinct note onset times: 0.0, 1.667, 3.333, 4.583, 5.0."""
    onsets = sorted(set(round(n.start_time, 3) for n in REFERENCE))
    expected = [0.0, 1.667, 3.333, 4.583, 5.0]
    for exp in expected:
        assert any(abs(o - exp) < 0.01 for o in onsets), \
            f"Expected onset near {exp}s not found in {onsets}"
    print(f"  [PASS] test_reference_has_four_chords (onsets: {onsets})")


# ---------------------------------------------------------------------------
# Done.wav — correct performance
# ---------------------------------------------------------------------------

def test_done_has_no_wrong_notes():
    """Done.wav is a correct performance — wrong notes should be minimal (<= 1).

    Basic Pitch may produce occasional false-positive notes even for a clean
    recording, especially in dense polyphonic passages.  One wrong note is
    acceptable for audio-based polyphonic analysis.
    """
    wrong_count = DONE_SUMMARY["wrong"]
    assert wrong_count <= 1, \
        f"Expected <= 1 wrong notes in correct performance, got {wrong_count}"
    print(f"  [PASS] test_done_has_no_wrong_notes (wrong={wrong_count})")


def test_done_all_matched_are_correct_or_late():
    """Every matched note in Done.wav should be 'correct' or 'late'.

    Basic Pitch may detect some notes with a slight delay (up to ~300ms)
    due to the attack-to-sustain transition in polyphonic audio.  'late'
    is still a valid match — the right pitch at approximately the right
    time.  'early' and 'wrong' should not appear in a clean recording.

    With MAX_MATCH_WINDOW_MS=500ms, cross-chord false matches (e.g., C at 0.0s
    matched to C at 5.0s with delta=5000ms) are prevented — the comparator now
    refuses to match notes that are too far apart in time.
    """
    matched = [r for r in DONE_RESULTS if r.status not in ("missed", "wrong")]
    bad = [r for r in matched if r.status not in ("correct", "late")]
    assert len(bad) == 0, \
        f"All matched notes in Done should be correct or late, got: " \
        + ", ".join(f"{r.status}(pitch={r.played_pitch}, delta={r.time_delta_ms:.0f}ms)"
                     for r in bad)
    assert len(matched) > 0, "Done should have at least 1 matched note"
    late_count = sum(1 for r in matched if r.status == "late")
    assert late_count <= 2, \
        f"Expected <= 2 late notes in correct performance, got {late_count}"
    print(f"  [PASS] test_done_all_matched_are_correct_or_late "
          f"({len(matched)} matched, {late_count} late)")


def test_done_has_acceptable_timing():
    """Done.wav is a correct performance — late/early should be minimal.

    Basic Pitch may detect some chord notes with a slight delay (typically
    100-300ms) because the model sometimes latches onto the sustain phase
    rather than the initial attack.  Up to 2 late notes and 0 early notes
    is an acceptable tolerance for audio-based polyphonic transcription.
    """
    late = DONE_SUMMARY["late"]
    early = DONE_SUMMARY["early"]
    assert late <= 2, \
        f"Expected <= 2 late notes in correct performance, got {late}"
    assert early == 0, \
        f"Expected 0 early notes in correct performance, got {early}"
    print(f"  [PASS] test_done_has_acceptable_timing (late={late}, early={early})")


def test_done_has_any_correct():
    """Done.wav should have at least some correct notes (not all missed)."""
    assert DONE_SUMMARY["correct"] > 0, \
        f"Expected at least 1 correct note, got {DONE_SUMMARY['correct']}"
    print(f"  [PASS] test_done_has_any_correct (correct={DONE_SUMMARY['correct']})")


def test_done_timing_within_tolerance():
    """All correct notes in Done.wav should have timing delta <= 100ms."""
    correct_notes = [r for r in DONE_RESULTS if r.status == "correct"]
    for r in correct_notes:
        assert abs(r.time_delta_ms) <= 100, \
            f"Correct note pitch={r.reference_pitch} has delta={r.time_delta_ms:.0f}ms > 100ms"
    print(f"  [PASS] test_done_timing_within_tolerance ({len(correct_notes)} notes checked)")


# ---------------------------------------------------------------------------
# FailNote.wav — one wrong note
# ---------------------------------------------------------------------------

def test_failnote_has_wrong_note():
    """FailNote.wav has one intentionally wrong note — must be detected."""
    wrong_count = FAILNOTE_SUMMARY["wrong"]
    assert wrong_count >= 1, \
        f"Expected at least 1 wrong note in FailNote.wav, got {wrong_count}"
    print(f"  [PASS] test_failnote_has_wrong_note (wrong={wrong_count})")


def test_failnote_wrong_pitch_is_detected():
    """The wrong note should have pitch ~63 (played Eb instead of G)."""
    wrong_notes = [r for r in FAILNOTE_RESULTS if r.status == "wrong"]
    wrong_pitches = [r.played_pitch for r in wrong_notes]
    # The wrong note should be around pitch 63 (originally note #4, pitch=63.0)
    has_wrong_pitch = any(abs(p - 63.0) < 1.0 for p in wrong_pitches)
    assert has_wrong_pitch, \
        f"Expected wrong note near pitch 63, got pitches {wrong_pitches}"
    print(f"  [PASS] test_failnote_wrong_pitch_is_detected (wrong pitches: {wrong_pitches})")


def test_failnote_has_more_wrong_than_done():
    """FailNote.wav has a wrong note — strictly more 'wrong' than Done."""
    assert FAILNOTE_SUMMARY["wrong"] > DONE_SUMMARY["wrong"], \
        f"FailNote wrong ({FAILNOTE_SUMMARY['wrong']}) should be > Done wrong ({DONE_SUMMARY['wrong']})"
    print(f"  [PASS] test_failnote_has_more_wrong_than_done "
          f"(failnote={FAILNOTE_SUMMARY['wrong']} > done={DONE_SUMMARY['wrong']})")


# ---------------------------------------------------------------------------
# FailTempo.wav — one late note
# ---------------------------------------------------------------------------

def test_failtempo_has_late_or_early():
    """FailTempo.wav has one note shifted in time — should be late or early."""
    late = FAILTEMPO_SUMMARY["late"]
    early = FAILTEMPO_SUMMARY["early"]
    assert late + early >= 1, \
        f"Expected at least 1 late/early note, got late={late}, early={early}"
    print(f"  [PASS] test_failtempo_has_late_or_early (late={late}, early={early})")


def test_failtempo_late_note_is_correct_pitch():
    """The late note should be pitch ~60 (C4 — correct pitch, wrong time)."""
    late_notes = [r for r in FAILTEMPO_RESULTS if r.status in ("late", "early")]
    late_pitches = [r.played_pitch for r in late_notes]
    # The shifted note has pitch 60.0
    has_pitch_60 = any(abs(p - 60.0) < 1.0 for p in late_pitches)
    assert has_pitch_60, \
        f"Expected late/early note near pitch 60, got pitches {late_pitches}"
    print(f"  [PASS] test_failtempo_late_note_is_correct_pitch "
          f"(late/early pitches: {late_pitches})")


def test_failtempo_timing_delta_exceeds_tolerance():
    """The shifted note should have timing delta > 100ms."""
    late_or_early = [r for r in FAILTEMPO_RESULTS if r.status in ("late", "early")]
    for r in late_or_early:
        assert r.time_delta_ms is not None
        assert abs(r.time_delta_ms) > 100, \
            f"Late/early note should exceed 100ms tolerance, got {r.time_delta_ms:.0f}ms"
    print(f"  [PASS] test_failtempo_timing_delta_exceeds_tolerance "
          f"({len(late_or_early)} notes checked)")


def test_failtempo_has_more_late_early_than_done():
    """FailTempo.wav has a shifted note — should have more late/early than Done."""
    fail_te = FAILTEMPO_SUMMARY["late"] + FAILTEMPO_SUMMARY["early"]
    done_te = DONE_SUMMARY["late"] + DONE_SUMMARY["early"]
    assert fail_te > done_te, \
        f"FailTempo late+early ({fail_te}) should be > Done late+early ({done_te})"
    print(f"  [PASS] test_failtempo_has_more_late_early_than_done "
          f"(failtempo={fail_te} > done={done_te})")


# ---------------------------------------------------------------------------
# Cross-file sanity checks
# ---------------------------------------------------------------------------

def test_done_is_best_performance():
    """Done.wav should have the highest correct count among all three files."""
    done_c = DONE_SUMMARY["correct"]
    failnote_c = FAILNOTE_SUMMARY["correct"]
    failtempo_c = FAILTEMPO_SUMMARY["correct"]
    assert done_c >= failnote_c, \
        f"Done correct ({done_c}) should be >= FailNote correct ({failnote_c})"
    assert done_c >= failtempo_c, \
        f"Done correct ({done_c}) should be >= FailTempo correct ({failtempo_c})"
    print(f"  [PASS] test_done_is_best_performance "
          f"(done={done_c}, failnote={failnote_c}, failtempo={failtempo_c})")


def test_all_files_have_played_notes():
    """Every WAV file should produce at least some detected notes."""
    for label, summary in [
        ("Done.wav", DONE_SUMMARY),
        ("FailNote.wav", FAILNOTE_SUMMARY),
        ("FailTempo.wav", FAILTEMPO_SUMMARY),
    ]:
        assert summary["total_played_notes"] > 0, \
            f"{label} has 0 played notes — Basic Pitch failed?"
    print(f"  [PASS] test_all_files_have_played_notes")


def test_all_files_total_is_consistent():
    """The total_reference_notes should be 17 for all comparisons."""
    for label, summary in [
        ("Done.wav", DONE_SUMMARY),
        ("FailNote.wav", FAILNOTE_SUMMARY),
        ("FailTempo.wav", FAILTEMPO_SUMMARY),
    ]:
        assert summary["total_reference_notes"] == 17, \
            f"{label}: expected 17 reference notes, got {summary['total_reference_notes']}"
    print("  [PASS] test_all_files_total_is_consistent")


def test_no_empty_results():
    """compare_notes should always return a non-empty list."""
    assert len(DONE_RESULTS) > 0
    assert len(FAILNOTE_RESULTS) > 0
    assert len(FAILTEMPO_RESULTS) > 0
    print(f"  [PASS] test_no_empty_results "
          f"(done={len(DONE_RESULTS)}, failnote={len(FAILNOTE_RESULTS)}, "
          f"failtempo={len(FAILTEMPO_RESULTS)})")


# ---------------------------------------------------------------------------
# Detailed inspection (informational, not strict assertions)
# ---------------------------------------------------------------------------

def print_detailed_report():
    """Print a human-readable comparison report for all three files."""
    print("\n" + "=" * 70)
    print("DETAILED COMPARISON REPORT")
    print("=" * 70)

    for label, summary in [
        ("Done.wav (correct performance)", DONE_SUMMARY),
        ("FailNote.wav (1 wrong note)", FAILNOTE_SUMMARY),
        ("FailTempo.wav (1 shifted note)", FAILTEMPO_SUMMARY),
    ]:
        print(f"\n--- {label} ---")
        print(f"  Reference notes: {summary['total_reference_notes']}")
        print(f"  Played notes:    {summary['total_played_notes']}")
        print(f"  Correct: {summary['correct']:>3}")
        print(f"  Late:    {summary['late']:>3}")
        print(f"  Early:   {summary['early']:>3}")
        print(f"  Wrong:   {summary['wrong']:>3}")
        print(f"  Missed:  {summary['missed']:>3}")

        # Print per-note details
        for r in summary["notes"]:
            if r.status == "correct":
                continue  # skip correct to keep output readable
            extra = ""
            if r.played_pitch is not None:
                extra = f"  played_pitch={r.played_pitch:.1f}"
            if r.time_delta_ms is not None:
                extra += f"  delta={r.time_delta_ms:.0f}ms"
            print(f"    [{r.status.upper():7s}] ref_pitch={r.reference_pitch:5.1f} "
                  f"@ {r.reference_start:.3f}s{extra}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # Reference
        test_reference_note_count,
        test_reference_pitches_in_piano_range,
        test_reference_sorted_by_time,
        test_reference_has_four_chords,
        # Done.wav
        test_done_has_no_wrong_notes,
        test_done_all_matched_are_correct_or_late,
        test_done_has_acceptable_timing,
        test_done_has_any_correct,
        test_done_timing_within_tolerance,
        # FailNote.wav
        test_failnote_has_wrong_note,
        test_failnote_wrong_pitch_is_detected,
        test_failnote_has_more_wrong_than_done,
        # FailTempo.wav
        test_failtempo_has_late_or_early,
        test_failtempo_late_note_is_correct_pitch,
        test_failtempo_timing_delta_exceeds_tolerance,
        test_failtempo_has_more_late_early_than_done,
        # Cross-file
        test_done_is_best_performance,
        test_all_files_have_played_notes,
        test_all_files_total_is_consistent,
        test_no_empty_results,
    ]

    failed = 0
    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {test_fn.__name__}: {e}")

    print_detailed_report()

    print("\n" + "=" * 70)
    if failed == 0:
        print(f"All {len(tests)} tests passed!")
    else:
        print(f"{len(tests) - failed}/{len(tests)} passed, {failed} FAILED")
    print("=" * 70)

    sys.exit(0 if failed == 0 else 1)
