"""Audio-to-notes transcription using Spotify's Basic Pitch.

Basic Pitch 0.4.0 returns:
    predict() -> (model_output, midi_data, note_events)
    note_events: list of (start_time, end_time, pitch_midi, amplitude, pitch_bend)
    All timing values are in seconds.
"""

from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

from config import MIDI_NOTE_MIN, MIDI_NOTE_MAX
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
    )

    notes: list[NoteEvent] = []

    # In Basic Pitch 0.4.0, note_events is a list of tuples:
    # (start_time_sec, end_time_sec, pitch_midi, amplitude, pitch_bend)
    for start, end, pitch, amplitude, _bend in note_events:
        pitch = float(pitch)
        if MIDI_NOTE_MIN <= pitch <= MIDI_NOTE_MAX:
            notes.append(NoteEvent(
                pitch=pitch,
                start_time=float(start),
                end_time=float(end),
            ))

    # Sort by start_time for consistent comparison
    notes.sort(key=lambda n: n.start_time)
    return notes
