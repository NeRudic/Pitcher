"""Note comparison engine.

Compares played notes (from audio) against reference notes (from MIDI)
using tolerance thresholds for pitch and timing.

Algorithm:
    1. For each reference note, try to find a matching played note.
    2. Match criteria:
       - Pitch within ±PITCH_TOLERANCE_SEMITONES
       - Timing within ±TIMING_TOLERANCE_MS
    3. A reference note with a match is classified as:
       - "correct" if timing delta ≤ TIMING_TOLERANCE_MS
       - "late" if played note start > reference start + tolerance
       - "early" if played note start < reference start - tolerance
    4. An unmatched reference note is "missed".
    5. Unmatched played notes (above amplitude threshold) are "wrong".
"""


from config import PITCH_TOLERANCE_SEMITONES, TIMING_TOLERANCE_MS
from models import NoteComparisonResult, NoteEvent


def compare_notes(
    reference: list[NoteEvent],
    played: list[NoteEvent],
) -> list[NoteComparisonResult]:
    """Compare played notes against reference notes.

    Uses a greedy matching algorithm: for each reference note, finds the
    closest played note within tolerance that hasn't been matched yet.

    Args:
        reference: Reference notes from MIDI.
        played: Played notes from audio transcription.

    Returns:
        List of NoteComparisonResult objects describing the comparison.
    """
    timing_tolerance_sec = TIMING_TOLERANCE_MS / 1000.0
    used_played: set[int] = set()  # indices of matched played notes
    results: list[NoteComparisonResult] = []

    for ref in reference:
        best_match_idx: int | None = None
        best_time_delta: float = float("inf")

        for i, pl in enumerate(played):
            if i in used_played:
                continue

            # Check pitch match
            pitch_diff = abs(pl.pitch - ref.pitch)
            if pitch_diff > PITCH_TOLERANCE_SEMITONES:
                continue

            # Check timing — how far is the played note from the reference?
            time_delta = pl.start_time - ref.start_time

            if abs(time_delta) < abs(best_time_delta):
                best_time_delta = time_delta
                best_match_idx = i

        if best_match_idx is not None:
            used_played.add(best_match_idx)
            matched = played[best_match_idx]
            time_delta_ms = best_time_delta * 1000

            # Classify based on timing
            if abs(time_delta_ms) <= TIMING_TOLERANCE_MS:
                status = "correct"
            elif time_delta_ms > 0:
                status = "late"
            else:
                status = "early"

            results.append(NoteComparisonResult(
                reference_pitch=ref.pitch,
                reference_start=ref.start_time,
                reference_end=ref.end_time,
                status=status,
                played_pitch=matched.pitch,
                played_start=matched.start_time,
                time_delta_ms=time_delta_ms,
            ))
        else:
            # No matching played note found — missed
            results.append(NoteComparisonResult(
                reference_pitch=ref.pitch,
                reference_start=ref.start_time,
                reference_end=ref.end_time,
                status="missed",
            ))

    # Add wrong notes — played notes above amplitude threshold that
    # didn't match any reference (real wrong notes, not artifacts).
    for i, pl in enumerate(played):
        if i not in used_played:
            results.append(NoteComparisonResult(
                reference_pitch=-1,  # no reference
                reference_start=-1,
                reference_end=-1,
                status="wrong",
                played_pitch=pl.pitch,
                played_start=pl.start_time,
                time_delta_ms=None,
            ))

    return results


def build_comparison_summary(
    reference: list[NoteEvent],
    played: list[NoteEvent],
    note_results: list[NoteComparisonResult],
) -> dict:
    """Build a summary dictionary of the comparison results.

    Args:
        reference: Reference notes from MIDI.
        played: Played notes from audio.
        note_results: Results from compare_notes().

    Returns:
        Dictionary with counts and the full notes list.
    """
    counts = {
        "correct": 0,
        "wrong": 0,
        "late": 0,
        "early": 0,
        "missed": 0,
    }
    for r in note_results:
        counts[r.status] = counts.get(r.status, 0) + 1

    # Count matched + wrong played notes (artifacts already filtered by amplitude)
    matched_played = counts["correct"] + counts["late"] + counts["early"] + counts["wrong"]

    return {
        "total_reference_notes": len(reference),
        "total_played_notes": matched_played,
        **counts,
        "notes": note_results,
        "played_notes": played,
    }
