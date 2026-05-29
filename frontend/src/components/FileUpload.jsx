import { useState, useRef } from 'react';

/**
 * File upload form for audio recording and reference MIDI.
 */
export default function FileUpload({ onUpload, loading }) {
  const [audioFile, setAudioFile] = useState(null);
  const [midiFile, setMidiFile] = useState(null);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);
  const midiRef = useRef(null);

  const handleAudioChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const validTypes = ['audio/wav', 'audio/mpeg', 'audio/x-wav', 'audio/wave'];
      if (!validTypes.includes(file.type) && !file.name.match(/\.(wav|mp3)$/i)) {
        setError('Please select a .wav or .mp3 file.');
        return;
      }
      setAudioFile(file);
      setError(null);
    }
  };

  const handleMidiChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const validExt = file.name.match(/\.(mid|midi)$/i);
      if (!validExt) {
        setError('Please select a .mid file.');
        return;
      }
      setMidiFile(file);
      setError(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!audioFile || !midiFile) {
      setError('Please select both files.');
      return;
    }
    setError(null);
    onUpload(audioFile, midiFile);
  };

  return (
    <form className="file-upload-form" onSubmit={handleSubmit}>
      <h2>Upload Files</h2>

      <div className="file-inputs">
        <div className="file-input-group">
          <label htmlFor="audio-file">🎵 Audio Recording (.wav / .mp3)</label>
          <input
            ref={audioRef}
            id="audio-file"
            type="file"
            accept=".wav,.mp3,audio/wav,audio/mpeg"
            onChange={handleAudioChange}
          />
          {audioFile && (
            <span className="file-name">✓ {audioFile.name}</span>
          )}
        </div>

        <div className="file-input-group">
          <label htmlFor="midi-file">🎹 Reference MIDI (.mid)</label>
          <input
            ref={midiRef}
            id="midi-file"
            type="file"
            accept=".mid,.midi"
            onChange={handleMidiChange}
          />
          {midiFile && (
            <span className="file-name">✓ {midiFile.name}</span>
          )}
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      <button
        type="submit"
        className="submit-btn"
        disabled={loading || !audioFile || !midiFile}
      >
        {loading ? '⏳ Analyzing...' : '🔍 Compare'}
      </button>
    </form>
  );
}
