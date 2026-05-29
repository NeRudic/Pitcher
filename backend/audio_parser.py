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
        onset_threshold=0.6,       # default 0.5 — higher = fewer false onsets
        frame_threshold=0.4,       # default 0.3 — higher = less note fragmentation
        minimum_note_length=150,   # default ~128ms — discard shorter spurious notes
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
            ))

    # Deduplicate — merge fragmented notes before comparison
    notes = _deduplicate_notes(notes)

    # Sort by start_time for consistent comparison
    notes.sort(key=lambda n: n.start_time)
    return notes


# Pitch and timing tolerances for deduplication (separate from comparison tolerances)
_DEDUP_PITCH_TOLERANCE = 1.0   # ±1 semitone — fragments of the same note won't drift far
_DEDUP_GAP_MS = 50             # max gap between fragments to merge (in milliseconds)


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

            if pitch_diff <= _DEDUP_PITCH_TOLERANCE and time_gap <= gap_sec:
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
