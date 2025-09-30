/**
 * Gesture-based control system (no cursor)
 * Direct gesture mapping for DJ interface control
 */

class GestureUI {
    constructor() {
        // Mode management
        this.modes = ['fx', 'loop', 'scratch'];
        this.currentModeIndex = 0;
        this.currentMode = null;

        // Swipe detection
        this.swipeStartX = null;
        this.swipeThreshold = 0.3; // 30% of normalized space
        this.lastSwipeTime = 0;
        this.swipeCooldown = 800; // ms

        // Gesture state tracking
        this.leftGesture = 'none';
        this.rightGesture = 'none';
        this.previousLeftGesture = 'none';
        this.previousRightGesture = 'none';
        this.leftPosition = { x: 0, y: 0 };
        this.rightPosition = { x: 0, y: 0 };

        // Action cooldowns
        this.lastActionTime = {};
        this.actionCooldown = 600; // ms

        // UI elements
        this.modeButtons = document.querySelectorAll('.mode-btn');
        this.leftGestureDisplay = document.getElementById('left-gesture');
        this.rightGestureDisplay = document.getElementById('right-gesture');
        this.interactionStateDisplay = document.getElementById('interaction-state');

        this.init();
    }

    init() {
        console.log('[GestureUI] Initialized - Direct gesture control mode');
        this.updateGestureMapping();
    }

    updateGestureState(gestureData) {
        // Store previous gestures
        this.previousLeftGesture = this.leftGesture;
        this.previousRightGesture = this.rightGesture;

        // Update current gestures
        this.leftGesture = gestureData.left_hand.gesture;
        this.rightGesture = gestureData.right_hand.gesture;

        // Update hand detection status
        this.leftDetected = gestureData.left_hand.detected;
        this.rightDetected = gestureData.right_hand.detected;

        // Update positions
        this.updateHandPosition('left', gestureData.left_hand.position);
        this.updateHandPosition('right', gestureData.right_hand.position);

        // Update displays
        this.updateGestureDisplays(gestureData);

        // Check for backend-detected swipes
        if (gestureData.left_hand.swipe) {
            this.handleSwipeEvent('left', gestureData.left_hand.swipe);
        }
        if (gestureData.right_hand.swipe) {
            this.handleSwipeEvent('right', gestureData.right_hand.swipe);
        }

        // Process gestures
        this.processGestures();
    }

    handleSwipeEvent(hand, direction) {
        const currentTime = Date.now();

        // Check cooldown
        if (currentTime - this.lastSwipeTime < this.swipeCooldown) {
            return;
        }

        this.lastSwipeTime = currentTime;
        console.log(`[Swipe Event] ${hand} hand swipe ${direction}`);

        // Show swipe visual feedback
        this.showSwipeFeedback(direction);

        // Cycle modes based on swipe direction
        if (direction === 'right') {
            this.cycleMode('next');
        } else if (direction === 'left') {
            this.cycleMode('previous');
        }
    }

