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
        if (state.waveform) {
            const waveform = deck === 'a' ? window.waveformA : window.waveformB;
            if (waveform) {
                waveform.setWaveformData(state.waveform);
                // Also set duration
                if (state.duration) {
                    waveform.duration = state.duration;
                }
            }
        }
    }

    updateDeckUI(deck, state) {
        // Update deck playing state for visual effects
        const deckElement = document.querySelector(`.deck-${deck}`);
        if (deckElement) {
            deckElement.classList.toggle('playing', state.playing);
        }

        // Update play/pause button
        const playBtn = document.getElementById(`play-${deck}`);
        if (playBtn) {
            const icon = playBtn.querySelector('.button-icon');
            if (icon) {
                icon.innerHTML = state.playing ? Icons.get('pause') : Icons.get('play');
            }
            playBtn.classList.toggle('playing', state.playing);
        }

        // Update BPM display with animation
        const bpmDisplay = document.getElementById(`bpm-${deck}`);
        if (bpmDisplay && state.bpm !== undefined) {
            const currentBPM = parseFloat(bpmDisplay.textContent) || 0;
            const newBPM = state.bpm;

            // Only update if BPM changed significantly
            if (Math.abs(currentBPM - newBPM) > 0.1) {
                bpmDisplay.textContent = newBPM.toFixed(1);
                // Add visual feedback for BPM change
                bpmDisplay.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    bpmDisplay.style.transform = 'scale(1)';
                }, 200);
            }
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

        // Update time displays immediately
        if (state.position !== undefined) {
            this.updateTimeDisplay(deck, state.position, this.deckStates[deck].duration);
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

        // Update knob position
        const knob = document.getElementById('crossfader');
        if (knob) {
            knob.style.left = `${position * 100}%`;
        }

        // Update visual trail (shows crossfader path from left to current position)
        const trail = document.getElementById('crossfader-trail');
        if (trail) {
            trail.style.width = `${position * 100}%`;
        }

        // Update position percentage display
        const positionDisplay = document.getElementById('crossfader-position');
        if (positionDisplay) {
            const percentage = Math.round(position * 100);
            positionDisplay.textContent = `${percentage}%`;

            // Color code based on which deck is dominant
            if (position < 0.45) {
                positionDisplay.style.color = 'rgba(124, 58, 237, 1)';  // Purple for Deck A
            } else if (position > 0.55) {
                positionDisplay.style.color = 'rgba(0, 255, 136, 1)';  // Green for Deck B
            } else {
                positionDisplay.style.color = '#b19aff';  // Neutral purple
            }
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

    // Handle stop - unload the track
    stopDeck(deck) {
        const deckState = this.deckStates[deck];
        deckState.playing = false;
        deckState.position = 0;

        // Send unload_track to backend via WebSocket to completely unload the track
        if (window.wsClient) {
            window.wsClient.sendAudioControl('unload_track', { deck: deck });
        }
    }

    // Handle sync
    syncDeck(deck) {
        console.log(`[Audio] Syncing deck ${deck.toUpperCase()}`);

        // Get the other deck
        const otherDeck = deck === 'a' ? 'b' : 'a';

        // Get BPMs
        const currentBPM = this.deckStates[deck].bpm;
        const targetBPM = this.deckStates[otherDeck].bpm;

        console.log(`[Audio] Current BPM: ${currentBPM}, Target BPM: ${targetBPM}`);

        // Visual feedback on sync button
        const syncBtn = document.getElementById(`sync-${deck}`);
        if (syncBtn) {
            syncBtn.classList.add('syncing');
            syncBtn.style.background = 'rgba(124, 58, 237, 0.3)';
            syncBtn.style.borderColor = 'rgba(124, 58, 237, 0.6)';
            syncBtn.style.color = '#b19aff';

            // Reset after animation
            setTimeout(() => {
                syncBtn.classList.remove('syncing');
                syncBtn.style.background = '';
                syncBtn.style.borderColor = '';
                syncBtn.style.color = '';
            }, 500);
        }

        // Send to backend via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('sync', {
                deck: deck,
                target_deck: otherDeck
            });
        }

        // Show notification
        if (window.app) {
            window.app.showNotification(
                `Deck ${deck.toUpperCase()} synced to Deck ${otherDeck.toUpperCase()}`,
                'success'
            );
        }
    }

    // Handle load track
    loadTrack(deck) {
        console.log(`Loading track for deck ${deck}`);
        // Send to backend via WebSocket - backend will open file dialog
        if (window.wsClient) {
            window.wsClient.sendAudioControl('load_track', { deck: deck });
        }
    }

    // Handle unload/eject track
    unloadTrack(deck) {
        console.log(`Unloading track from deck ${deck}`);
        // Send to backend via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('unload_track', { deck: deck });
        }
    }
}

// Initialize audio controller
let audioController = null;

document.addEventListener('DOMContentLoaded', () => {
    audioController = new AudioController();
    window.audioController = audioController;
});