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

        // Add click-to-seek functionality
        this.setupClickHandlers();

        // Clear canvas initially
        this.clear();
    }

    setupClickHandlers() {
        // Hover effect variables
        this.hoverPosition = null;
        this.isHovering = false;

        // Click event for seeking
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // Mousemove for hover preview
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));

        // Mouseleave to clear hover
        this.canvas.addEventListener('mouseleave', () => this.handleMouseLeave());

        // Add cursor pointer style
        this.canvas.style.cursor = 'pointer';
    }

    handleClick(event) {
        if (this.duration <= 0) {
            console.warn('[Waveform] Cannot seek - no track loaded');
            return;
        }

        const rect = this.canvas.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickRatio = clickX / this.canvas.width;
        const seekTime = clickRatio * this.duration;

        console.log(`[Waveform ${this.deck}] Seeking to ${seekTime.toFixed(2)}s (${(clickRatio * 100).toFixed(1)}%)`);

        // Send seek command via WebSocket
        if (window.wsClient) {
            window.wsClient.sendAudioControl('seek', {
                deck: this.deck,
                position: seekTime
            });
        } else {
            console.warn('[Waveform] WebSocket client not available');
        }
    }

    handleMouseMove(event) {
        if (this.duration <= 0) {
            return;
        }

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const hoverRatio = mouseX / this.canvas.width;

        this.hoverPosition = hoverRatio;
        this.isHovering = true;
        this.draw();
    }

    handleMouseLeave() {
        this.isHovering = false;
        this.hoverPosition = null;
        this.draw();
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

        // Draw hover indicator
        if (this.isHovering && this.hoverPosition !== null) {
            const hoverX = this.hoverPosition * this.canvas.width;

            // Draw vertical line
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(hoverX, 0);
            this.ctx.lineTo(hoverX, this.canvas.height);
            this.ctx.stroke();

            // Draw time indicator
            const hoverTime = this.hoverPosition * this.duration;
            const timeText = this.formatTime(hoverTime);

            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            this.ctx.fillRect(hoverX - 30, 5, 60, 20);

            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            this.ctx.font = '11px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(timeText, hoverX, 15);
        }
    }

    formatTime(seconds) {
        if (!seconds || seconds === 0) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
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