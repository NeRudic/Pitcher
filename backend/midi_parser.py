"""MIDI file parsing using PrettyMIDI.

Converts MIDI ticks to seconds using the formula:
    time_seconds = ticks / PPQ / BPM * 60
"""

import pretty_midi

from config import MIDI_NOTE_MIN, MIDI_NOTE_MAX
from models import NoteEvent


def parse_midi(file_path: str) -> list[NoteEvent]:
    """Parse a MIDI file and extract note events with timing in seconds.

    Args:
        file_path: Path to the .mid file.

    Returns:
        List of NoteEvent objects with pitch, start_time, end_time, velocity.
        Notes outside the standard 88-key piano range are filtered out.
    """
    midi_data = pretty_midi.PrettyMIDI(file_path)
    notes: list[NoteEvent] = []

    for instrument in midi_data.instruments:
        for note in instrument.notes:
            # Filter to standard piano range
            if MIDI_NOTE_MIN <= note.pitch <= MIDI_NOTE_MAX:
                notes.append(NoteEvent(
                    pitch=note.pitch,
                    start_time=note.start,
                    end_time=note.end,
                    velocity=note.velocity,
                ))

    # Sort by start_time for consistent comparison
    notes.sort(key=lambda n: n.start_time)
    return notes
