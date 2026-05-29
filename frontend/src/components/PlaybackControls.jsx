import { useRef, useCallback } from 'react';

/**
 * Playback controls — pure UI component.
 * Audio element is managed by the parent (App.jsx).
 *
 * Props:
 *   isPlaying       — current playback state
 *   currentTime     — current audio position in seconds
 *   duration        — total audio duration in seconds
 *   onPlay          — called when Play is clicked
 *   onPause         — called when Pause is clicked
 *   onSeek          — called with new time in seconds
 *   onRestart       — called when Restart is clicked (after completion)
 *   disabled        — disable controls
 *   playbackComplete — whether playback has finished
 */
export default function PlaybackControls({
  isPlaying,
  currentTime,
  duration,
  onPlay,
  onPause,
  onSeek,
  onRestart,
  disabled,
  playbackComplete,
}) {
  const progressRef = useRef(null);

  const handleToggle = useCallback(() => {
    if (playbackComplete) {
      onRestart();
    } else if (isPlaying) {
      onPause();
    } else {
      onPlay();
    }
  }, [isPlaying, playbackComplete, onPlay, onPause, onRestart]);

  const handleProgressClick = useCallback((e) => {
    if (!progressRef.current || !duration) return;
    const rect = progressRef.current.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    onSeek(ratio * duration);
  }, [duration, onSeek]);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const formatTime = (sec) => {
    if (!isFinite(sec) || sec < 0) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const buttonLabel = playbackComplete ? '🔄' : isPlaying ? '⏸' : '▶';
  const buttonTitle = playbackComplete ? 'Replay' : isPlaying ? 'Pause' : 'Play';

  return (
    <div className="playback-controls">
      <button
        className="play-btn"
        onClick={handleToggle}
        disabled={disabled}
        title={buttonTitle}
      >
        {buttonLabel}
      </button>

      <span className="time-display">{formatTime(currentTime)}</span>

      <div
        className="progress-bar"
        ref={progressRef}
        onClick={handleProgressClick}
      >
        <div
          className="progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      <span className="time-display">{formatTime(duration)}</span>
    </div>
  );
}
