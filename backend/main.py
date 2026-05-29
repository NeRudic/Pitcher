"""Piano Performance Analyzer — FastAPI Backend.

Endpoints:
    GET  /health              — Health check
    POST /compare             — Upload audio + MIDI, get comparison results
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ComparisonResponse, NoteComparisonResult
from midi_parser import parse_midi
from audio_parser import parse_audio
from comparator import compare_notes, build_comparison_summary
from config import (
    MAX_AUDIO_SIZE_MB,
    MAX_MIDI_SIZE_MB,
    ALLOWED_AUDIO_TYPES,
    ALLOWED_MIDI_TYPES,
)

app = FastAPI(
    title="Piano Performance Analyzer",
    description="Compare a recorded piano performance against a reference MIDI file.",
    version="1.0.0",
)

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "piano-analyzer"}


@app.post("/compare", response_model=ComparisonResponse)
async def compare_recordings(
    audio: UploadFile = File(...),
    midi: UploadFile = File(...),
) -> ComparisonResponse:
    """Upload an audio recording and a reference MIDI file for comparison.

    Returns a detailed note-by-note comparison with statuses:
        correct, wrong, late, early, missed.
    """
    # -- Validate audio file ------------------------------------------------
    if audio.content_type and audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {audio.content_type}. "
                   f"Allowed: {', '.join(ALLOWED_AUDIO_TYPES)}",
        )

    # -- Validate MIDI file -------------------------------------------------
    if midi.content_type and midi.content_type not in ALLOWED_MIDI_TYPES:
        # Known but unsupported content type — reject unless extension is MIDI.
        midi_ext = _get_suffix(midi.filename, "")
        if midi_ext not in (".mid", ".midi"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported MIDI type: {midi.content_type}. "
                       f"Allowed: {', '.join(ALLOWED_MIDI_TYPES)}",
            )
    elif not midi.content_type:
        # Browsers often omit Content-Type for MIDI files — fall back to
        # extension check so that non-MIDI files don't slip through.
        midi_ext = _get_suffix(midi.filename, "")
        if midi_ext not in (".mid", ".midi"):
            raise HTTPException(
                status_code=400,
                detail=f"Unknown file type. Please upload a .mid or .midi file.",
            )

    # -- Save uploaded files to temp directory ------------------------------
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        # Determine file extensions
        audio_suffix = _get_suffix(audio.filename, ".wav")
        midi_suffix = _get_suffix(midi.filename, ".mid")

        audio_path = os.path.join(tmpdir, f"recording{audio_suffix}")
        midi_path = os.path.join(tmpdir, f"reference{midi_suffix}")

        # Write audio file
        audio_content = await audio.read()
        if len(audio_content) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Max {MAX_AUDIO_SIZE_MB} MB.",
            )
        with open(audio_path, "wb") as f:
            f.write(audio_content)

        # Write MIDI file
        midi_content = await midi.read()
        if len(midi_content) > MAX_MIDI_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"MIDI file too large. Max {MAX_MIDI_SIZE_MB} MB.",
            )
        with open(midi_path, "wb") as f:
            f.write(midi_content)

        # -- Parse files ----------------------------------------------------
        try:
            reference_notes = parse_midi(midi_path)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse MIDI file: {e}",
            )

        try:
            played_notes = parse_audio(audio_path)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to transcribe audio: {e}",
            )

        # -- Compare notes --------------------------------------------------
        note_results = compare_notes(reference_notes, played_notes)
        summary = build_comparison_summary(
            reference_notes, played_notes, note_results
        )

    return ComparisonResponse(**summary)


def _get_suffix(filename: str | None, default: str) -> str:
    """Extract file extension or return a default."""
    if filename and "." in filename:
        ext = Path(filename).suffix
        if ext:
            return ext.lower()
    return default
