/**
 * WebSocket client for real-time communication with gesture recognition backend
 */

class WebSocketClient {
    constructor(url = 'ws://localhost:8765') {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;

        // Event handlers
        this.onGestureUpdate = null;
        this.onAudioUpdate = null;
        this.onSystemUpdate = null;
        this.onConnectionChange = null;

        this.connect();
    }

    connect() {
        try {
            this.socket = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleReconnect();
        }
    }

    setupEventHandlers() {
        this.socket.onopen = () => {
            console.log('Connected to AirGroove backend');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');

            if (this.onConnectionChange) {
                this.onConnectionChange(true);
            }
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');

            if (this.onConnectionChange) {
                this.onConnectionChange(false);
            }

            if (!event.wasClean) {
                this.handleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnected = false;
            this.updateConnectionStatus('error');
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'gesture_update':
                if (this.onGestureUpdate) {
                    this.onGestureUpdate(data.payload);
                }
                break;

            case 'audio_update':
                if (this.onAudioUpdate) {
                    this.onAudioUpdate(data.payload);
                }
                break;

            case 'system_update':
                if (this.onSystemUpdate) {
                    this.onSystemUpdate(data.payload);
                }
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    send(type, payload) {
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            const message = {
                type: type,
                payload: payload,
                timestamp: Date.now()
            };

            try {
                this.socket.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('WebSocket not connected, message not sent:', type);
            return false;
        }
    }

    // Send mode selection to backend
    sendModeSelection(mode) {
        return this.send('mode_select', { mode: mode });
    }

    // Send audio control command
    sendAudioControl(action, parameters = {}) {
        return this.send('audio_control', {
            action: action,
            parameters: parameters
        });
    }

    // Send UI interaction event
    sendUIInteraction(element, action, position = null) {
        return this.send('ui_interaction', {
            element: element,
            action: action,
            position: position
        });
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

            console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.updateConnectionStatus('reconnecting');

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = status;
            statusElement.className = status;
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Client disconnect');
        }
    }
}

// Export for use in other modules
window.WebSocketClient = WebSocketClient;