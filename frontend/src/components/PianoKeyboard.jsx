import { useMemo } from 'react';

/**
 * Piano keyboard visualization with note highlighting.
 *
 * Displays a standard 88-key piano (A0–C8, MIDI 21–108).
 * Each key is color-coded based on the comparison result status.
 */

// Status → color mapping
const STATUS_COLORS = {
  correct: '#4caf50',   // green
  wrong:   '#f44336',   // red
  late:    '#ff9800',   // orange
  early:   '#ffc107',   // amber
  missed:  '#9e9e9e',   // gray
};

// White key note numbers within one octave (C through B)
const WHITE_KEYS_IN_OCTAVE = [0, 2, 4, 5, 7, 9, 11];

// Black key note numbers within one octave
const BLACK_KEYS_IN_OCTAVE = [1, 3, 6, 8, 10];

// Note names for labels
const NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

function isWhiteKey(midiNote) {
  return WHITE_KEYS_IN_OCTAVE.includes(midiNote % 12);
}

function noteName(midiNote) {
  const octave = Math.floor(midiNote / 12) - 1;
  const name = NOTE_NAMES[midiNote % 12];
  return `${name}${octave}`;
}

export default function PianoKeyboard({ noteResults = [], highlightMap = null }) {
  // Build a map from MIDI pitch → status for quick lookup
  const statusMap = useMemo(() => {
    if (highlightMap) return highlightMap;
    const map = {};
    for (const r of noteResults) {
      const pitch = r.reference_pitch;
      // Only overwrite with "worse" status (preserve wrong over correct, etc.)
      // Priority: wrong > missed > late > early > correct
      const priority = { wrong: 5, missed: 4, late: 3, early: 2, correct: 1 };
      if (!map[pitch] || priority[r.status] > priority[map[pitch]]) {
        map[pitch] = r.status;
      }
    }
    return map;
  }, [noteResults, highlightMap]);

  // Build the keyboard layout
  const keys = useMemo(() => {
    const result = [];
    const MIDI_MIN = 21;  // A0
    const MIDI_MAX = 108; // C8

    let whiteKeyIndex = 0;

    for (let midi = MIDI_MIN; midi <= MIDI_MAX; midi++) {
      const white = isWhiteKey(midi);
      result.push({
        midi,
        white,
        noteLabel: noteName(midi),
        whiteKeyIndex: white ? whiteKeyIndex : -1,
        status: statusMap[midi] || null,
      });
      if (white) whiteKeyIndex++;
    }

    return result;
  }, [statusMap]);

  const whiteKeys = keys.filter((k) => k.white);
  const blackKeys = keys.filter((k) => !k.white);
  const totalWhiteKeys = whiteKeys.length;

  return (
    <div className="piano-container">
      <div className="piano-keyboard">
        {/* White keys */}
        {whiteKeys.map((key, i) => (
          <div
            key={key.midi}
            className={`piano-key white-key ${key.status ? 'highlighted' : ''}`}
            style={{
              width: `${100 / totalWhiteKeys}%`,
              left: `${(100 / totalWhiteKeys) * i}%`,
              backgroundColor: key.status
                ? STATUS_COLORS[key.status]
                : '#ffffff',
              borderColor: key.status ? 'rgba(0,0,0,0.3)' : '#333',
            }}
            title={`${key.noteLabel}${key.status ? ` — ${key.status}` : ''}`}
          >
            <span className="key-label">{key.noteLabel}</span>
          </div>
        ))}

        {/* Black keys */}
        {blackKeys.map((key) => {
          // Position black key between the two white keys it sits between
          // Find the index of the white key to the left
          const leftWhiteIdx = whiteKeys.findIndex(
            (wk) => wk.midi === key.midi - 1
          );
          // If no white key to the left, find the one to the right
          const idx = leftWhiteIdx >= 0 ? leftWhiteIdx : whiteKeys.findIndex(
            (wk) => wk.midi === key.midi + 1
          ) - 1;

          return (
            <div
              key={key.midi}
              className={`piano-key black-key ${key.status ? 'highlighted' : ''}`}
              style={{
                width: `${(100 / totalWhiteKeys) * 0.65}%`,
                left: `${(100 / totalWhiteKeys) * (idx + 0.675)}%`,
                backgroundColor: key.status
                  ? STATUS_COLORS[key.status]
                  : '#1a1a1a',
                borderColor: key.status ? 'rgba(255,255,255,0.3)' : '#000',
              }}
              title={`${key.noteLabel}${key.status ? ` — ${key.status}` : ''}`}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="legend">
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <div key={status} className="legend-item">
            <span
              className="legend-color"
              style={{ backgroundColor: color }}
            />
            <span className="legend-label">{status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
