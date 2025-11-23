/**
 * Main application controller for AirGroove DJ Interface
 */

class AirGrooveApp {
    constructor() {
        this.wsClient = null;
        this.gestureUI = null;
        this.libraryManager = null;
        this.isInitialized = false;

        // Performance tracking
        this.lastFrameTime = performance.now();
        this.frameCount = 0;
        this.fps = 0;

        // Current mode tracking
        this.currentMode = 'normal';

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

            // Initialize Library Manager
            this.libraryManager = new LibraryManager(this.wsClient);
            console.log('✓ Library manager initialized');

            // Set up event listeners
            this.setupEventListeners();
            console.log('✓ Event listeners set up');

            // Start performance monitoring
            this.startPerformanceMonitoring();
            console.log('✓ Performance monitoring started');

            this.isInitialized = true;
            console.log('🎵 AirGroove DJ Interface ready!');

            // Initialize normal mode controls by default
            this.injectModeControls('normal');

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
            this.updateGestureText(gestureData);
            this.updateDebugInfo(gestureData);
        };

        // Handle audio updates
        this.wsClient.onAudioUpdate = (audioData) => {
            console.log('[TRACE-FRONTEND] onAudioUpdate called, has fx_state:', !!audioData.fx_state);
            if (audioData.fx_state) {
                console.log('[TRACE-FRONTEND] FX state received:', audioData.fx_state);
            }

            // Use the new audio controller for updates
            if (window.audioController) {
                window.audioController.updateAudioState(audioData);
            }

            // Update FX display if we have FX state data
            if (audioData.fx_state) {
                console.log('[TRACE-FRONTEND] Calling updateFXDisplay with:', audioData.fx_state);
                this.updateFXDisplay(audioData.fx_state);
                console.log('[TRACE-FRONTEND] updateFXDisplay completed');
            }
        };

        // Handle system updates (FPS, status, etc.)
        this.wsClient.onSystemUpdate = (systemData) => {
            this.updateSystemStatus(systemData);
            // Quick gesture notifications removed
        };

        // Handle connection changes
        this.wsClient.onConnectionChange = (connected) => {
            this.handleConnectionChange(connected);
        };

        // Handle mode changes from backend
        this.wsClient.onModeChange = (modeData) => {
            this.updateModeDisplay(modeData.mode);
        };

        // Handle mode gesture updates from backend
        this.wsClient.onModeGesture = (gestureData) => {
            this.handleModeGesture(gestureData);
        };

        // Handle FX state updates from backend
        this.wsClient.onFXStateUpdate = (fxState) => {
            this.updateFXDisplay(fxState);
        };

