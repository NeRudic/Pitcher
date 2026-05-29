import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import FileUpload from './components/FileUpload';
import PianoKeyboard from './components/PianoKeyboard';
import ResultsPanel from './components/ResultsPanel';
import PlaybackControls from './components/PlaybackControls';
import { compareRecordings } from './api/client';

export default function App() {
  // --- Comparison state ---
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- Audio / Playback state ---
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackComplete, setPlaybackComplete] = useState(false);

  const audioRef = useRef(null);
  const rafRef = useRef(null);

  // --- Cleanup audio on unmount ---
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  // --- Compute active notes at currentTime for playback ---
  const activeHighlightMap = useMemo(() => {
    if (!results || !results.notes) return null;

    if (isPlaying) {
      const map = {};
      const t = currentTime;
      const playedNotes = results.played_notes || [];
      const comparisons = results.notes;

      // Build a lookup: key = "pitch:start_time" → comparison result
      const matchLookup = {};
      for (const c of comparisons) {
        if (c.played_pitch != null && c.played_start != null) {
          const key = `${c.played_pitch}:${c.played_start.toFixed(3)}`;
          matchLookup[key] = c.status;
        }
      }

      // Show PLAYED notes active at currentTime
      for (const pn of playedNotes) {
        if (pn.start_time <= t && pn.end_time >= t) {
          const key = `${pn.pitch}:${pn.start_time.toFixed(3)}`;
          // Matched → use comparison status. Unmatched → "wrong"
          map[pn.pitch] = matchLookup[key] || 'wrong';
        }
      }

      return Object.keys(map).length > 0 ? map : {};
    }

    // Static mode: show all reference notes colored by status
    return null;
  }, [results, currentTime, isPlaying]);

  // --- requestAnimationFrame loop ---
  useEffect(() => {
    if (!isPlaying || !audioRef.current) return;

    const tick = () => {
      const audio = audioRef.current;
      if (!audio) return;

      setCurrentTime(audio.currentTime);

      if (audio.ended || audio.paused) {
        if (audio.ended) {
          setIsPlaying(false);
          setPlaybackComplete(true);
        }
        return;
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isPlaying]);

  // --- Handlers ---
  const handleUpload = async (audioFile, midiFile) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setPlaybackComplete(false);
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);

    // Revoke old URL if exists
    if (audioUrl) URL.revokeObjectURL(audioUrl);

    // Create object URL for local playback
    const url = URL.createObjectURL(audioFile);
    setAudioUrl(url);

    try {
      const data = await compareRecordings(audioFile, midiFile);
      setResults(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = useCallback(() => {
    if (!audioUrl) return;

    // Create audio element on first play or reuse
    if (!audioRef.current || audioRef.current.src !== audioUrl) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.addEventListener('loadedmetadata', () => {
        setDuration(audio.duration);
      });

      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        setPlaybackComplete(true);
        setCurrentTime(audio.duration || 0);
      });
    }

    const audio = audioRef.current;
    if (audio.readyState >= 1) {
      setDuration(audio.duration);
    }

    audio.play().then(() => {
      setIsPlaying(true);
      setPlaybackComplete(false);
    }).catch(() => {
      setIsPlaying(false);
    });
  }, [audioUrl]);

  const handlePause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsPlaying(false);
  }, []);

  const handleSeek = useCallback((time) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
    setCurrentTime(time);
  }, []);

  const handleRestart = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
    setCurrentTime(0);
    setPlaybackComplete(false);
    handlePlay();
  }, [handlePlay]);

  // --- Derived state ---
  const showResults = playbackComplete && results;
  const showKeyboard = results && !loading;

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

        {/* Playback controls — shown after successful comparison */}
        {results && !loading && (
          <PlaybackControls
            audioUrl={audioUrl}
            isPlaying={isPlaying}
            currentTime={currentTime}
            duration={duration}
            onPlay={handlePlay}
            onPause={handlePause}
            onSeek={handleSeek}
            onRestart={handleRestart}
            disabled={!audioUrl}
            playbackComplete={playbackComplete}
          />
        )}

        {/* Results — shown after playback completes */}
        {showResults && (
          <section className="results-section">
            <ResultsPanel results={results} />
          </section>
        )}

        {/* Piano keyboard */}
        {showKeyboard && (
          <PianoKeyboard
            noteResults={results.notes || []}
            highlightMap={activeHighlightMap}
          />
        )}
      </main>
    </div>
  );
}
