"""Configuration constants for the Piano Performance Analyzer."""

# Tolerance thresholds for note comparison
PITCH_TOLERANCE_SEMITONES = 0.5  # quarter-tone tolerance (for fretless instruments)
TIMING_TOLERANCE_MS = 100      # ±100 milliseconds

# File constraints
MAX_AUDIO_SIZE_MB = 50
MAX_MIDI_SIZE_MB = 10
ALLOWED_AUDIO_TYPES = ["audio/wav", "audio/mpeg", "audio/x-wav", "audio/wave"]
ALLOWED_MIDI_TYPES = ["audio/midi", "audio/mid", "audio/x-midi", "application/x-midi"]

# Basic Pitch artifact filter — notes below this amplitude are treated as
# false-positive detections and dropped before comparison.
MIN_AMPLITUDE = 0.25  # raised from 0.1 — closer to Basic Pitch's frame_threshold (0.3)
# to filter out harmonic over-detections and low-confidence artifacts

# Piano note range (standard 88-key piano)
MIDI_NOTE_MIN = 21  # A0
MIDI_NOTE_MAX = 108  # C8
