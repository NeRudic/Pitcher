/**
 * API client for the Piano Performance Analyzer backend.
 */

const API_BASE = '/api';

/**
 * Upload audio and MIDI files for comparison.
 * @param {File} audioFile - The audio recording (.wav/.mp3)
 * @param {File} midiFile - The reference MIDI file (.mid)
 * @returns {Promise<object>} Comparison result from the backend
 */
export async function compareRecordings(audioFile, midiFile) {
  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('midi', midiFile);

  const response = await fetch(`${API_BASE}/compare`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health.
 * @returns {Promise<object>} Health check response
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}