        // Make wsClient globally available
        window.wsClient = this.wsClient;
    }

    updateModeDisplay(mode) {
        console.log('[UI] Mode changed to:', mode);

        // Store current mode
        this.currentMode = mode;

        // Update mode name display
        const modeNameEl = document.getElementById('current-mode-name');
        if (modeNameEl) {
            modeNameEl.textContent = mode.toUpperCase();
            // Update color class
            modeNameEl.className = 'mode-name mode-' + mode;
            console.log('[UI] Updated mode name element:', mode);
        } else {
            console.warn('[UI] Mode name element not found');
        }

        // Update mode selector items - highlight active mode
        const modeItems = document.querySelectorAll('.mode-item');
        console.log('[UI] Found mode items:', modeItems.length);

        modeItems.forEach(item => {
            if (item.dataset.mode === mode) {
                item.classList.add('active');
                console.log('[UI] Activated mode item:', item.dataset.mode);
            } else {
                item.classList.remove('active');
            }
        });

        // Inject mode-specific controls
        this.injectModeControls(mode);

        // Visual feedback notification
        this.showNotification(`Mode: ${mode.toUpperCase()}`, 'info');
    }

    updateGestureText(gestureData) {
        // Update left hand gesture text
        if (gestureData.left_hand) {
            const leftGestureText = document.getElementById('left-gesture-text');
            if (leftGestureText) {
                leftGestureText.textContent = gestureData.left_hand.gesture || 'none';
            }
        }

        // Update right hand gesture text
        if (gestureData.right_hand) {
            const rightGestureText = document.getElementById('right-gesture-text');
            if (rightGestureText) {
                rightGestureText.textContent = gestureData.right_hand.gesture || 'none';
            }
        }
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

        // Mode selector item clicks (header mode buttons)
        document.querySelectorAll('.mode-item').forEach(item => {
            item.addEventListener('click', () => {
                const mode = item.dataset.mode;
                console.log('[UI] Mode item clicked:', mode);

                // Send mode change to backend
                if (this.wsClient) {
                    this.wsClient.sendModeSelection(mode);
                }

                // Update UI immediately
                this.updateModeDisplay(mode);
            });
        });

        // Play/stop button handlers
        document.getElementById('play-a')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.togglePlayPause('a');
            }
        });

        document.getElementById('stop-a')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.stopDeck('a');
            }
        });

        document.getElementById('play-b')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.togglePlayPause('b');
            }
        });

        document.getElementById('stop-b')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.stopDeck('b');
            }
        });

        // Load track button handlers
        document.getElementById('load-track-a')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.loadTrack('a');
            }
        });

        document.getElementById('load-track-b')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.loadTrack('b');
            }
        });

        // Add unload/eject buttons if they exist
        document.getElementById('eject-a')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.unloadTrack('a');
            }
        });

        document.getElementById('eject-b')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.unloadTrack('b');
            }
        });

        // Sync button handlers
        document.getElementById('sync-a')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.syncDeck('a');
            }
        });

        document.getElementById('sync-b')?.addEventListener('click', () => {
            if (window.audioController) {
                window.audioController.syncDeck('b');
            }
        });

        // Track navigation handlers
        document.getElementById('prev-track-a')?.addEventListener('click', () => {
            if (this.libraryManager) {
                this.libraryManager.previousTrack('a');
            }
        });

        document.getElementById('next-track-a')?.addEventListener('click', () => {
            if (this.libraryManager) {
                this.libraryManager.nextTrack('a');
            }
        });

        document.getElementById('prev-track-b')?.addEventListener('click', () => {
            if (this.libraryManager) {
                this.libraryManager.previousTrack('b');
            }
        });

        document.getElementById('next-track-b')?.addEventListener('click', () => {
            if (this.libraryManager) {
                this.libraryManager.nextTrack('b');
            }
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
            playBtn.innerHTML = data.playing ? Icons.get('pause') : Icons.get('play');
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

    // Quick gesture action removed - no longer needed

    formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return '00:00';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    injectModeControls(mode) {
        const modeControlsContainer = document.getElementById('mode-controls');
        if (!modeControlsContainer) return;

        // Show/hide FX and Loop panels based on mode
        const fxPanel = document.getElementById('fx-controls-panel');
        const loopPanel = document.getElementById('loop-controls-panel');

        if (fxPanel) {
            fxPanel.style.display = (mode === 'fx') ? 'block' : 'none';
        }
        if (loopPanel) {
            loopPanel.style.display = (mode === 'loop') ? 'block' : 'none';
        }

        // Clear existing controls
        modeControlsContainer.innerHTML = '';

        let controlsHTML = '';

        switch (mode) {
            case 'normal':
                controlsHTML = `
                    <div class="mode-control-panel">
                        <h4 class="mode-panel-title">NORMAL MODE</h4>
                        <div class="gesture-list">
                            <div class="gesture-item">
                                <span class="gesture-icon">👆</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Tap</div>
                                    <div class="gesture-desc">Play/Pause</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">🤏</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Pinch Vertical</div>
                                    <div class="gesture-desc">Volume Control</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">👈👉</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Swipe L/R</div>
                                    <div class="gesture-desc">Switch Mode</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;

            case 'fx':
                controlsHTML = `
                    <div class="mode-control-panel">
                        <h4 class="mode-panel-title">FX MODE</h4>
                        <div class="current-effect">
                            <label>Current Effect:</label>
                            <span id="current-effect-type">Filter</span>
                        </div>
                        <div class="effect-parameters">
                            <div class="param-display">
                                <label>Wet/Dry Mix:</label>
                                <span id="effect-wet-dry">50%</span>
                            </div>
                            <div class="param-display">
                                <label>Parameter:</label>
                                <span id="effect-param">0%</span>
                            </div>
                        </div>
                        <div class="gesture-list">
                            <div class="gesture-item">
                                <span class="gesture-icon">🤏↕️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Pinch Vertical</div>
                                    <div class="gesture-desc">Wet/Dry Mix</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">🤏↔️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Pinch Horizontal</div>
                                    <div class="gesture-desc">Effect Parameter</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">✌️↕️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Two Fingers</div>
                                    <div class="gesture-desc">Select Effect</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;

            case 'loop':
                controlsHTML = `
                    <div class="mode-control-panel">
                        <h4 class="mode-panel-title">LOOP MODE</h4>
                        <div class="loop-status">
                            <div class="param-display">
                                <label>Loop Status:</label>
                                <span id="loop-active">Inactive</span>
                            </div>
                            <div class="param-display">
                                <label>Loop Length:</label>
                                <span id="loop-length">4 beats</span>
                            </div>
                        </div>
                        <div class="gesture-list">
                            <div class="gesture-item">
                                <span class="gesture-icon">✌️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Peace Sign</div>
                                    <div class="gesture-desc">Set Loop In/Out</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">🤏</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Pinch</div>
                                    <div class="gesture-desc">Adjust Loop Length</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">✌️↔️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Two Fingers Move</div>
                                    <div class="gesture-desc">Move Loop Position</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;

            case 'scratch':
                controlsHTML = `
                    <div class="mode-control-panel">
                        <h4 class="mode-panel-title">SCRATCH MODE</h4>
                        <div class="scratch-status">
                            <div class="param-display">
                                <label>Sensitivity:</label>
                                <span id="scratch-sensitivity">Medium</span>
                            </div>
                            <div class="param-display">
                                <label>Scratch Active:</label>
                                <span id="scratch-active">No</span>
                            </div>
                        </div>
                        <div class="gesture-list">
                            <div class="gesture-item">
                                <span class="gesture-icon">🖐️🔄</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Palm Rotation</div>
                                    <div class="gesture-desc">Scratch/Scrub</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">🤏</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Pinch</div>
                                    <div class="gesture-desc">Adjust Sensitivity</div>
                                </div>
                            </div>
                            <div class="gesture-item">
                                <span class="gesture-icon">✌️</span>
                                <div class="gesture-info">
                                    <div class="gesture-name">Two Fingers</div>
                                    <div class="gesture-desc">Beatjump</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;

            default:
                controlsHTML = `
                    <div class="no-mode-message">
                        <p>Select a mode to see controls</p>
                        <p>Make a fist over a mode button</p>
                    </div>
                `;
        }

        modeControlsContainer.innerHTML = controlsHTML;
    }

    handleModeGesture(gestureData) {
        // Handle mode-specific gestures
        const { mode, gesture, action, value, deck } = gestureData;

        console.log('[Mode Gesture]', { mode, gesture, action, value, deck });

        // Update UI based on mode and gesture
        switch (mode) {
            case 'fx':
                this.handleFXGesture(gesture, action, value, deck);
                break;
            case 'loop':
                this.handleLoopGesture(gesture, action, value, deck);
                break;
            case 'scratch':
                this.handleScratchGesture(gesture, action, value, deck);
                break;
        }

        // Send to backend
        if (this.wsClient) {
            this.wsClient.send('mode_gesture', {
                mode: mode,
                gesture: gesture,
                action: action,
                value: value,
                deck: deck
            });
        }
    }

    handleFXGesture(gesture, action, value, deck) {
        // Update FX UI elements
        switch (action) {
            case 'adjust_wet':
                const wetDryEl = document.getElementById('effect-wet-dry');
                if (wetDryEl) {
                    wetDryEl.textContent = `${Math.round(value * 100)}%`;
                }
                break;
            case 'adjust_param':
                const paramEl = document.getElementById('effect-param');
                if (paramEl) {
                    paramEl.textContent = `${Math.round(value * 100)}%`;
                }
                break;
            case 'select_effect':
                const effectTypeEl = document.getElementById('current-effect-type');
                if (effectTypeEl) {
                    const effects = ['Filter', 'Echo', 'Reverb', 'Delay', 'Flanger'];
                    const effectIndex = Math.floor(value * effects.length);
                    effectTypeEl.textContent = effects[Math.min(effectIndex, effects.length - 1)];
                }
                break;
        }
    }

    updateFXDisplay(fxState) {
        // Update FX state display with real filter parameters
        console.log('[TRACE-FX-DISPLAY] updateFXDisplay called with:', fxState);
        if (!fxState) {
            console.log('[TRACE-FX-DISPLAY] No FX state provided, returning');
            return;
        }

        // Update filter type
        const effectTypeEl = document.getElementById('current-effect-type');
        console.log('[TRACE-FX-DISPLAY] effectTypeEl:', effectTypeEl, 'filter_type:', fxState.filter_type);
        if (effectTypeEl && fxState.filter_type) {
            const filterType = fxState.filter_type.charAt(0).toUpperCase() + fxState.filter_type.slice(1);
            effectTypeEl.textContent = filterType;
            console.log('[TRACE-FX-DISPLAY] Updated filter type to:', filterType);

            // Color code filter types
            const colors = {
                'lowpass': '#3b82f6',   // blue
                'highpass': '#ef4444',  // red
                'bandpass': '#8b5cf6'   // purple
            };
            effectTypeEl.style.color = colors[fxState.filter_type] || '#fff';
        }

        // Update cutoff frequency
        const paramEl = document.getElementById('effect-param');
        console.log('[TRACE-FX-DISPLAY] paramEl:', paramEl, 'filter_cutoff:', fxState.filter_cutoff);
        if (paramEl && fxState.filter_cutoff !== undefined) {
            paramEl.textContent = `${Math.round(fxState.filter_cutoff)}Hz`;
            console.log('[TRACE-FX-DISPLAY] Updated cutoff to:', Math.round(fxState.filter_cutoff), 'Hz');
        }

        // Update wet/dry mix
        const wetDryEl = document.getElementById('effect-wet-dry');
        console.log('[TRACE-FX-DISPLAY] wetDryEl:', wetDryEl, 'wet_dry_mix:', fxState.wet_dry_mix);
        if (wetDryEl && fxState.wet_dry_mix !== undefined) {
            wetDryEl.textContent = `${Math.round(fxState.wet_dry_mix * 100)}%`;
            console.log('[TRACE-FX-DISPLAY] Updated wet/dry to:', Math.round(fxState.wet_dry_mix * 100), '%');
        }

        // Update resonance (if there's an element for it)
        const resonanceEl = document.getElementById('effect-resonance');
        console.log('[TRACE-FX-DISPLAY] resonanceEl:', resonanceEl, 'filter_resonance:', fxState.filter_resonance);
        if (resonanceEl && fxState.filter_resonance !== undefined) {
            resonanceEl.textContent = `Q: ${fxState.filter_resonance.toFixed(1)}`;
            console.log('[TRACE-FX-DISPLAY] Updated resonance to Q:', fxState.filter_resonance.toFixed(1));
        }

        // Update filter enabled state
        const filterStatusEl = document.getElementById('effect-status');
        if (filterStatusEl && fxState.filter_enabled !== undefined) {
            filterStatusEl.textContent = fxState.filter_enabled ? 'ENABLED' : 'DISABLED';
            filterStatusEl.style.color = fxState.filter_enabled ? '#22c55e' : '#a1a1aa';
        }
    }

    handleLoopGesture(gesture, action, value, deck) {
        // Update Loop UI elements
        switch (action) {
            case 'set_loop':
                const loopActiveEl = document.getElementById('loop-active');
                if (loopActiveEl) {
                    loopActiveEl.textContent = value ? 'Active' : 'Inactive';
                    loopActiveEl.style.color = value ? '#22c55e' : '#a1a1aa';
                }
                break;
            case 'adjust_length':
                const loopLengthEl = document.getElementById('loop-length');
                if (loopLengthEl) {
                    const lengths = [1, 2, 4, 8, 16];
                    const lengthIndex = Math.floor(value * lengths.length);
                    loopLengthEl.textContent = `${lengths[Math.min(lengthIndex, lengths.length - 1)]} beats`;
                }
                break;
        }
    }

    handleScratchGesture(gesture, action, value, deck) {
        // Update Scratch UI elements
        switch (action) {
            case 'adjust_sensitivity':
                const sensEl = document.getElementById('scratch-sensitivity');
                if (sensEl) {
                    if (value < 0.33) {
                        sensEl.textContent = 'Low';
                    } else if (value < 0.66) {
                        sensEl.textContent = 'Medium';
                    } else {
                        sensEl.textContent = 'High';
                    }
                }
                break;
            case 'scratch_active':
                const scratchActiveEl = document.getElementById('scratch-active');
                if (scratchActiveEl) {
                    scratchActiveEl.textContent = value ? 'Yes' : 'No';
                    scratchActiveEl.style.color = value ? '#22c55e' : '#a1a1aa';
                }
                break;
        }
    }

    showHowToUse() {
        // Create modal for How to Use guide
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: rgba(15, 15, 20, 0.98);
            border: 1px solid rgba(124, 58, 237, 0.3);
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            color: #e4e4e7;
        `;

        content.innerHTML = `
            <h2 style="color: #b19aff; margin-bottom: 20px; font-size: 28px; font-weight: 700;">
                🎵 How to Use AirGroove
            </h2>

            <div style="background: rgba(124, 58, 237, 0.1); border-left: 3px solid #b19aff; padding: 15px; margin-bottom: 25px; border-radius: 8px;">
                <p style="margin: 0; color: #e4e4e7; font-size: 14px;">
                    <b>Welcome to AirGroove!</b> Control your DJ setup with simple hand gestures.
                    No physical equipment needed - just your webcam and your hands.
                </p>
            </div>

            <h3 style="color: #00ff88; margin: 25px 0 15px; font-size: 20px; font-weight: 600;">
                🎚️ Deck Controls
            </h3>
            <div style="background: rgba(0, 255, 136, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">✊</span>
                        <b style="color: #00ff88;">Closed Fist</b>
                        <span style="color: #a1a1aa;">- Play/Pause Deck</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Hold for 0.3 seconds • Left hand → Deck A • Right hand → Deck B
                        </div>
                    </li>
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">👍</span>
                        <b style="color: #00ff88;">Thumbs Up</b>
                        <span style="color: #a1a1aa;">- Load Track</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Hold for 0.8 seconds • Opens file browser for selected deck
                        </div>
                    </li>
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">👎</span>
                        <b style="color: #00ff88;">Thumbs Down</b>
                        <span style="color: #a1a1aa;">- Unload Track</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Hold for 0.8 seconds • Ejects track from deck
                        </div>
                    </li>
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">✌️</span>
                        <b style="color: #00ff88;">Two Fingers</b>
                        <span style="color: #a1a1aa;">- Stop Deck</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Stops playback and resets position to start
                        </div>
                    </li>
                </ul>
            </div>

            <h3 style="color: #ff88cc; margin: 25px 0 15px; font-size: 20px; font-weight: 600;">
                🎛️ Crossfader & Mixing
            </h3>
            <div style="background: rgba(255, 136, 204, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">👌</span>
                        <b style="color: #ff88cc;">Pinch Gesture</b>
                        <span style="color: #a1a1aa;">- Control Crossfader</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Move hand left/right • Use one or both hands • Smooth constant-power mixing
                        </div>
                    </li>
                </ul>
            </div>

            <h3 style="color: #88ccff; margin: 25px 0 15px; font-size: 20px; font-weight: 600;">
                ✋ Navigation
            </h3>
            <div style="background: rgba(136, 204, 255, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin: 12px 0; padding-left: 30px; position: relative;">
                        <span style="position: absolute; left: 0; font-size: 20px;">✋</span>
                        <b style="color: #88ccff;">Open Palm Swipe</b>
                        <span style="color: #a1a1aa;">- Switch Modes</span>
                        <div style="font-size: 12px; color: #71717a; margin-top: 4px;">
                            Swipe left or right to cycle: FX → Loop → Scratch
                        </div>
                    </li>
                </ul>
            </div>

            <h3 style="color: #ffaa00; margin: 25px 0 15px; font-size: 20px; font-weight: 600;">
                💡 Pro Tips
            </h3>
            <div style="background: rgba(255, 170, 0, 0.05); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <ul style="list-style: none; padding: 0; margin: 0;">
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        <b style="color: #e4e4e7;">Left hand controls Deck A</b>, Right hand controls Deck B
                    </li>
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        Hold gestures to prevent accidental triggers (0.3-0.8 seconds)
                    </li>
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        Keep hands clearly visible in the camera frame
                    </li>
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        Good lighting significantly improves gesture detection
                    </li>
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        Avoid rapid movements for more stable control
                    </li>
                    <li style="margin: 8px 0; padding-left: 20px; position: relative; color: #a1a1aa; font-size: 14px;">
                        <span style="position: absolute; left: 0; color: #ffaa00;">▸</span>
                        No cursor needed - direct gesture-to-action mapping
                    </li>
                </ul>
            </div>

            <button onclick="this.parentElement.parentElement.remove()" style="
                margin-top: 20px;
                background: rgba(124, 58, 237, 0.2);
                border: 1px solid rgba(124, 58, 237, 0.5);
                color: #b19aff;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
            ">Close</button>
        `;

        modal.appendChild(content);
        document.body.appendChild(modal);

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
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