"""Unit tests for the note comparison logic."""

from models import NoteEvent
from comparator import compare_notes, build_comparison_summary


def test_exact_match():
    """Notes that match perfectly in pitch and timing should be 'correct'."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),
    ]
    played = [
        NoteEvent(pitch=60, start_time=1.02, end_time=1.98),
    ]
    results = compare_notes(reference, played)
    assert len(results) == 1
    assert results[0].status == "correct", f"Expected correct, got {results[0].status}"
    print("[PASS] test_exact_match")


def test_missed_note():
    """A reference note with no matching played note should be 'missed'."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),
    ]
    played = []  # nothing played
    results = compare_notes(reference, played)
    assert len(results) == 1
    assert results[0].status == "missed", f"Expected missed, got {results[0].status}"
    print("[PASS] test_missed_note passed")


def test_late_note():
    """A note played >100ms after reference should be 'late'."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),
    ]
    played = [
        NoteEvent(pitch=60, start_time=1.5, end_time=2.5),  # 500ms late
    ]
    results = compare_notes(reference, played)
    assert len(results) == 1
    assert results[0].status == "late", f"Expected late, got {results[0].status}"
    assert results[0].time_delta_ms == 500
    print("[PASS] test_late_note passed")


def test_early_note():
    """A note played >100ms before reference should be 'early'."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),
    ]
    played = [
        NoteEvent(pitch=60, start_time=0.5, end_time=1.5),  # 500ms early
    ]
    results = compare_notes(reference, played)
    assert len(results) == 1
    assert results[0].status == "early", f"Expected early, got {results[0].status}"
    assert results[0].time_delta_ms == -500
    print("[PASS] test_early_note passed")


def test_pitch_tolerance():
    """A note within ±1 semitone should still match."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),  # C4
    ]
    played = [
        NoteEvent(pitch=61, start_time=1.02, end_time=1.98),  # C#4 — 1 semitone off
    ]
    results = compare_notes(reference, played)
    assert len(results) == 1
    assert results[0].status == "correct", f"Expected correct, got {results[0].status}"
    assert results[0].played_pitch == 61
    print("[PASS] test_pitch_tolerance passed")


def test_pitch_out_of_tolerance():
    """A note >1 semitone off should not match."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),  # C4
    ]
    played = [
        NoteEvent(pitch=62, start_time=1.02, end_time=1.98),  # D4 — 2 semitones off
    ]
    results = compare_notes(reference, played)
    # Played note is ignored (no matching reference — likely artifact)
    # Only the unmatched reference note is reported
    assert len(results) == 1
    assert results[0].status == "missed"
    print("[PASS] test_pitch_out_of_tolerance passed")


def test_multiple_notes():
    """Complex scenario with multiple notes and mixed results."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),   # C4 — should be correct
        NoteEvent(pitch=62, start_time=2.0, end_time=3.0, velocity=80),   # D4 — should be missed
        NoteEvent(pitch=64, start_time=3.0, end_time=4.0, velocity=80),   # E4 — should be late
    ]
    played = [
        NoteEvent(pitch=60, start_time=1.05, end_time=1.95),   # correct (5ms off)
        NoteEvent(pitch=64, start_time=3.4, end_time=4.4),     # late (400ms)
    ]
    results = compare_notes(reference, played)
    assert len(results) == 3  # correct, missed, late

    statuses = {r.status for r in results}
    assert "correct" in statuses
    assert "missed" in statuses   # D4 (ref pitch 62) not played
    assert "late" in statuses     # E4 played at 3.4 instead of 3.0

    # Check specific notes
    correct = [r for r in results if r.reference_pitch == 60]
    assert len(correct) == 1 and correct[0].status == "correct"

    missed = [r for r in results if r.reference_pitch == 62]
    assert len(missed) == 1 and missed[0].status == "missed"

    late = [r for r in results if r.reference_pitch == 64]
    assert len(late) == 1 and late[0].status == "late"

    print("[PASS] test_multiple_notes passed")


def test_summary_counts():
    """Verify the summary builder produces correct counts."""
    reference = [
        NoteEvent(pitch=60, start_time=1.0, end_time=2.0, velocity=80),
        NoteEvent(pitch=62, start_time=2.0, end_time=3.0, velocity=80),
    ]
    played = [
        NoteEvent(pitch=60, start_time=1.02, end_time=1.98),
    ]
    results = compare_notes(reference, played)
    summary = build_comparison_summary(reference, played, results)

    assert summary["total_reference_notes"] == 2
    assert summary["total_played_notes"] == 1
    assert summary["correct"] == 1
    assert summary["missed"] == 1
    assert summary["wrong"] == 0
    print("[PASS] test_summary_counts passed")


if __name__ == "__main__":
    test_exact_match()
    test_missed_note()
    test_late_note()
    test_early_note()
    test_pitch_tolerance()
    test_pitch_out_of_tolerance()
    test_multiple_notes()
    test_summary_counts()
    print("\nAll tests passed!")
