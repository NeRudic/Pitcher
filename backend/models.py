"""Pydantic models for the API."""

from pydantic import BaseModel


class NoteEvent(BaseModel):
    """A single note event extracted from MIDI or audio."""
    pitch: float        # MIDI note number (may be fractional for audio)
    start_time: float   # note start in seconds
    end_time: float     # note end in seconds
    velocity: int | None = None  # MIDI velocity (0–127), None for audio
    amplitude: float | None = None  # Basic Pitch confidence (0–1), None for MIDI


class NoteComparisonResult(BaseModel):
    """Result of comparing a single reference note to the performance."""
    reference_pitch: float
    reference_start: float
    reference_end: float
    status: str                     # "correct", "wrong", "late", "early", "missed"
    played_pitch: float | None = None
    played_start: float | None = None
    time_delta_ms: float | None = None  # difference from reference in ms


class ComparisonResponse(BaseModel):
    """Full comparison response returned by the API."""
    total_reference_notes: int
    total_played_notes: int
    correct: int
    wrong: int
    late: int
    early: int
    missed: int
    notes: list[NoteComparisonResult]
    played_notes: list[NoteEvent] = []  # raw played notes for playback mode


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
