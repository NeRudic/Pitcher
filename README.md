# 🎹 Piano Performance Analyzer

Compare your recorded piano performance against a reference MIDI file.
Highlights missed, wrong, late, and early notes on a virtual piano keyboard.

## Features

- Upload audio recording (.wav/.mp3) + reference MIDI (.mid)
- Automatic note extraction and comparison
- Visual keyboard highlighting: correct / wrong / late / early / missed
- Tolerance: ±1 semitone pitch, ±100ms timing

## Tech Stack

| Layer    | Technology                       |
|----------|----------------------------------|
| Backend  | FastAPI + PrettyMIDI + Basic Pitch (Spotify) |
| Frontend | React 19 + Vite + Web Audio API  |

## Requirements

- **Python 3.11** (required by Basic Pitch / TensorFlow)
- **Node.js 20+** (for frontend)

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### 3. Usage

1. Open the web app
2. Upload your audio recording (.wav or .mp3)
3. Upload the reference MIDI file (.mid)
4. Click "Compare"
5. See the piano keyboard highlight your performance

## API

### `GET /health`

Health check. Returns `{"status": "ok", "service": "piano-analyzer"}`.

### `POST /compare`

Upload audio and MIDI files for comparison.

**Request:** `multipart/form-data`
- `audio` — audio recording (.wav, .mp3)
- `midi` — reference MIDI file (.mid)

**Response:** JSON with comparison results:
```json
{
  "total_reference_notes": 50,
  "total_played_notes": 48,
  "correct": 40,
  "wrong": 3,
  "late": 5,
  "early": 2,
  "missed": 0,
  "notes": [
    {
      "reference_pitch": 60,
      "reference_start": 1.0,
      "reference_end": 2.0,
      "status": "correct",
      "played_pitch": 60,
      "played_start": 1.02,
      "time_delta_ms": 20
    }
  ]
}
```

### Status Values

| Status    | Meaning                                |
|-----------|----------------------------------------|
| `correct` | Played within pitch and timing tolerance |
| `wrong`   | Played note has no matching reference  |
| `late`    | Played >100ms after reference          |
| `early`   | Played >100ms before reference         |
| `missed`  | Reference note was not played          |

## Project Structure

```
Pitcher/
├── SPEC.md                 # Technical specification
├── README.md               # This file
├── backend/
│   ├── requirements.txt    # Python dependencies
│   ├── main.py             # FastAPI application
│   ├── models.py           # Pydantic data models
│   ├── config.py           # Tolerance thresholds & constants
│   ├── midi_parser.py      # MIDI → notes (PrettyMIDI)
│   ├── audio_parser.py     # Audio → notes (Basic Pitch)
│   ├── comparator.py       # Note comparison engine
│   ├── test_comparator.py  # Unit tests for comparator
│   └── test_api.py         # Integration tests for API
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx        # React entry point
        ├── App.jsx          # Main application
        ├── App.css          # Styles
        ├── api/client.js    # API client
        └── components/
            ├── FileUpload.jsx       # File upload form
            ├── PianoKeyboard.jsx    # Piano keyboard visualization
            └── ResultsPanel.jsx     # Results summary
```

## Running Tests

```bash
cd backend

# Unit tests (comparison logic)
python test_comparator.py

# Integration tests (API endpoints)
python test_api.py
```
