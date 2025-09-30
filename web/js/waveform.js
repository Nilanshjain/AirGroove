/**
 * Waveform visualization for audio tracks
 */

class WaveformVisualizer {
    constructor(canvasId, deck) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.deck = deck;
        this.waveformData = [];
        this.isPlaying = false;
        this.position = 0;
        this.duration = 0;

        // Visual settings
        this.barWidth = 2;
        this.barGap = 1;
        this.barColor = 'rgba(124, 58, 237, 0.6)';
        this.playedColor = 'rgba(124, 58, 237, 0.9)';
        this.backgroundColor = 'rgba(0, 0, 0, 0.3)';

        this.init();
    }

    init() {
        // Set canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Clear canvas initially
        this.clear();
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();
        this.canvas.width = rect.width - 24; // Account for padding
        this.canvas.height = 120;
    }

    clear() {
        this.ctx.fillStyle = this.backgroundColor;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    setWaveformData(data) {
        this.waveformData = data || [];
        this.draw();
    }

    updatePosition(position, duration) {
        this.position = position;
        this.duration = duration;
        this.draw();
    }

    setPlaying(playing) {
        this.isPlaying = playing;
    }

    draw() {
        this.clear();

        if (this.waveformData.length === 0) {
            this.drawPlaceholder();
            return;
        }

        const barCount = Math.floor(this.canvas.width / (this.barWidth + this.barGap));
        const dataStep = Math.max(1, Math.floor(this.waveformData.length / barCount));

        const centerY = this.canvas.height / 2;
        const maxHeight = this.canvas.height * 0.8;

        // Calculate current position in bars
        const progressRatio = this.duration > 0 ? this.position / this.duration : 0;
        const progressBar = Math.floor(progressRatio * barCount);

        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.min(i * dataStep, this.waveformData.length - 1);
            const value = Math.abs(this.waveformData[dataIndex] || 0);
            const barHeight = Math.max(2, value * maxHeight);

            // Set color based on playback position
            if (i <= progressBar) {
                this.ctx.fillStyle = this.playedColor;
            } else {
                this.ctx.fillStyle = this.barColor;
            }

            const x = i * (this.barWidth + this.barGap);
            const y = centerY - barHeight / 2;

            // Draw the bar
            this.ctx.fillRect(x, y, this.barWidth, barHeight);
        }

        // Draw center line
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(0, centerY);
        this.ctx.lineTo(this.canvas.width, centerY);
        this.ctx.stroke();
    }

    drawPlaceholder() {
        const centerY = this.canvas.height / 2;

        // Draw placeholder bars
        const barCount = Math.floor(this.canvas.width / (this.barWidth + this.barGap));

        for (let i = 0; i < barCount; i++) {
            const x = i * (this.barWidth + this.barGap);
            const randomHeight = Math.random() * 20 + 5;

            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
            this.ctx.fillRect(x, centerY - randomHeight / 2, this.barWidth, randomHeight);
        }

        // Draw "No track loaded" text
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        this.ctx.font = '12px Inter, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('No waveform data', this.canvas.width / 2, centerY);
    }
}

// Initialize waveform visualizers for both decks
let waveformA = null;
let waveformB = null;

document.addEventListener('DOMContentLoaded', () => {
    waveformA = new WaveformVisualizer('waveform-a', 'a');
    waveformB = new WaveformVisualizer('waveform-b', 'b');

    // Make them globally accessible
    window.waveformA = waveformA;
    window.waveformB = waveformB;
});