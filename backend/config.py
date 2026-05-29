"""Configuration constants for the Piano Performance Analyzer."""

# Tolerance thresholds for note comparison
PITCH_TOLERANCE_SEMITONES = 1  # ±1 semitone
TIMING_TOLERANCE_MS = 100      # ±100 milliseconds

# File constraints
MAX_AUDIO_SIZE_MB = 50
MAX_MIDI_SIZE_MB = 10
ALLOWED_AUDIO_TYPES = ["audio/wav", "audio/mpeg", "audio/x-wav", "audio/wave"]
ALLOWED_MIDI_TYPES = ["audio/midi", "audio/mid", "audio/x-midi", "application/x-midi"]

# Piano note range (standard 88-key piano)
MIDI_NOTE_MIN = 21  # A0
MIDI_NOTE_MAX = 108  # C8
