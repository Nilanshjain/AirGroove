/**
 * Loop Controls Manager
 * Handles UI interactions for loop controls
 */

class LoopControlsManager {
    constructor() {
        this.loopEnabled = false;
        this.loopLength = 4; // beats
        this.loopInPoint = null; // seconds
        this.loopOutPoint = null; // seconds
        this.loopPosition = 0; // normalized 0-1
        this.currentBPM = 120;
        this.isRolling = false;

        // UI elements
        this.loopPanel = null;
        this.enableBtn = null;
        this.positionSlider = null;
        this.loopVisualization = null;

        console.log('[Loop Controls] Initialized');
    }

    init() {
        // Get UI elements
        this.loopPanel = document.getElementById('loop-controls-panel');
        this.enableBtn = document.getElementById('loop-enable-btn');
        this.positionSlider = document.getElementById('loop-position-slider');
        this.loopVisualization = document.getElementById('loop-visualization');

        if (!this.loopPanel) {
            console.warn('[Loop Controls] Loop panel not found');
            return;
        }

        // Set up event listeners
        this.setupEventListeners();

        // Draw initial visualization
        this.drawLoopVisualization();

        console.log('[Loop Controls] Initialized UI');
    }

    setupEventListeners() {
        // Enable/Disable loop button
        if (this.enableBtn) {
            this.enableBtn.addEventListener('click', () => {
                this.toggleLoop();
            });
        }

        // Loop length buttons
        const lengthBtns = document.querySelectorAll('.loop-length-btn');
        lengthBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const length = parseFloat(e.currentTarget.dataset.length);
                this.setLoopLength(length);
            });
        });

        // Loop position slider
        if (this.positionSlider) {
            this.positionSlider.addEventListener('input', (e) => {
                this.loopPosition = parseFloat(e.target.value) / 100;
                this.updateLoopPositionDisplay();
                this.sendLoopParameter('position', this.loopPosition);
                this.drawLoopVisualization();
            });
        }

        // Set In/Out point buttons
        const setInBtn = document.getElementById('loop-in-btn');
        if (setInBtn) {
            setInBtn.addEventListener('click', () => {
                this.setLoopInPoint();
            });
        }

        const setOutBtn = document.getElementById('loop-out-btn');
        if (setOutBtn) {
            setOutBtn.addEventListener('click', () => {
                this.setLoopOutPoint();
            });
        }

        // Quick action buttons
        const loopRollBtn = document.getElementById('loop-roll-btn');
        if (loopRollBtn) {
            loopRollBtn.addEventListener('click', () => {
                this.loopRoll();
            });
        }

        const loopDoubleBtn = document.getElementById('loop-double-btn');
        if (loopDoubleBtn) {
            loopDoubleBtn.addEventListener('click', () => {
                this.doubleLoop();
            });
        }

        const loopHalfBtn = document.getElementById('loop-half-btn');
        if (loopHalfBtn) {
            loopHalfBtn.addEventListener('click', () => {
                this.halveLoop();
            });
        }
    }

    toggleLoop() {
        this.loopEnabled = !this.loopEnabled;

        // Update button appearance
        if (this.loopEnabled) {
            this.enableBtn.classList.add('active');
            document.getElementById('loop-enable-text').textContent = 'DEACTIVATE LOOP';
            document.getElementById('loop-enable-indicator').classList.add('active');
        } else {
            this.enableBtn.classList.remove('active');
            document.getElementById('loop-enable-text').textContent = 'ACTIVATE LOOP';
            document.getElementById('loop-enable-indicator').classList.remove('active');
        }

        // Send to backend
        this.sendLoopParameter('enable', this.loopEnabled ? 1.0 : 0.0);

        // Redraw visualization
        this.drawLoopVisualization();

        console.log(`[Loop Controls] Loop ${this.loopEnabled ? 'enabled' : 'disabled'}`);
    }

    setLoopLength(length) {
        this.loopLength = length;

        // Update button states
        const lengthBtns = document.querySelectorAll('.loop-length-btn');
        lengthBtns.forEach(btn => {
            if (parseFloat(btn.dataset.length) === length) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Send to backend
        this.sendLoopParameter('length', length);

        // Update visualization
        this.drawLoopVisualization();

        console.log(`[Loop Controls] Loop length: ${length} beats`);
    }

    setLoopInPoint() {
        // Request current playback position from backend
        this.sendLoopAction('set_in');

        // Visual feedback
        const setInBtn = document.getElementById('loop-in-btn');
        if (setInBtn) {
            setInBtn.classList.add('active');
            setTimeout(() => setInBtn.classList.remove('active'), 200);
        }

        console.log('[Loop Controls] Set loop IN point');
    }

    setLoopOutPoint() {
        // Request current playback position from backend
        this.sendLoopAction('set_out');

        // Visual feedback
        const setOutBtn = document.getElementById('loop-out-btn');
        if (setOutBtn) {
            setOutBtn.classList.add('active');
            setTimeout(() => setOutBtn.classList.remove('active'), 200);
        }

        console.log('[Loop Controls] Set loop OUT point');
    }

    loopRoll() {
        this.isRolling = !this.isRolling;

        // Send to backend
        this.sendLoopAction('roll', { active: this.isRolling });

        // Visual feedback
        const loopRollBtn = document.getElementById('loop-roll-btn');
        if (loopRollBtn) {
            if (this.isRolling) {
                loopRollBtn.classList.add('active');
            } else {
                loopRollBtn.classList.remove('active');
            }
        }

        console.log(`[Loop Controls] Loop roll ${this.isRolling ? 'activated' : 'deactivated'}`);
    }

    doubleLoop() {
        // Double the loop length
        const newLength = Math.min(this.loopLength * 2, 32);
        this.setLoopLength(newLength);

        // Visual feedback
        const loopDoubleBtn = document.getElementById('loop-double-btn');
        if (loopDoubleBtn) {
            loopDoubleBtn.classList.add('active');
            setTimeout(() => loopDoubleBtn.classList.remove('active'), 200);
        }

        console.log(`[Loop Controls] Loop doubled to ${newLength} beats`);
    }

    halveLoop() {
        // Halve the loop length
        const newLength = Math.max(this.loopLength / 2, 0.25);
        this.setLoopLength(newLength);

        // Visual feedback
        const loopHalfBtn = document.getElementById('loop-half-btn');
        if (loopHalfBtn) {
            loopHalfBtn.classList.add('active');
            setTimeout(() => loopHalfBtn.classList.remove('active'), 200);
        }

        console.log(`[Loop Controls] Loop halved to ${newLength} beats`);
    }

    updateLoopPositionDisplay() {
        const positionValue = document.getElementById('loop-position-value');
        if (positionValue) {
            positionValue.textContent = Math.round(this.loopPosition * 100);
        }
    }

    updateLoopPointDisplay(inPoint, outPoint) {
        const inValue = document.getElementById('loop-in-value');
        const outValue = document.getElementById('loop-out-value');

        if (inValue && inPoint !== null) {
            inValue.textContent = this.formatTime(inPoint);
        }

        if (outValue && outPoint !== null) {
            outValue.textContent = this.formatTime(outPoint);
        }
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 100);
        return `${minutes}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
    }

    sendLoopParameter(parameter, value) {
        // Send loop parameter change via WebSocket
        if (window.wsClient && window.wsClient.ws && window.wsClient.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'loop_control',
                payload: {
                    parameter: parameter,
                    value: value
                }
            };
            window.wsClient.ws.send(JSON.stringify(message));
            console.log(`[Loop Controls] Sent ${parameter}: ${value}`);
        } else {
            console.warn('[Loop Controls] WebSocket not connected');
        }
    }

    sendLoopAction(action, data = {}) {
        // Send loop action via WebSocket
        if (window.wsClient && window.wsClient.ws && window.wsClient.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'loop_control',
                payload: {
                    action: action,
                    ...data
                }
            };
            window.wsClient.ws.send(JSON.stringify(message));
            console.log(`[Loop Controls] Action: ${action}`, data);
        } else {
            console.warn('[Loop Controls] WebSocket not connected');
        }
    }

    drawLoopVisualization() {
        if (!this.loopVisualization) return;

        const ctx = this.loopVisualization.getContext('2d');
        const width = this.loopVisualization.width;
        const height = this.loopVisualization.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(0, 0, width, height);

        // Draw loop region
        if (this.loopEnabled) {
            // Loop active region (green)
            const loopWidth = width * (this.loopLength / 32); // Normalize to max 32 beats
            const loopX = this.loopPosition * (width - loopWidth);

            ctx.fillStyle = 'rgba(0, 255, 136, 0.3)';
            ctx.fillRect(loopX, 0, loopWidth, height);

            // Loop boundaries
            ctx.strokeStyle = '#00ff88';
            ctx.lineWidth = 2;

            // IN point
            ctx.beginPath();
            ctx.moveTo(loopX, 0);
            ctx.lineTo(loopX, height);
            ctx.stroke();

            // OUT point
            ctx.beginPath();
            ctx.moveTo(loopX + loopWidth, 0);
            ctx.lineTo(loopX + loopWidth, height);
            ctx.stroke();

            // Labels
            ctx.fillStyle = '#00ff88';
            ctx.font = 'bold 10px Arial';
            ctx.fillText('IN', loopX + 5, 15);
            ctx.fillText('OUT', loopX + loopWidth - 25, 15);

            // Loop length label
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 12px Arial';
            const lengthText = this.loopLength >= 1 ? `${this.loopLength} BEATS` : `${this.loopLength * 4}/4 BEAT`;
            const textWidth = ctx.measureText(lengthText).width;
            ctx.fillText(lengthText, loopX + (loopWidth - textWidth) / 2, height / 2 + 5);
        } else {
            // Loop inactive - show grid
            ctx.strokeStyle = 'rgba(0, 255, 136, 0.2)';
            ctx.lineWidth = 1;

            // Draw beat markers
            for (let i = 0; i <= 8; i++) {
                const x = (width / 8) * i;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }

            // Inactive label
            ctx.fillStyle = '#666';
            ctx.font = 'bold 12px Arial';
            ctx.fillText('LOOP INACTIVE', width / 2 - 50, height / 2 + 5);
        }

        // Current playback position (if rolling)
        if (this.isRolling) {
            const playheadX = width / 2;
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(playheadX, 0);
            ctx.lineTo(playheadX, height);
            ctx.stroke();
        }
    }

    show() {
        if (this.loopPanel) {
            this.loopPanel.style.display = 'block';
            this.drawLoopVisualization();
            console.log('[Loop Controls] Panel shown');
        }
    }

    hide() {
        if (this.loopPanel) {
            this.loopPanel.style.display = 'none';
            console.log('[Loop Controls] Panel hidden');
        }
    }

    updateFromBackend(loopState) {
        if (!loopState) return;

        // Update internal state
        if (loopState.loop_enabled !== undefined) {
            this.loopEnabled = loopState.loop_enabled;

            // Update enable button
            if (this.loopEnabled) {
                this.enableBtn?.classList.add('active');
                const enableText = document.getElementById('loop-enable-text');
                if (enableText) enableText.textContent = 'DEACTIVATE LOOP';
                const indicator = document.getElementById('loop-enable-indicator');
                if (indicator) indicator.classList.add('active');
            } else {
                this.enableBtn?.classList.remove('active');
                const enableText = document.getElementById('loop-enable-text');
                if (enableText) enableText.textContent = 'ACTIVATE LOOP';
                const indicator = document.getElementById('loop-enable-indicator');
                if (indicator) indicator.classList.remove('active');
            }
        }

        if (loopState.loop_length !== undefined) {
            this.loopLength = loopState.loop_length;
            // Update button states
            const lengthBtns = document.querySelectorAll('.loop-length-btn');
            lengthBtns.forEach(btn => {
                if (parseFloat(btn.dataset.length) === this.loopLength) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        if (loopState.loop_in_point !== undefined) {
            this.loopInPoint = loopState.loop_in_point;
        }

        if (loopState.loop_out_point !== undefined) {
            this.loopOutPoint = loopState.loop_out_point;
        }

        if (loopState.loop_position !== undefined) {
            this.loopPosition = loopState.loop_position;
            if (this.positionSlider) {
                this.positionSlider.value = Math.round(this.loopPosition * 100);
            }
            this.updateLoopPositionDisplay();
        }

        if (loopState.bpm !== undefined) {
            this.currentBPM = loopState.bpm;
        }

        if (loopState.is_rolling !== undefined) {
            this.isRolling = loopState.is_rolling;
            const loopRollBtn = document.getElementById('loop-roll-btn');
            if (loopRollBtn) {
                if (this.isRolling) {
                    loopRollBtn.classList.add('active');
                } else {
                    loopRollBtn.classList.remove('active');
                }
            }
        }

        // Update loop point displays
        this.updateLoopPointDisplay(this.loopInPoint, this.loopOutPoint);

        // Redraw visualization
        this.drawLoopVisualization();
    }
}

// Initialize loop controls when DOM is ready
let loopControls = null;

document.addEventListener('DOMContentLoaded', () => {
    loopControls = new LoopControlsManager();
    loopControls.init();
    window.loopControls = loopControls;
    console.log('[Loop Controls] Ready');
});
