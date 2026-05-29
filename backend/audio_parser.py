"""Audio-to-notes transcription using Spotify's Basic Pitch.

Basic Pitch 0.4.0 returns:
    predict() -> (model_output, midi_data, note_events)
    note_events: list of (start_time, end_time, pitch_midi, amplitude, pitch_bend)
    All timing values are in seconds.
"""

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

from config import MIDI_NOTE_MIN, MIDI_NOTE_MAX, MIN_AMPLITUDE
from models import NoteEvent


def parse_audio(file_path: str) -> list[NoteEvent]:
    """Transcribe an audio file to note events using Basic Pitch.

    Args:
        file_path: Path to the audio file (.wav, .mp3, etc.).

    Returns:
        List of NoteEvent objects with pitch, start_time, end_time.
    """
    _model_output, _midi_data, note_events = predict(
        file_path,
        ICASSP_2022_MODEL_PATH,
        onset_threshold=0.4,       # default 0.5 — lowered to catch more polyphonic notes
        frame_threshold=0.3,       # default 0.3 — back to default for fuller detection
        minimum_note_length=80,    # default ~128ms — lowered to keep short chord notes
        melodia_trick=False,       # default True — can add harmonic/resonance artifacts
    )

    notes: list[NoteEvent] = []

    # In Basic Pitch 0.4.0, note_events is a list of tuples:
    # (start_time_sec, end_time_sec, pitch_midi, amplitude, pitch_bend)
    for start, end, pitch, amplitude, _bend in note_events:
        # Skip low-amplitude detections — likely artifacts / noise
        if float(amplitude) < MIN_AMPLITUDE:
            continue
        pitch = float(pitch)
        if MIDI_NOTE_MIN <= pitch <= MIDI_NOTE_MAX:
            notes.append(NoteEvent(
                pitch=pitch,
                start_time=float(start),
                end_time=float(end),
                amplitude=float(amplitude),  # needed for harmonic filtering
            ))

    # Filter out harmonic over-detections — notes that are likely
    # overtones of louder overlapping notes (octaves, fifths, etc.)
    notes = _filter_harmonics(notes)

    # Deduplicate — merge fragmented notes before comparison
    notes = _deduplicate_notes(notes)

    # Sort by start_time for consistent comparison
    notes.sort(key=lambda n: n.start_time)
    return notes


# Pitch and timing tolerances for deduplication (separate from comparison tolerances)
_DEDUP_PITCH_TOLERANCE = 1.0   # ±1 semitone — fragments of the same note won't drift far
_DEDUP_GAP_MS = 50             # max gap between fragments to merge (in milliseconds)
_DEDUP_MAX_DURATION_MS = 2000  # refuse to merge if result exceeds 2s — prevents cross-chord merging


# Harmonic intervals that Basic Pitch commonly misdetects as separate notes.
# When a note's pitch is exactly one of these intervals above a louder
# overlapping note, it's almost certainly an overtone artifact.
_HARMONIC_INTERVALS = [12, 19, 24]  # octave, octave+fifth, 2 octaves — true overtone intervals
# Removed 7 (fifth) and 5 (fourth) — those are normal chord intervals, not overtones
_HARMONIC_TOLERANCE = 0.5  # ±quarter-tone tolerance for harmonic match


