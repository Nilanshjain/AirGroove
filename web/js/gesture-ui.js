/**
 * Gesture-based UI interaction system
 * Handles gesture pointer, hover detection, and mode selection
 */

class GestureUI {
    constructor() {
        this.gesturePointer = document.getElementById('gesture-pointer');
        console.log('GestureUI initialized, pointer element:', this.gesturePointer);
        this.currentMode = null;
        this.isSelecting = false;
        this.hoverTimeout = null;
        this.selectionTimeout = null;

        // UI elements
        this.modeButtons = document.querySelectorAll('.mode-btn');
        this.currentModeDisplay = document.getElementById('current-mode');

        // Gesture state
        this.leftGesture = 'none';
        this.rightGesture = 'none';
        this.interactionState = 'browsing';
        this.leftPosition = { x: 0, y: 0 };
        this.rightPosition = { x: 0, y: 0 };

        // Make mode buttons hoverable
        this.modeButtons.forEach(btn => {
            btn.classList.add('hoverable');
        });

        // Make gesture buttons hoverable
        this.gestureButtons = document.querySelectorAll('.gesture-button');
        this.gestureButtons.forEach(btn => {
            btn.classList.add('hoverable');
        });

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Handle window resize for coordinate mapping
        window.addEventListener('resize', () => {
            this.updatePointerPosition();
        });
    }

    updateGestureState(gestureData) {
        // Update gesture data
        this.leftGesture = gestureData.left_hand.gesture;
        this.rightGesture = gestureData.right_hand.gesture;
        this.interactionState = gestureData.interaction_state;
        this.leftPosition = gestureData.left_hand.position;
        this.rightPosition = gestureData.right_hand.position;

        // Update UI displays
        this.updateGestureDisplays(gestureData);
        this.updatePointerPosition();
        this.handleInteractionState();
    }

