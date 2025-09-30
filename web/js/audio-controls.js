/**
 * Audio controls and state management
 */

class AudioController {
    constructor() {
        this.deckStates = {
            a: {
                playing: false,
                track: null,
                position: 0,
                duration: 0,
                volume: 1.0,
                bpm: 120
            },
            b: {
                playing: false,
                track: null,
                position: 0,
                duration: 0,
                volume: 1.0,
                bpm: 120
            }
        };

        this.crossfaderPosition = 0.5;
        this.masterVolume = 1.0;

        this.init();
    }

    init() {
        // Set up periodic UI updates
        setInterval(() => this.updatePlaybackPositions(), 100);
    }

    updateAudioState(audioData) {
        if (!audioData) return;

        // Update deck states
        if (audioData.deck_a) {
            this.updateDeckState('a', audioData.deck_a);
        }

        if (audioData.deck_b) {
            this.updateDeckState('b', audioData.deck_b);
        }

        // Update crossfader
        if (audioData.crossfader !== undefined) {
            this.updateCrossfader(audioData.crossfader);
        }

        // Update master volume
        if (audioData.master_volume !== undefined) {
            this.masterVolume = audioData.master_volume;
        }
    }

    updateDeckState(deck, state) {
        const deckState = this.deckStates[deck];

        // Update state
        deckState.playing = state.playing || false;
        deckState.position = state.position || 0;
        deckState.duration = state.duration || 0;
        deckState.volume = state.volume || 1.0;
        deckState.bpm = state.bpm || 120;

        // Update UI elements
        this.updateDeckUI(deck, state);

        // Update waveform
        if (state.waveform_data) {
            const waveform = deck === 'a' ? window.waveformA : window.waveformB;
            if (waveform) {
                waveform.setWaveformData(state.waveform_data);
            }
        }
    }

    updateDeckUI(deck, state) {
        // Update play/pause button
        const playBtn = document.getElementById(`play-${deck}`);
        if (playBtn) {
            const icon = playBtn.querySelector('.button-icon');
            if (icon) {
                icon.textContent = state.playing ? '⏸️' : '▶️';
            }
            playBtn.classList.toggle('playing', state.playing);
        }

        // Update BPM display
        const bpmDisplay = document.getElementById(`bpm-${deck}`);
        if (bpmDisplay && state.bpm) {
            bpmDisplay.textContent = state.bpm.toFixed(1);
        }

        // Update volume
        const volumeFill = document.getElementById(`volume-${deck}`);
        const volumeValue = document.getElementById(`volume-value-${deck}`);
        if (volumeFill && state.volume !== undefined) {
            volumeFill.style.width = `${state.volume * 100}%`;
        }
        if (volumeValue && state.volume !== undefined) {
            volumeValue.textContent = `${Math.round(state.volume * 100)}%`;
        }

        // Update track info if provided
        if (state.track_name) {
            const trackTitle = document.querySelector(`#track-info-${deck} .track-title`);
            if (trackTitle) {
                trackTitle.textContent = state.track_name;
            }
        }

        if (state.artist) {
            const trackArtist = document.querySelector(`#track-info-${deck} .track-artist`);
            if (trackArtist) {
                trackArtist.textContent = state.artist;
            }
        }
    }

    updatePlaybackPositions() {
        // Update position displays and waveforms for playing decks
        ['a', 'b'].forEach(deck => {
            const deckState = this.deckStates[deck];

            if (deckState.playing && deckState.duration > 0) {
                // Estimate position (will be corrected by server updates)
                deckState.position += 0.1;
                if (deckState.position > deckState.duration) {
                    deckState.position = deckState.duration;
                }
            }

            // Update time display
            this.updateTimeDisplay(deck, deckState.position, deckState.duration);

            // Update waveform position
            const waveform = deck === 'a' ? window.waveformA : window.waveformB;
            if (waveform) {
                waveform.updatePosition(deckState.position, deckState.duration);
            }

            // Update position marker
            this.updatePositionMarker(deck, deckState.position, deckState.duration);
        });
    }

    updateTimeDisplay(deck, position, duration) {
        const currentTimeEl = document.getElementById(`current-time-${deck}`);
        const totalTimeEl = document.getElementById(`total-time-${deck}`);

        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatTime(position);
        }

        if (totalTimeEl) {
            totalTimeEl.textContent = this.formatTime(duration);
        }
    }

    updatePositionMarker(deck, position, duration) {
        const marker = document.getElementById(`position-${deck}`);
        if (marker && duration > 0) {
            const percentage = (position / duration) * 100;
            marker.style.left = `${percentage}%`;
        }
    }

    updateCrossfader(position) {
        this.crossfaderPosition = position;
        const knob = document.getElementById('crossfader');
        if (knob) {
            knob.style.left = `${position * 100}%`;
        }
    }

    formatTime(seconds) {
        if (!seconds || seconds < 0) return '00:00';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    // Handle play/pause toggle
    togglePlayPause(deck) {
        const deckState = this.deckStates[deck];
        deckState.playing = !deckState.playing;

        // Send to backend via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('play_pause', { deck: deck });
        }
    }

    // Handle stop
    stopDeck(deck) {
        const deckState = this.deckStates[deck];
        deckState.playing = false;
        deckState.position = 0;

        // Send to backend via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('stop', { deck: deck });
        }
    }

    // Handle sync
    syncDeck(deck) {
        // Send to backend via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('sync', { deck: deck });
        }
    }
}

// Initialize audio controller
let audioController = null;

document.addEventListener('DOMContentLoaded', () => {
    audioController = new AudioController();
    window.audioController = audioController;
});