def _filter_harmonics(notes: list[NoteEvent]) -> list[NoteEvent]:
    """Remove notes that are likely harmonic overtones of louder notes.

    Basic Pitch sometimes detects harmonics (octaves, etc.) as independent
    notes, especially for piano audio with rich harmonic content.  Since
    fundamentals are almost always louder than their harmonics, we process
    notes from loudest to quietest and remove any note that falls on a
    harmonic interval of an already-kept, overlapping note.

    Real-note safeguard: before removing a candidate overtone, we check
    whether the candidate itself has higher notes (12, 19, or 24 semitones
    above it) in the pre-filtered note list.  If it does, it is a real
    fundamental in the chord, not an overtone artifact — keep it.

    Args:
        notes: List of NoteEvent objects with amplitude populated
               (after amplitude + range filters, before dedup).

    Returns:
        Filtered list with harmonic artifacts removed.
    """
    if len(notes) <= 1:
        return notes

    # Keep a reference to the full pre-filter list for the real-note check
    raw_notes = notes

    # Process loudest first — fundamentals dominate harmonics in amplitude
    sorted_notes = sorted(notes, key=lambda n: n.amplitude or 0, reverse=True)

    kept: list[NoteEvent] = []
    for note in sorted_notes:
        is_harmonic = False
        for k in kept:
            # Must overlap in time — harmonics can't exist without the fundamental
            if note.end_time <= k.start_time or note.start_time >= k.end_time:
                continue

            pitch_diff = abs(note.pitch - k.pitch)
            for interval in _HARMONIC_INTERVALS:
                if abs(pitch_diff - interval) <= _HARMONIC_TOLERANCE:
                    # Candidate overtone.  Check whether THIS note has higher
                    # harmonics above it in the raw list — a real fundamental
                    # should have overtones of its own.
                    has_upper_harmonics = False
                    for raw_n in raw_notes:
                        if raw_n is note:
                            continue
                        if raw_n.end_time <= note.start_time or raw_n.start_time >= note.end_time:
                            continue
                        raw_diff = raw_n.pitch - note.pitch
                        for up_interval in _HARMONIC_INTERVALS:
                            if abs(raw_diff - up_interval) <= _HARMONIC_TOLERANCE:
                                has_upper_harmonics = True
                                break
                        if has_upper_harmonics:
                            break

                    if has_upper_harmonics:
                        # Real note — has its own harmonics, keep it
                        continue

                    is_harmonic = True
                    break
            if is_harmonic:
                break

        if not is_harmonic:
            kept.append(note)

    return kept


def _deduplicate_notes(notes: list[NoteEvent]) -> list[NoteEvent]:
    """Merge note fragments that likely belong to the same played note.

    Basic Pitch sometimes splits a single sustained note into multiple
    shorter notes due to amplitude fluctuations during the sustain phase.
    This function merges notes that have nearly the same pitch and
    overlapping or adjacent time intervals.

    Args:
        notes: List of NoteEvent objects (unsorted).

    Returns:
        Deduplicated list of NoteEvent objects.
    """
    if len(notes) <= 1:
        return notes

    gap_sec = _DEDUP_GAP_MS / 1000.0
    max_dur_sec = _DEDUP_MAX_DURATION_MS / 1000.0

    # Group notes by integer MIDI pitch (round to nearest int)
    groups: dict[int, list[NoteEvent]] = {}
    for n in notes:
        midi_bucket = round(n.pitch)
        groups.setdefault(midi_bucket, []).append(n)

    merged: list[NoteEvent] = []

    for _bucket, group in groups.items():
        # Sort within group by start_time
        group.sort(key=lambda n: n.start_time)

        current = group[0]
        for next_note in group[1:]:
            # Check if notes are close enough in pitch and time to merge
            pitch_diff = abs(next_note.pitch - current.pitch)
            time_gap = next_note.start_time - current.end_time
            # Don't merge if the result would exceed max duration —
            # prevents merging fragments across chord boundaries
            would_be_duration = max(current.end_time, next_note.end_time) - current.start_time

            if (pitch_diff <= _DEDUP_PITCH_TOLERANCE
                    and time_gap <= gap_sec
                    and would_be_duration <= max_dur_sec):
                # Merge: extend current to cover both notes.
                # Decide which pitch to keep BEFORE modifying end_time.
                dur_current = current.end_time - current.start_time
                dur_next = next_note.end_time - next_note.start_time
                current.end_time = max(current.end_time, next_note.end_time)
                # Keep the pitch of the longer fragment
                if dur_next > dur_current:
                    current.pitch = next_note.pitch
                # start_time stays as the earlier one (current.start_time is earlier
                # because the group is sorted by start_time)
            else:
                # Can't merge — save current and move on
                merged.append(current)
                current = next_note

        merged.append(current)

    return merged