    updateGestureDisplays(gestureData) {
        // Update left hand display
        const leftGestureEl = document.getElementById('left-gesture');
        const leftConfidenceEl = document.getElementById('left-confidence');

        if (leftGestureEl) {
            leftGestureEl.textContent = this.leftGesture;
            leftGestureEl.className = `gesture-display gesture-${this.leftGesture}`;
        }

        if (leftConfidenceEl) {
            const confidence = gestureData.left_hand.confidence * 100;
            leftConfidenceEl.style.width = `${confidence}%`;
            leftConfidenceEl.className = `confidence-fill ${this.getConfidenceClass(confidence)}`;
        }

        // Update right hand display
        const rightGestureEl = document.getElementById('right-gesture');
        const rightConfidenceEl = document.getElementById('right-confidence');

        if (rightGestureEl) {
            rightGestureEl.textContent = this.rightGesture;
            rightGestureEl.className = `gesture-display gesture-${this.rightGesture}`;
        }

        if (rightConfidenceEl) {
            const confidence = gestureData.right_hand.confidence * 100;
            rightConfidenceEl.style.width = `${confidence}%`;
            rightConfidenceEl.className = `confidence-fill ${this.getConfidenceClass(confidence)}`;
        }

        // Update interaction state
        const interactionEl = document.getElementById('interaction-state');
        if (interactionEl) {
            interactionEl.textContent = this.interactionState.replace(/_/g, ' ');
            interactionEl.className = `interaction-state gesture-state-${this.getStateClass()}`;
        }
    }

    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'confidence-high';
        if (confidence >= 50) return 'confidence-medium';
        return 'confidence-low';
    }

    getStateClass() {
        if (this.interactionState === 'browsing') return 'browsing';
        if (this.interactionState.includes('selecting')) return 'selecting';
        if (this.interactionState.includes('controlling')) return 'controlling';
        return 'unknown';
    }

    updatePointerPosition() {
        if (!this.gesturePointer) {
            console.warn('Gesture pointer element not found!');
            return;
        }

        let activePosition;
        let activeGesture;

        // Show cursor for ANY detected hand - prioritize right hand, then left
        // Use hand position data regardless of gesture type
        if (this.rightPosition && this.rightPosition.x >= 0 && this.rightPosition.y >= 0) {
            activePosition = this.rightPosition;
            activeGesture = this.rightGesture;
        } else if (this.leftPosition && this.leftPosition.x >= 0 && this.leftPosition.y >= 0) {
            activePosition = this.leftPosition;
            activeGesture = this.leftGesture;
        }

        // Default to open_palm for any unknown or none gestures
        if (activeGesture === 'none' || !activeGesture || activeGesture === 'unknown') {
            activeGesture = 'open_palm';
        }

        console.log('Cursor Debug:', {
            leftGesture: this.leftGesture,
            rightGesture: this.rightGesture,
            leftPosition: this.leftPosition,
            rightPosition: this.rightPosition,
            activePosition: activePosition,
            activeGesture: activeGesture
        });

        if (activePosition && activePosition.x >= 0 && activePosition.y >= 0) {
            // Convert normalized coordinates to screen coordinates
            const x = activePosition.x * window.innerWidth;
            const y = activePosition.y * window.innerHeight;

            console.log('Setting cursor position:', { x, y, gesture: activeGesture });

            this.gesturePointer.style.left = `${x}px`;
            this.gesturePointer.style.top = `${y}px`;
            // Apply gesture class for cursor styling - always show as active
            this.gesturePointer.className = `gesture-pointer active ${activeGesture}`;

            // Check for hover over UI elements
            this.checkHoverElements(x, y);
        } else {
            console.log('No active position, hiding cursor');
            this.gesturePointer.classList.remove('active');
            this.clearAllHovers();
        }
    }

    checkHoverElements(x, y) {
        // Get element at pointer position
        const element = document.elementFromPoint(x, y);

        if (element) {
            // Check if it's a hoverable element
            const hoverable = element.closest('.hoverable');

            if (hoverable) {
                this.handleHover(hoverable);
            } else {
                this.clearAllHovers();
            }
        }
    }

    handleHover(element) {
        // Clear previous hovers
        this.clearAllHovers();

        // Add hover class
        element.classList.add('hovered');

        // Handle mode button hover
        if (element.classList.contains('mode-btn')) {
            this.handleModeButtonHover(element);
        }

        // Handle gesture button hover
        if (element.classList.contains('gesture-button')) {
            this.handleGestureButtonHover(element);
        }
    }

    handleModeButtonHover(button) {
        const mode = button.dataset.mode;

        // If user makes a fist while hovering, select the mode
        if (this.leftGesture === 'closed_fist' || this.rightGesture === 'closed_fist') {
            this.selectMode(mode, button);
        }
    }

    handleGestureButtonHover(button) {
        const requiredGesture = button.dataset.gesture;
        const action = button.dataset.action;
        const deck = button.dataset.deck;

        // Show visual feedback for the expected gesture
        button.classList.add('gesture-ready');

        // Check if the user is making the correct gesture
        if (this.leftGesture === requiredGesture || this.rightGesture === requiredGesture) {
            button.classList.add('gesture-match');

            // Send quick gesture feedback
            this.showQuickGestureFeedback(`${requiredGesture} detected over ${action} ${deck}`, 'success');
        } else {
            button.classList.remove('gesture-match');
        }
    }

    showQuickGestureFeedback(message, type = 'info') {
        const feedbackEl = document.getElementById('quick-gesture-feedback');
        if (feedbackEl) {
            feedbackEl.textContent = message;
            feedbackEl.className = `quick-gesture-feedback ${type}`;

            // Clear after 2 seconds
            setTimeout(() => {
                feedbackEl.textContent = '';
                feedbackEl.className = 'quick-gesture-feedback';
            }, 2000);
        }
    }

    selectMode(mode, button) {
        if (this.currentMode === mode) return;

        // Clear previous selection
        this.modeButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Activate new mode
        button.classList.add('active');
        button.classList.add('selecting-feedback');

        // Remove feedback class after animation
        setTimeout(() => {
            button.classList.remove('selecting-feedback');
        }, 800);

        this.currentMode = mode;

        // Update display
        if (this.currentModeDisplay) {
            this.currentModeDisplay.textContent = this.getModeDisplayName(mode);
        }

        // Update body class for mode-specific styling
        document.body.className = `mode-${mode}-active`;

        // Send mode selection to backend
        if (window.wsClient) {
            window.wsClient.sendModeSelection(mode);
        }

        // Update mode controls
        this.updateModeControls(mode);

        console.log(`Mode selected: ${mode}`);
    }

    getModeDisplayName(mode) {
        const names = {
            'fx': 'Control FX',
            'loop': 'Loop',
            'scratch': 'Scratch'
        };
        return names[mode] || mode;
    }

    updateModeControls(mode) {
        const modeControlsEl = document.getElementById('mode-controls');
        if (!modeControlsEl) return;

        // Clear existing controls
        modeControlsEl.innerHTML = '';

        // Add mode-specific controls
        switch (mode) {
            case 'fx':
                this.createFXControls(modeControlsEl);
                break;
            case 'loop':
                this.createLoopControls(modeControlsEl);
                break;
            case 'scratch':
                this.createScratchControls(modeControlsEl);
                break;
        }
    }

    createFXControls(container) {
        container.innerHTML = `
            <div class="fx-controls">
                <h3>Control FX</h3>
                <div class="fx-parameter">
                    <label>Filter</label>
                    <div class="parameter-control" id="fx-filter">
                        <div class="parameter-value" id="fx-filter-value">50%</div>
                    </div>
                </div>
                <div class="fx-parameter">
                    <label>Reverb</label>
                    <div class="parameter-control" id="fx-reverb">
                        <div class="parameter-value" id="fx-reverb-value">0%</div>
                    </div>
                </div>
                <div class="fx-parameter">
                    <label>Delay</label>
                    <div class="parameter-control" id="fx-delay">
                        <div class="parameter-value" id="fx-delay-value">0%</div>
                    </div>
                </div>
                <div class="gesture-instructions">
                    <p>🤏 Pinch: Filter Control</p>
                    <p>👉 Point: Effect Mix</p>
                    <p>✌️ Two Fingers: Reverb + Delay</p>
                </div>
            </div>
        `;
    }

    createLoopControls(container) {
        container.innerHTML = `
            <div class="loop-controls">
                <h3>Loop Control</h3>
                <div class="loop-parameter">
                    <label>Loop Length</label>
                    <div class="parameter-control" id="loop-length">
                        <div class="parameter-value" id="loop-length-value">4 beats</div>
                    </div>
                </div>
                <div class="loop-parameter">
                    <label>Loop Position</label>
                    <div class="parameter-control" id="loop-position">
                        <div class="parameter-value" id="loop-position-value">0.0s</div>
                    </div>
                </div>
                <div class="loop-status">
                    <span id="loop-active-status">Loop: Inactive</span>
                </div>
                <div class="gesture-instructions">
                    <p>🤏 Pinch: Loop Length</p>
                    <p>👉 Point: Set In/Out Points</p>
                    <p>✌️ Two Fingers: Loop Roll</p>
                </div>
            </div>
        `;
    }

    createScratchControls(container) {
        container.innerHTML = `
            <div class="scratch-controls">
                <h3>Scratch Control</h3>
                <div class="scratch-parameter">
                    <label>Scratch Speed</label>
                    <div class="parameter-control" id="scratch-speed">
                        <div class="parameter-value" id="scratch-speed-value">0.0</div>
                    </div>
                </div>
                <div class="scratch-parameter">
                    <label>Pitch Bend</label>
                    <div class="parameter-control" id="pitch-bend">
                        <div class="parameter-value" id="pitch-bend-value">0%</div>
                    </div>
                </div>
                <div class="turntable-visual">
                    <div class="turntable" id="turntable">
                        <div class="turntable-center"></div>
                    </div>
                </div>
                <div class="gesture-instructions">
                    <p>🤏 Pinch: Pitch Bend</p>
                    <p>👉 Point: Scratch Direction</p>
                    <p>✌️ Two Fingers: Crossfader</p>
                </div>
            </div>
        `;
    }

    handleInteractionState() {
        // Handle different interaction states
        switch (this.interactionState) {
            case 'browsing':
                this.clearAllHovers();
                break;

            case 'selecting_with_left':
            case 'selecting_with_right':
                // Mode selection active
                break;

            case 'controlling_with_left_pinch':
            case 'controlling_with_right_pinch':
                this.handlePinchControl();
                break;

            case 'controlling_with_left_pointer':
            case 'controlling_with_right_pointer':
                this.handlePointerControl();
                break;

            case 'controlling_with_left_two_fingers':
            case 'controlling_with_right_two_fingers':
                this.handleTwoFingerControl();
                break;
        }
    }

    handlePinchControl() {
        if (!this.currentMode) return;

        // Get controlling hand position
        const controllingHand = this.interactionState.includes('left') ? 'left' : 'right';
        const position = controllingHand === 'left' ? this.leftPosition : this.rightPosition;

        // Map position to parameter based on mode
        switch (this.currentMode) {
            case 'fx':
                this.updateFXParameter('filter', position.y);
                break;
            case 'loop':
                this.updateLoopParameter('length', position.x);
                break;
            case 'scratch':
                this.updateScratchParameter('pitch', position.y);
                break;
        }
    }

    handlePointerControl() {
        if (!this.currentMode) return;

        const controllingHand = this.interactionState.includes('left') ? 'left' : 'right';
        const position = controllingHand === 'left' ? this.leftPosition : this.rightPosition;

        switch (this.currentMode) {
            case 'fx':
                this.updateFXParameter('mix', position.x);
                break;
            case 'loop':
                this.updateLoopParameter('position', position.x);
                break;
            case 'scratch':
                this.updateScratchParameter('speed', position.x - 0.5);
                break;
        }
    }

    handleTwoFingerControl() {
        if (!this.currentMode) return;

        const controllingHand = this.interactionState.includes('left') ? 'left' : 'right';
        const position = controllingHand === 'left' ? this.leftPosition : this.rightPosition;

        switch (this.currentMode) {
            case 'fx':
                this.updateFXParameter('reverb', position.x);
                this.updateFXParameter('delay', position.y);
                break;
            case 'loop':
                this.updateLoopParameter('roll', position.y);
                break;
            case 'scratch':
                this.updateCrossfader(position.x);
                break;
        }
    }

    updateFXParameter(param, value) {
        const paramEl = document.getElementById(`fx-${param}-value`);
        if (paramEl) {
            const percentage = Math.round(value * 100);
            paramEl.textContent = `${percentage}%`;
        }

        // Send to backend
        if (window.wsClient) {
            window.wsClient.sendAudioControl('fx_control', {
                parameter: param,
                value: value
            });
        }
    }

    updateLoopParameter(param, value) {
        const paramEl = document.getElementById(`loop-${param}-value`);
        if (paramEl) {
            if (param === 'length') {
                const beats = Math.max(1, Math.round(value * 16));
                paramEl.textContent = `${beats} beats`;
            } else if (param === 'position') {
                paramEl.textContent = `${(value * 10).toFixed(1)}s`;
            }
        }

        // Send to backend
        if (window.wsClient) {
            window.wsClient.sendAudioControl('loop_control', {
                parameter: param,
                value: value
            });
        }
    }

    updateScratchParameter(param, value) {
        const paramEl = document.getElementById(`${param === 'speed' ? 'scratch-speed' : 'pitch-bend'}-value`);
        if (paramEl) {
            if (param === 'speed') {
                paramEl.textContent = value.toFixed(2);
            } else {
                paramEl.textContent = `${Math.round(value * 100)}%`;
            }
        }

        // Rotate turntable visual
        if (param === 'speed') {
            const turntable = document.getElementById('turntable');
            if (turntable) {
                const rotation = value * 360;
                turntable.style.transform = `rotate(${rotation}deg)`;
            }
        }

        // Send to backend
        if (window.wsClient) {
            window.wsClient.sendAudioControl('scratch_control', {
                parameter: param,
                value: value
            });
        }
    }

    updateCrossfader(value) {
        const crossfader = document.getElementById('crossfader');
        if (crossfader) {
            const percentage = value * 100;
            crossfader.style.left = `${percentage}%`;
        }

        // Send to backend
        if (window.wsClient) {
            window.wsClient.sendAudioControl('crossfader', {
                position: value
            });
        }
    }

    clearAllHovers() {
        document.querySelectorAll('.hovered').forEach(el => {
            el.classList.remove('hovered');
        });

        // Clear gesture button states
        document.querySelectorAll('.gesture-button').forEach(btn => {
            btn.classList.remove('gesture-ready', 'gesture-match');
        });
    }
}

// Export for use in main.js
window.GestureUI = GestureUI;