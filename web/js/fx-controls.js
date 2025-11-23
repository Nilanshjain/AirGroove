/**
 * FX Controls Manager
 * Handles UI interactions for audio effects controls
 */

class FXControlsManager {
    constructor() {
        this.currentFilterType = 'lowpass';
        this.filterEnabled = false;
        this.cutoffFrequency = 1000;
        this.resonance = 1.0;
        this.wetDryMix = 0.5;

        // UI elements
        this.fxPanel = null;
        this.enableBtn = null;
        this.cutoffSlider = null;
        this.resonanceSlider = null;
        this.wetDrySlider = null;
        this.frequencyGraph = null;

        console.log('[FX Controls] Initialized');
    }

    init() {
        // Get UI elements
        this.fxPanel = document.getElementById('fx-controls-panel');
        this.enableBtn = document.getElementById('fx-enable-btn');
        this.cutoffSlider = document.getElementById('fx-cutoff-slider');
        this.resonanceSlider = document.getElementById('fx-resonance-slider');
        this.wetDrySlider = document.getElementById('fx-wetdry-slider');
        this.frequencyGraph = document.getElementById('fx-frequency-graph');

        if (!this.fxPanel) {
            console.warn('[FX Controls] FX panel not found');
            return;
        }

        // Set up event listeners
        this.setupEventListeners();

        // Draw initial frequency response graph
        this.drawFrequencyGraph();

        console.log('[FX Controls] Initialized UI');
    }

