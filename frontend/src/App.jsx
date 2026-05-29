import { useState } from 'react';
import FileUpload from './components/FileUpload';
import PianoKeyboard from './components/PianoKeyboard';
import ResultsPanel from './components/ResultsPanel';
import { compareRecordings } from './api/client';

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (audioFile, midiFile) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await compareRecordings(audioFile, midiFile);
      setResults(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎹 Piano Performance Analyzer</h1>
        <p className="subtitle">
          Compare your recorded performance against a reference MIDI file
        </p>
      </header>

      <main className="app-main">
        <section className="upload-section">
          <FileUpload onUpload={handleUpload} loading={loading} />
        </section>

        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {results && (
          <section className="results-section">
            <ResultsPanel results={results} />
            <PianoKeyboard noteResults={results.notes || []} />
          </section>
        )}
      </main>
    </div>
  );
}
