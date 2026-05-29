"""Pydantic models for the API."""

from pydantic import BaseModel


class NoteEvent(BaseModel):
    """A single note event extracted from MIDI or audio."""
    pitch: int          # MIDI note number (0–127)
    start_time: float   # note start in seconds
    end_time: float     # note end in seconds (may be None for audio)
    velocity: int | None = None  # MIDI velocity (0–127), None for audio


class NoteComparisonResult(BaseModel):
    """Result of comparing a single reference note to the performance."""
    reference_pitch: int
    reference_start: float
    reference_end: float
    status: str                     # "correct", "wrong", "late", "early", "missed"
    played_pitch: int | None = None
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


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
