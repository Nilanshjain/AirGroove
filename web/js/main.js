/**
 * Main application controller for AirGroove DJ Interface
 */

class AirGrooveApp {
    constructor() {
        this.wsClient = null;
        this.gestureUI = null;
        this.isInitialized = false;

        // Performance tracking
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.fps = 0;

        this.init();
    }

    async init() {
        console.log('Initializing AirGroove DJ Interface...');

        try {
            // Initialize UI components
            this.gestureUI = new GestureUI();
            console.log('✓ Gesture UI initialized');

            // Initialize WebSocket connection
            this.wsClient = new WebSocketClient();
            this.setupWebSocketHandlers();
            console.log('✓ WebSocket client initialized');

            // Set up event listeners
            this.setupEventListeners();
            console.log('✓ Event listeners set up');

            // Start performance monitoring
            this.startPerformanceMonitoring();
            console.log('✓ Performance monitoring started');

            this.isInitialized = true;
            console.log('🎵 AirGroove DJ Interface ready!');

            // Show initialization success
            this.showNotification('AirGroove initialized successfully!', 'success');

        } catch (error) {
            console.error('Failed to initialize AirGroove:', error);
            this.showNotification('Failed to initialize AirGroove', 'error');
        }
    }

    setupWebSocketHandlers() {
        // Handle gesture updates from backend
        this.wsClient.onGestureUpdate = (gestureData) => {
            if (this.gestureUI) {
                this.gestureUI.updateGestureState(gestureData);
            }
            this.updateDebugInfo(gestureData);
        };

        // Handle audio updates
        this.wsClient.onAudioUpdate = (audioData) => {
            this.updateAudioDisplay(audioData);
        };

        // Handle system updates (FPS, status, etc.)
        this.wsClient.onSystemUpdate = (systemData) => {
            this.updateSystemStatus(systemData);

            // Handle quick gesture feedback
            if (systemData.quick_gesture && systemData.button_action) {
                this.handleQuickGestureAction(systemData.quick_gesture);
            }
        };

        // Handle connection changes
        this.wsClient.onConnectionChange = (connected) => {
            this.handleConnectionChange(connected);
        };

        // Make wsClient globally available
        window.wsClient = this.wsClient;
    }

    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboard(event);
        });

        // Window events
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        // Mode button clicks (backup for gesture control)
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                if (this.gestureUI) {
                    this.gestureUI.selectMode(mode, btn);
                }
            });
        });

        // Play/stop button handlers
        document.getElementById('play-a')?.addEventListener('click', () => {
            this.sendAudioCommand('play', 'deck_a');
        });

        document.getElementById('stop-a')?.addEventListener('click', () => {
            this.sendAudioCommand('stop', 'deck_a');
        });

        document.getElementById('play-b')?.addEventListener('click', () => {
            this.sendAudioCommand('play', 'deck_b');
        });

        document.getElementById('stop-b')?.addEventListener('click', () => {
            this.sendAudioCommand('stop', 'deck_b');
        });
    }

    handleKeyboard(event) {
        // Keyboard shortcuts for testing and backup control
        switch (event.key) {
            case ' ':
                event.preventDefault();
                this.sendAudioCommand('play_pause', 'deck_a');
                break;

            case 's':
                this.sendAudioCommand('stop', 'deck_a');
                break;

            case '1':
                this.gestureUI?.selectMode('fx', document.getElementById('mode-fx'));
                break;

            case '2':
                this.gestureUI?.selectMode('loop', document.getElementById('mode-loop'));
                break;

            case '3':
                this.gestureUI?.selectMode('scratch', document.getElementById('mode-scratch'));
                break;

            case 'Escape':
                this.gestureUI?.clearAllHovers();
                break;
        }
    }

    sendAudioCommand(action, deck = null) {
        if (this.wsClient) {
            this.wsClient.sendAudioControl(action, { deck: deck });
        }
    }

    updateAudioDisplay(audioData) {
        // Update deck A
        if (audioData.deck_a) {
            this.updateDeckDisplay('a', audioData.deck_a);
        }

        // Update deck B
        if (audioData.deck_b) {
            this.updateDeckDisplay('b', audioData.deck_b);
        }
    }

    updateDeckDisplay(deck, data) {
        // Update track info
        const titleEl = document.querySelector(`#track-info-${deck} .track-title`);
        const artistEl = document.querySelector(`#track-info-${deck} .track-artist`);
        const currentTimeEl = document.getElementById(`current-time-${deck}`);
        const totalTimeEl = document.getElementById(`total-time-${deck}`);
        const bpmEl = document.getElementById(`bpm-${deck}`);

        if (titleEl && data.track_name) {
            titleEl.textContent = data.track_name;
        }

        if (artistEl && data.artist) {
            artistEl.textContent = data.artist;
        }

        if (currentTimeEl && data.position !== undefined) {
            currentTimeEl.textContent = this.formatTime(data.position);
        }

        if (totalTimeEl && data.duration !== undefined) {
            totalTimeEl.textContent = this.formatTime(data.duration);
        }

        if (bpmEl && data.bpm !== undefined) {
            bpmEl.textContent = data.bpm.toFixed(1);
        }

        // Update volume
        const volumeFillEl = document.getElementById(`volume-${deck}`);
        const volumeValueEl = document.getElementById(`volume-value-${deck}`);

        if (volumeFillEl && data.volume !== undefined) {
            volumeFillEl.style.width = `${data.volume * 100}%`;
        }

        if (volumeValueEl && data.volume !== undefined) {
            volumeValueEl.textContent = `${Math.round(data.volume * 100)}%`;
        }

        // Update position marker
        const positionMarker = document.getElementById(`position-${deck}`);
        if (positionMarker && data.position !== undefined && data.duration > 0) {
            const percentage = (data.position / data.duration) * 100;
            positionMarker.style.left = `${percentage}%`;
        }

        // Update play button state
        const playBtn = document.getElementById(`play-${deck}`);
        if (playBtn && data.playing !== undefined) {
            playBtn.textContent = data.playing ? '⏸️' : '▶️';
            playBtn.classList.toggle('playing', data.playing);
        }

        // Update waveform if available
        if (data.waveform) {
            this.updateWaveform(deck, data.waveform);
        }
    }

    updateWaveform(deck, waveformData) {
        const canvas = document.getElementById(`waveform-${deck}`);
        if (!canvas || !waveformData.length) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Draw waveform
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 1;
        ctx.beginPath();

        const stepSize = width / waveformData.length;

        for (let i = 0; i < waveformData.length; i++) {
            const x = i * stepSize;
            const y = height / 2 + (waveformData[i] * height / 2);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();
    }

    updateSystemStatus(systemData) {
        // Update FPS display
        if (systemData.fps !== undefined) {
            const fpsEl = document.getElementById('fps');
            if (fpsEl) {
                fpsEl.textContent = systemData.fps;
            }
        }

        // Update other system metrics as needed
    }

    updateDebugInfo(gestureData) {
        const debugEl = document.getElementById('debug-info');
        if (!debugEl) return;

        const leftGesture = gestureData.left_hand.gesture;
        const rightGesture = gestureData.right_hand.gesture;
        const state = gestureData.interaction_state;

        debugEl.textContent = `L: ${leftGesture} | R: ${rightGesture} | State: ${state}`;
    }

    handleConnectionChange(connected) {
        if (connected) {
            this.showNotification('Connected to AirGroove backend', 'success');
        } else {
            this.showNotification('Disconnected from backend', 'warning');
        }
    }

    startPerformanceMonitoring() {
        const updateFPS = () => {
            const currentTime = performance.now();
            const deltaTime = currentTime - this.lastFrameTime;

            this.frameCount++;

            // Update FPS every second
            if (deltaTime >= 1000) {
                this.fps = Math.round((this.frameCount * 1000) / deltaTime);
                this.frameCount = 0;
                this.lastFrameTime = currentTime;

                // Update FPS display
                const fpsEl = document.getElementById('fps');
                if (fpsEl) {
                    fpsEl.textContent = this.fps;
                }
            }

            requestAnimationFrame(updateFPS);
        };

        requestAnimationFrame(updateFPS);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            backgroundColor: type === 'success' ? '#00ff88' :
                           type === 'error' ? '#ff4444' :
                           type === 'warning' ? '#ffaa00' : '#0099ff',
            color: type === 'success' ? '#000' : '#fff',
            fontWeight: 'bold',
            zIndex: '9999',
            opacity: '0',
            transform: 'translateX(100%)',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    handleQuickGestureAction(quickGesture) {
        // Show visual feedback for quick gesture
        const [hand, gesture] = quickGesture.split('_');

        // Flash the corresponding gesture command in the palette
        const commandPalette = document.querySelector('.gesture-command-palette');
        if (commandPalette) {
            commandPalette.classList.add('gesture-triggered');
            setTimeout(() => {
                commandPalette.classList.remove('gesture-triggered');
            }, 800);
        }

        // Animate gesture pointer
        const gesturePointer = document.getElementById('gesture-pointer');
        if (gesturePointer) {
            gesturePointer.classList.add('quick-gesture');
            setTimeout(() => {
                gesturePointer.classList.remove('quick-gesture');
            }, 500);
        }

        // Show notification
        const gestureNames = {
            'pinch': '👌 Pinch → Deck A',
            'pointer': '👉 Pointer → Deck B',
            'two_fingers': '✌️ Two Fingers → Stop All',
            'closed_fist': '✊ Fist → Action'
        };

        const gestureName = gestureNames[gesture] || gesture;
        this.showNotification(`Quick Gesture: ${gestureName}`, 'success');
    }

    formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return '00:00';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    cleanup() {
        if (this.wsClient) {
            this.wsClient.disconnect();
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AirGrooveApp();
});