    showSwipeFeedback(direction) {
        // Create swipe indicator
        const swipeIndicator = document.createElement('div');
        swipeIndicator.className = 'swipe-indicator';
        swipeIndicator.innerHTML = direction === 'right' ? '→' : '←';

        swipeIndicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 72px;
            color: rgba(124, 58, 237, 0.9);
            font-weight: bold;
            z-index: 10000;
            animation: swipeAnimation 0.5s ease;
            pointer-events: none;
        `;

        document.body.appendChild(swipeIndicator);

        setTimeout(() => {
            swipeIndicator.remove();
        }, 500);
    }

    updateHandPosition(hand, position) {
        if (Array.isArray(position) && position.length >= 2) {
            if (hand === 'left') {
                this.leftPosition = { x: position[0], y: position[1] };
            } else {
                this.rightPosition = { x: position[0], y: position[1] };
            }
        } else if (position && typeof position.x !== 'undefined') {
            if (hand === 'left') {
                this.leftPosition = position;
            } else {
                this.rightPosition = position;
            }
        }
    }

    // Removed frontend swipe detection - now handled by backend

    cycleMode(direction) {
        if (direction === 'next') {
            this.currentModeIndex = (this.currentModeIndex + 1) % this.modes.length;
        } else {
            this.currentModeIndex = (this.currentModeIndex - 1 + this.modes.length) % this.modes.length;
        }

        const newMode = this.modes[this.currentModeIndex];
        const button = document.getElementById(`mode-${newMode}`);

        if (button) {
            this.selectMode(newMode, button);
        }
    }

    processGestures() {
        // Use the backend's detection status for better accuracy
        const leftDetected = this.leftDetected && this.leftGesture !== 'none';
        const rightDetected = this.rightDetected && this.rightGesture !== 'none';

        // Debug hand detection
        if (Math.random() < 0.02) {  // 2% chance
            console.log(`[Hand Status] Left: ${leftDetected ? this.leftGesture : 'not detected'}, Right: ${rightDetected ? this.rightGesture : 'not detected'}`);
        }

        // Both hands detected
        if (leftDetected && rightDetected) {
            this.processTwoHandGestures();
        }
        // Only left hand detected
        else if (leftDetected && !rightDetected) {
            this.processSingleHandGesture('left');
        }
        // Only right hand detected
        else if (!leftDetected && rightDetected) {
            this.processSingleHandGesture('right');
        }

        // Update interaction state display
        this.updateInteractionState();
    }

    processTwoHandGestures() {
        // Both hands open = neutral/browsing state
        if (this.leftGesture === 'open_palm' && this.rightGesture === 'open_palm') {
            // No action - just browsing
            return;
        }

        // Left fist + Right gesture combinations
        if (this.leftGesture === 'closed_fist') {
            if (this.rightGesture === 'pinch') {
                this.triggerAction('fx_filter', this.rightPosition);
            } else if (this.rightGesture === 'pointer') {
                this.triggerAction('fx_mix', this.rightPosition);
            } else if (this.rightGesture === 'two_fingers') {
                this.triggerAction('stop_all');
            }
        }

        // Right fist + Left gesture combinations
        if (this.rightGesture === 'closed_fist') {
            if (this.leftGesture === 'pinch') {
                this.triggerAction('loop_length', this.leftPosition);
            } else if (this.leftGesture === 'pointer') {
                this.triggerAction('loop_position', this.leftPosition);
            } else if (this.leftGesture === 'two_fingers') {
                this.triggerAction('stop_all');
            }
        }

        // Special combinations
        if (this.leftGesture === 'pinch' && this.rightGesture === 'pinch') {
            this.triggerAction('crossfader', {
                x: (this.leftPosition.x + this.rightPosition.x) / 2,
                y: (this.leftPosition.y + this.rightPosition.y) / 2
            });
        }
    }

    processSingleHandGesture(hand) {
        const gesture = hand === 'left' ? this.leftGesture : this.rightGesture;
        const position = hand === 'left' ? this.leftPosition : this.rightPosition;

        // Map hands to decks: left hand -> Deck A, right hand -> Deck B
        const deck = hand === 'left' ? 'a' : 'b';

        console.log(`[Single Hand] ${hand} hand (${gesture}) controlling Deck ${deck.toUpperCase()}`);

        // Closed fist = play/pause for corresponding deck
        if (gesture === 'closed_fist') {
            if (this.gestureJustChanged(hand, 'closed_fist')) {
                console.log(`[Action] ${hand} hand fist -> Play/Pause Deck ${deck.toUpperCase()}`);
                this.triggerAction('play_pause', { deck: deck });
            }
        }

        // Pinch = Load track for deck
        else if (gesture === 'pinch') {
            if (this.gestureJustChanged(hand, 'pinch')) {
                console.log(`[Action] ${hand} hand pinch -> Load Track to Deck ${deck.toUpperCase()}`);
                this.triggerAction('load_track', { deck: deck });
            }
        }

        // Pointer = Cue/Sync
        else if (gesture === 'pointer') {
            if (this.gestureJustChanged(hand, 'pointer')) {
                console.log(`[Action] ${hand} hand pointer -> Sync Deck ${deck.toUpperCase()}`);
                this.triggerAction('sync', { deck: deck });
            }
        }

        // Two fingers = Stop deck
        else if (gesture === 'two_fingers') {
            if (this.gestureJustChanged(hand, 'two_fingers')) {
                console.log(`[Action] ${hand} hand two fingers -> Stop Deck ${deck.toUpperCase()}`);
                this.triggerAction('stop', { deck: deck });
            }
        }

        // Open palm with current mode active = mode control
        else if (gesture === 'open_palm' && this.currentMode) {
            this.applyModeControl(hand, position);
        }
    }

    gestureJustChanged(hand, targetGesture) {
        const current = hand === 'left' ? this.leftGesture : this.rightGesture;
        const previous = hand === 'left' ? this.previousLeftGesture : this.previousRightGesture;

        return current === targetGesture && previous !== targetGesture;
    }

    triggerAction(action, params = {}) {
        const currentTime = Date.now();

        // Check cooldown
        if (this.lastActionTime[action] &&
            currentTime - this.lastActionTime[action] < this.actionCooldown) {
            return;
        }

        this.lastActionTime[action] = currentTime;

        console.log(`[GestureUI] Action: ${action}`, params);

        // Send action to backend
        if (window.wsClient) {
            switch(action) {
                case 'play_pause':
                case 'stop':
                case 'sync':
                    window.wsClient.sendAudioControl(action, params);
                    this.showActionFeedback(action, params.deck);
                    break;

                case 'load_track':
                    // Load demo track based on deck
                    const demoTracks = [
                        { path: 'audio/Ainozama.mp3', name: 'Ainozama' },
                        { path: 'audio/pianos-by-jtwayne-7-174717.mp3', name: 'Pianos' }
                    ];
                    const track = demoTracks[params.deck === 'a' ? 0 : 1];

                    window.wsClient.sendAudioControl('load_track', {
                        deck: params.deck,
                        file_path: track.path,
                        file_name: track.name
                    });

                    // Update UI
                    const trackTitle = document.querySelector(`#track-info-${params.deck} .track-title`);
                    const trackArtist = document.querySelector(`#track-info-${params.deck} .track-artist`);
                    if (trackTitle) trackTitle.textContent = track.name;
                    if (trackArtist) trackArtist.textContent = 'Demo Track';

                    this.showActionFeedback(`Load: ${track.name}`, params.deck);
                    break;

                case 'stop_all':
                    window.wsClient.sendAudioControl('stop', { deck: 'a' });
                    window.wsClient.sendAudioControl('stop', { deck: 'b' });
                    this.showActionFeedback('Stop All Decks');
                    break;

                case 'crossfader':
                    window.wsClient.sendAudioControl('crossfader', { position: params.x });
                    break;

                case 'fx_filter':
                case 'fx_mix':
                    if (this.currentMode === 'fx') {
                        const parameter = action.replace('fx_', '');
                        window.wsClient.sendAudioControl('fx_control', {
                            parameter: parameter,
                            value: params.y
                        });
                    }
                    break;

                case 'loop_length':
                case 'loop_position':
                    if (this.currentMode === 'loop') {
                        const parameter = action.replace('loop_', '');
                        window.wsClient.sendAudioControl('loop_control', {
                            parameter: parameter,
                            value: params.x
                        });
                    }
                    break;
            }
        }
    }

    applyModeControl(hand, position) {
        if (!this.currentMode) return;

        // Apply continuous control based on hand position
        if (this.currentMode === 'fx') {
            window.wsClient?.sendAudioControl('fx_control', {
                parameter: hand === 'left' ? 'filter' : 'mix',
                value: position.y
            });
        } else if (this.currentMode === 'loop') {
            window.wsClient?.sendAudioControl('loop_control', {
                parameter: 'position',
                value: position.x
            });
        } else if (this.currentMode === 'scratch') {
            const centerX = 0.5;
            const scratchSpeed = (position.x - centerX) * 2; // -1 to 1
            window.wsClient?.sendAudioControl('scratch_control', {
                parameter: 'speed',
                value: scratchSpeed
            });
        }
    }

    selectMode(mode, button) {
        // Clear previous selection
        this.modeButtons.forEach(btn => btn.classList.remove('active'));

        // Activate new mode
        button.classList.add('active');
        this.currentMode = mode;

        // Update mode index
        this.currentModeIndex = this.modes.indexOf(mode);

        // Update display
        this.updateModeControls(mode);

        // Send to backend
        window.wsClient?.sendModeSelection(mode);

        // Visual feedback
        this.showActionFeedback(`Mode: ${mode.toUpperCase()}`);

        console.log(`[GestureUI] Mode selected: ${mode}`);
    }

    updateModeControls(mode) {
        const modeControlsEl = document.getElementById('mode-controls');
        if (!modeControlsEl) return;

        const modeDescriptions = {
            'fx': `
                <div class="mode-info">
                    <h4>FX Mode Active</h4>
                    <p>Left Fist + Right Pinch: Filter</p>
                    <p>Left Fist + Right Pointer: Mix</p>
                    <p>Open Palm: Y-axis control</p>
                </div>
            `,
            'loop': `
                <div class="mode-info">
                    <h4>Loop Mode Active</h4>
                    <p>Right Fist + Left Pinch: Length</p>
                    <p>Right Fist + Left Pointer: Position</p>
                    <p>Open Palm: X-axis control</p>
                </div>
            `,
            'scratch': `
                <div class="mode-info">
                    <h4>Scratch Mode Active</h4>
                    <p>Open Palm: Scratch speed</p>
                    <p>Hand position controls speed</p>
                </div>
            `
        };

        modeControlsEl.innerHTML = modeDescriptions[mode] || '<p>No mode selected</p>';
    }

    updateGestureDisplays(gestureData) {
        // Update gesture emoji displays
        const gestureEmojis = {
            'open_palm': '✋',
            'closed_fist': '✊',
            'pinch': '👌',
            'pointer': '👉',
            'two_fingers': '✌️',
            'none': '—'
        };

        if (this.leftGestureDisplay) {
            this.leftGestureDisplay.textContent = gestureEmojis[this.leftGesture] || '?';
        }

        if (this.rightGestureDisplay) {
            this.rightGestureDisplay.textContent = gestureEmojis[this.rightGesture] || '?';
        }
    }

    updateInteractionState() {
        if (!this.interactionStateDisplay) return;

        let state = 'ready';

        // Determine state based on gestures
        if (this.leftGesture === 'open_palm' && this.rightGesture === 'open_palm') {
            state = 'browsing';
        } else if (this.leftGesture === 'closed_fist' || this.rightGesture === 'closed_fist') {
            state = 'controlling';
        } else if (this.leftGesture !== 'none' || this.rightGesture !== 'none') {
            state = 'active';
        }

        this.interactionStateDisplay.textContent = state;
        this.interactionStateDisplay.className = `interaction-state state-${state}`;
    }

    showActionFeedback(action, deck = null) {
        // Create temporary visual feedback
        const feedback = document.createElement('div');
        feedback.className = 'action-feedback';
        feedback.textContent = deck ? `${action} - Deck ${deck.toUpperCase()}` : action;

        feedback.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(124, 58, 237, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            z-index: 1000;
            animation: fadeInOut 1.5s ease;
        `;

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 1500);
    }

    updateGestureMapping() {
        console.log(`
        ╔══════════════════════════════════════════════╗
        ║          GESTURE CONTROL MAPPING            ║
        ╠══════════════════════════════════════════════╣
        ║ HAND → DECK MAPPING:                        ║
        ║ • Left Hand  → Controls Deck A              ║
        ║ • Right Hand → Controls Deck B              ║
        ║                                              ║
        ║ SINGLE HAND CONTROLS:                       ║
        ║ • Closed Fist    → Play/Pause Deck          ║
        ║ • Pinch          → Load Track                ║
        ║ • Pointer        → Sync Deck                 ║
        ║ • Two Fingers    → Stop Deck                 ║
        ║ • Open Palm      → Swipe for modes          ║
        ║                                              ║
        ║ TWO HAND COMBINATIONS:                      ║
        ║ • Both Open      → Neutral/Browse           ║
        ║ • L-Fist + R-Pinch  → FX Filter            ║
        ║ • L-Fist + R-Pointer → FX Mix              ║
        ║ • R-Fist + L-Pinch  → Loop Length          ║
        ║ • R-Fist + L-Pointer → Loop Position       ║
        ║ • Any + Two Fingers  → Stop All            ║
        ║                                              ║
        ║ MODE SWITCHING:                             ║
        ║ • Swipe Left/Right with Open Palm          ║
        ║ • Single hand swipe = easy                  ║
        ║ • Two hands = needs bigger swipe            ║
        ╚══════════════════════════════════════════════╝
        `);
    }

    // Removed cursor-related methods
    clearAllHovers() {
        // No longer needed - no cursor system
    }
}

// Add animations and styles
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateX(-50%) translateY(20px); }
        20% { opacity: 1; transform: translateX(-50%) translateY(0); }
        80% { opacity: 1; transform: translateX(-50%) translateY(0); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-20px); }
    }

    @keyframes swipeAnimation {
        0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
        }
        50% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1.2);
        }
        100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.5);
        }
    }

    .mode-info {
        text-align: center;
        color: #888;
    }

    .mode-info h4 {
        color: #b19aff;
        margin-bottom: 10px;
    }

    .mode-info p {
        margin: 5px 0;
        font-size: 0.85rem;
    }

    .state-browsing { color: #666; }
    .state-controlling { color: #b19aff; }
    .state-active { color: #888; }
`;
document.head.appendChild(style);

// Export for use in main.js
window.GestureUI = GestureUI;