    setupEventListeners() {
        // Enable/Disable button
        if (this.enableBtn) {
            this.enableBtn.addEventListener('click', () => {
                this.toggleFilter();
            });
        }

        // Filter type buttons
        const filterTypeBtns = document.querySelectorAll('.filter-type-btn');
        filterTypeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filterType = e.currentTarget.dataset.filterType;
                this.setFilterType(filterType);
            });
        });

        // Cutoff frequency slider
        if (this.cutoffSlider) {
            this.cutoffSlider.addEventListener('input', (e) => {
                this.cutoffFrequency = parseFloat(e.target.value);
                this.updateCutoffDisplay();
                this.sendFXParameter('cutoff', this.cutoffFrequency);
                this.drawFrequencyGraph();
            });
        }

        // Resonance slider
        if (this.resonanceSlider) {
            this.resonanceSlider.addEventListener('input', (e) => {
                this.resonance = parseFloat(e.target.value);
                this.updateResonanceDisplay();
                this.sendFXParameter('resonance', this.resonance);
                this.drawFrequencyGraph();
            });
        }

        // Wet/Dry mix slider
        if (this.wetDrySlider) {
            this.wetDrySlider.addEventListener('input', (e) => {
                const percentage = parseInt(e.target.value);
                this.wetDryMix = percentage / 100;
                this.updateWetDryDisplay();
                this.sendFXParameter('wet_dry', this.wetDryMix);
            });
        }
    }

    toggleFilter() {
        this.filterEnabled = !this.filterEnabled;

        // Update button appearance
        if (this.filterEnabled) {
            this.enableBtn.classList.add('active');
            document.getElementById('fx-enable-text').textContent = 'DISABLE FILTER';
        } else {
            this.enableBtn.classList.remove('active');
            document.getElementById('fx-enable-text').textContent = 'ENABLE FILTER';
        }

        // Send to backend
        this.sendFXParameter('enable', this.filterEnabled ? 1.0 : 0.0);

        console.log(`[FX Controls] Filter ${this.filterEnabled ? 'enabled' : 'disabled'}`);
    }

    setFilterType(filterType) {
        this.currentFilterType = filterType;

        // Update button states
        const filterTypeBtns = document.querySelectorAll('.filter-type-btn');
        filterTypeBtns.forEach(btn => {
            if (btn.dataset.filterType === filterType) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Send to backend
        this.sendFXParameter('filter_type', filterType);

        // Redraw frequency graph
        this.drawFrequencyGraph();

        console.log(`[FX Controls] Filter type: ${filterType}`);
    }

    updateCutoffDisplay() {
        const cutoffValue = document.getElementById('fx-cutoff-value');
        if (cutoffValue) {
            // Format frequency display (use kHz for values >= 1000)
            if (this.cutoffFrequency >= 1000) {
                cutoffValue.textContent = (this.cutoffFrequency / 1000).toFixed(1) + 'k';
            } else {
                cutoffValue.textContent = Math.round(this.cutoffFrequency);
            }
        }
    }

    updateResonanceDisplay() {
        const resonanceValue = document.getElementById('fx-resonance-value');
        if (resonanceValue) {
            resonanceValue.textContent = this.resonance.toFixed(1);
        }
    }

    updateWetDryDisplay() {
        const wetDryValue = document.getElementById('fx-wetdry-value');
        if (wetDryValue) {
            wetDryValue.textContent = Math.round(this.wetDryMix * 100);
        }
    }

    sendFXParameter(parameter, value) {
        // Send FX parameter change via WebSocket
        if (window.wsClient && window.wsClient.ws && window.wsClient.ws.readyState === WebSocket.OPEN) {
            const message = {
                type: 'fx_control',
                payload: {
                    parameter: parameter,
                    value: value
                }
            };
            window.wsClient.ws.send(JSON.stringify(message));
            console.log(`[FX Controls] Sent ${parameter}: ${value}`);
        } else {
            console.warn('[FX Controls] WebSocket not connected');
        }
    }

    drawFrequencyGraph() {
        if (!this.frequencyGraph) return;

        const ctx = this.frequencyGraph.getContext('2d');
        const width = this.frequencyGraph.width;
        const height = this.frequencyGraph.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(0, 0, width, height);

        // Draw grid
        ctx.strokeStyle = 'rgba(124, 58, 237, 0.2)';
        ctx.lineWidth = 1;

        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Draw frequency response curve
        ctx.strokeStyle = this.filterEnabled ? '#7c3aed' : '#666';
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (let x = 0; x < width; x++) {
            // Map x position to frequency (20Hz - 20kHz, logarithmic)
            const freq = 20 * Math.pow(1000, x / width);

            // Calculate filter response
            let response = this.calculateFilterResponse(freq);

            // Map response to y position (0 = top, 1 = bottom)
            const y = height - (response * height);

            if (x === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();

        // Draw cutoff frequency indicator
        const cutoffX = width * (Math.log(this.cutoffFrequency / 20) / Math.log(1000));
        ctx.strokeStyle = '#00ff88';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(cutoffX, 0);
        ctx.lineTo(cutoffX, height);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label
        ctx.fillStyle = '#00ff88';
        ctx.font = '10px Arial';
        ctx.fillText(`${Math.round(this.cutoffFrequency)}Hz`, cutoffX + 5, 15);
    }

    calculateFilterResponse(freq) {
        // Simplified filter response calculation
        const normalizedFreq = freq / this.cutoffFrequency;
        let response = 0.5;

        if (this.currentFilterType === 'lowpass') {
            response = 1 / (1 + Math.pow(normalizedFreq * this.resonance, 2));
        } else if (this.currentFilterType === 'highpass') {
            response = Math.pow(normalizedFreq * this.resonance, 2) / (1 + Math.pow(normalizedFreq * this.resonance, 2));
        } else if (this.currentFilterType === 'bandpass') {
            const distance = Math.abs(Math.log(normalizedFreq));
            response = Math.exp(-distance * this.resonance);
        }

        return response;
    }

    show() {
        if (this.fxPanel) {
            this.fxPanel.style.display = 'block';
            this.drawFrequencyGraph();
            console.log('[FX Controls] Panel shown');
        }
    }

    hide() {
        if (this.fxPanel) {
            this.fxPanel.style.display = 'none';
            console.log('[FX Controls] Panel hidden');
        }
    }

    updateFromBackend(fxState) {
        if (!fxState) return;

        // Update internal state
        if (fxState.filter_enabled !== undefined) {
            this.filterEnabled = fxState.filter_enabled;

            // Update enable button
            if (this.filterEnabled) {
                this.enableBtn?.classList.add('active');
                const enableText = document.getElementById('fx-enable-text');
                if (enableText) enableText.textContent = 'DISABLE FILTER';
            } else {
                this.enableBtn?.classList.remove('active');
                const enableText = document.getElementById('fx-enable-text');
                if (enableText) enableText.textContent = 'ENABLE FILTER';
            }
        }

        if (fxState.filter_type && fxState.filter_type !== this.currentFilterType) {
            this.setFilterType(fxState.filter_type);
        }

        if (fxState.filter_cutoff && Math.abs(fxState.filter_cutoff - this.cutoffFrequency) > 10) {
            this.cutoffFrequency = fxState.filter_cutoff;
            if (this.cutoffSlider) this.cutoffSlider.value = this.cutoffFrequency;
            this.updateCutoffDisplay();
        }

        if (fxState.filter_resonance && Math.abs(fxState.filter_resonance - this.resonance) > 0.1) {
            this.resonance = fxState.filter_resonance;
            if (this.resonanceSlider) this.resonanceSlider.value = this.resonance;
            this.updateResonanceDisplay();
        }

        if (fxState.wet_dry_mix !== undefined && Math.abs(fxState.wet_dry_mix - this.wetDryMix) > 0.01) {
            this.wetDryMix = fxState.wet_dry_mix;
            if (this.wetDrySlider) this.wetDrySlider.value = Math.round(this.wetDryMix * 100);
            this.updateWetDryDisplay();
        }

        // Redraw graph
        this.drawFrequencyGraph();
    }
}

// Initialize FX controls when DOM is ready
let fxControls = null;

document.addEventListener('DOMContentLoaded', () => {
    fxControls = new FXControlsManager();
    fxControls.init();
    window.fxControls = fxControls;
    console.log('[FX Controls] Ready');
});
