/**
 * Library Manager - Playlist and track management system
 */

class LibraryManager {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.library = null;
        this.currentPlaylist = null;

        // Deck queues and state
        this.deckQueues = {
            a: {
                playlist: null,
                currentIndex: -1,
                tracks: [],
                autoAdvance: true
            },
            b: {
                playlist: null,
                currentIndex: -1,
                tracks: [],
                autoAdvance: true
            }
        };

        this.isOpen = false;
        this.init();
    }

    async init() {
        console.log('[Library] Initializing library manager...');

        // Load saved deck queues from localStorage
        this.loadDeckQueuesFromStorage();

        // Create UI elements
        this.createLibraryUI();

        // Load library data
        await this.loadLibrary();

        // Set up event listeners
        this.setupEventListeners();

        console.log('[Library] Library manager initialized');
        console.log('[Library] Deck queues:', this.deckQueues);
    }

    // Save deck queues to localStorage for persistence
    saveDeckQueuesToStorage() {
        try {
            const queuesData = {
                a: {
                    playlist: this.deckQueues.a.playlist,
                    currentIndex: this.deckQueues.a.currentIndex,
                    tracks: this.deckQueues.a.tracks,
                    autoAdvance: this.deckQueues.a.autoAdvance
                },
                b: {
                    playlist: this.deckQueues.b.playlist,
                    currentIndex: this.deckQueues.b.currentIndex,
                    tracks: this.deckQueues.b.tracks,
                    autoAdvance: this.deckQueues.b.autoAdvance
                }
            };
            localStorage.setItem('airgroove_deck_queues', JSON.stringify(queuesData));
            console.log('[Library] Deck queues saved to localStorage');
        } catch (error) {
            console.error('[Library] Error saving deck queues:', error);
        }
    }

    // Load deck queues from localStorage
    loadDeckQueuesFromStorage() {
        try {
            const stored = localStorage.getItem('airgroove_deck_queues');
            if (stored) {
                const queuesData = JSON.parse(stored);
                this.deckQueues = queuesData;
                console.log('[Library] Deck queues loaded from localStorage');
            }
        } catch (error) {
            console.error('[Library] Error loading deck queues:', error);
        }
    }

    createLibraryUI() {
        // Create library toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'library-toggle';
        toggleBtn.id = 'library-toggle';
        toggleBtn.innerHTML = `<span class="library-toggle-icon">${Icons.get('music')}</span>`;
        document.body.appendChild(toggleBtn);

        // Create library panel
        const panel = document.createElement('div');
        panel.className = 'library-panel';
        panel.id = 'library-panel';
        panel.innerHTML = `
            <div class="library-header">
                <h3 class="library-title">
                    <span class="library-icon">${Icons.get('music')}</span>
                    Music Library
                </h3>
                <p class="library-subtitle">Browse and load playlists</p>
            </div>

            <div class="playlist-selector">
                <label for="playlist-select">Select Playlist</label>
                <select id="playlist-select" class="playlist-select">
                    <option value="">Loading playlists...</option>
                </select>
            </div>

            <div class="track-list" id="track-list">
                <!-- Tracks will be populated here -->
            </div>

            <div class="playlist-actions">
                <button class="playlist-action-btn deck-a" id="load-playlist-a">
                    <span>${Icons.get('play')}</span>
                    <span>DECK A</span>
                </button>
                <button class="playlist-action-btn deck-b" id="load-playlist-b">
                    <span>${Icons.get('play')}</span>
                    <span>DECK B</span>
                </button>
            </div>

            <div class="deck-queue-section" id="deck-queues">
                <!-- Deck queues will be shown here -->
            </div>
        `;
        document.body.appendChild(panel);
    }

    setupEventListeners() {
        // Toggle library panel
        const toggleBtn = document.getElementById('library-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Playlist selector
        const playlistSelect = document.getElementById('playlist-select');
        if (playlistSelect) {
            playlistSelect.addEventListener('change', (e) => {
                this.selectPlaylist(e.target.value);
            });
        }

        // Load playlist buttons
        document.getElementById('load-playlist-a')?.addEventListener('click', () => {
            this.loadPlaylistToDeck('a');
        });

        document.getElementById('load-playlist-b')?.addEventListener('click', () => {
            this.loadPlaylistToDeck('b');
        });
    }

    async loadLibrary() {
        try {
            const response = await fetch('library.json');
            this.library = await response.json();
            console.log('[Library] Library loaded:', this.library);

            this.populatePlaylists();

            // Select first playlist by default
            const firstPlaylistId = Object.keys(this.library.playlists)[0];
            if (firstPlaylistId) {
                this.selectPlaylist(firstPlaylistId);
            }
        } catch (error) {
            console.error('[Library] Failed to load library:', error);
            this.showError('Failed to load library');
        }
    }

    populatePlaylists() {
        const select = document.getElementById('playlist-select');
        if (!select || !this.library) return;

        select.innerHTML = '';

        // Add option for each playlist
        Object.values(this.library.playlists).forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.id;
            option.textContent = playlist.name;
            select.appendChild(option);
        });
    }

    selectPlaylist(playlistId) {
        if (!playlistId || !this.library) return;

        this.currentPlaylist = this.library.playlists[playlistId];
        console.log('[Library] Selected playlist:', this.currentPlaylist);

        this.displayPlaylistTracks();
    }

    displayPlaylistTracks() {
        const trackList = document.getElementById('track-list');
        if (!trackList || !this.currentPlaylist) return;

        trackList.innerHTML = '';

        if (!this.currentPlaylist.tracks || this.currentPlaylist.tracks.length === 0) {
            trackList.innerHTML = `
                <div class="library-empty">
                    <div class="library-empty-icon">${Icons.get('music')}</div>
                    <p class="library-empty-text">No tracks in this playlist</p>
                    <p class="library-empty-hint">Add tracks to get started</p>
                </div>
            `;
            return;
        }

        // Display each track
        this.currentPlaylist.tracks.forEach((trackId, index) => {
            const track = this.library.tracks[trackId];
            if (!track) return;

            const trackItem = document.createElement('div');
            trackItem.className = 'track-item';
            trackItem.dataset.trackId = trackId;
            trackItem.dataset.trackIndex = index;

            trackItem.innerHTML = `
                <div class="track-name">${track.name}</div>
                <div class="track-artist">${track.artist || 'Unknown Artist'}</div>
                <div class="track-meta">
                    <span class="track-bpm">${track.bpm.toFixed(1)} BPM</span>
                    <span class="track-duration">${this.formatDuration(track.duration)}</span>
                </div>
            `;

            // Click to load individual track
            trackItem.addEventListener('click', () => {
                this.showTrackLoadMenu(track, trackItem);
            });

            trackList.appendChild(trackItem);
        });
    }

    showTrackLoadMenu(track, trackElement) {
        // Simple implementation - load to Deck A by default
        // Could be enhanced with a context menu
        console.log('[Library] Loading track:', track.name);

        if (this.wsClient) {
            this.wsClient.sendAudioControl('load_track', {
                deck: 'a',
                file_path: track.path,
                file_name: track.name
            });
        }
    }

    loadPlaylistToDeck(deck) {
        if (!this.currentPlaylist) {
            console.warn('[Library] No playlist selected');
            return;
        }

        console.log(`[Library] Loading playlist "${this.currentPlaylist.name}" to Deck ${deck.toUpperCase()}`);

        const deckQueue = this.deckQueues[deck];
        deckQueue.playlist = this.currentPlaylist;
        deckQueue.tracks = this.currentPlaylist.tracks.map(trackId => this.library.tracks[trackId]);
        deckQueue.currentIndex = 0;
        deckQueue.autoAdvance = true;

        // Save state to localStorage
        this.saveDeckQueuesToStorage();

        // Load first track
        if (deckQueue.tracks.length > 0) {
            this.loadTrackFromQueue(deck, 0);
            this.updateDeckQueueDisplay();
        }

        // Show notification
        if (window.app) {
            window.app.showNotification(
                `Playlist "${this.currentPlaylist.name}" loaded to Deck ${deck.toUpperCase()}`,
                'success'
            );
        }
    }

    loadTrackFromQueue(deck, index) {
        const deckQueue = this.deckQueues[deck];

        if (index < 0 || index >= deckQueue.tracks.length) {
            console.warn(`[Library] Invalid track index: ${index}`);
            return;
        }

        deckQueue.currentIndex = index;
        const track = deckQueue.tracks[index];

        console.log(`[Library] Loading track ${index + 1}/${deckQueue.tracks.length}: ${track.name} to Deck ${deck.toUpperCase()}`);

        // Send load command to backend
        if (this.wsClient) {
            this.wsClient.sendAudioControl('load_track', {
                deck: deck,
                file_path: track.path,
                file_name: track.name,
                from_playlist: true
            });
        }

        // Save state to localStorage
        this.saveDeckQueuesToStorage();

        this.updateDeckQueueDisplay();
    }

    nextTrack(deck) {
        const deckQueue = this.deckQueues[deck];

        if (!deckQueue.playlist) {
            console.warn(`[Library] No playlist loaded on Deck ${deck.toUpperCase()}`);
            return false;
        }

        const nextIndex = deckQueue.currentIndex + 1;

        if (nextIndex >= deckQueue.tracks.length) {
            console.log(`[Library] Reached end of playlist on Deck ${deck.toUpperCase()}`);
            return false;
        }

        this.loadTrackFromQueue(deck, nextIndex);
        return true;
    }

    previousTrack(deck) {
        const deckQueue = this.deckQueues[deck];

        if (!deckQueue.playlist) {
            console.warn(`[Library] No playlist loaded on Deck ${deck.toUpperCase()}`);
            return false;
        }

        const prevIndex = deckQueue.currentIndex - 1;

        if (prevIndex < 0) {
            console.log(`[Library] Already at first track on Deck ${deck.toUpperCase()}`);
            return false;
        }

        this.loadTrackFromQueue(deck, prevIndex);
        return true;
    }

    onTrackEnd(deck) {
        const deckQueue = this.deckQueues[deck];

        if (deckQueue.autoAdvance && deckQueue.playlist) {
            console.log(`[Library] Track ended on Deck ${deck.toUpperCase()}, auto-advancing...`);
            this.nextTrack(deck);
        }
    }

    updateDeckQueueDisplay() {
        const queueContainer = document.getElementById('deck-queues');
        if (!queueContainer) return;

        let html = '';

        // Display queue for each deck
        ['a', 'b'].forEach(deck => {
            const deckQueue = this.deckQueues[deck];

            if (deckQueue.playlist && deckQueue.tracks.length > 0) {
                const deckLabel = deck === 'a' ? 'DECK A' : 'DECK B';
                const deckClass = deck === 'a' ? 'deck-a' : 'deck-b';

                html += `
                    <div class="queue-header">
                        <span class="queue-deck-label ${deckClass}">${deckLabel}</span>
                        <span>${deckQueue.playlist.name}</span>
                    </div>
                    <div class="queue-list">
                `;

                // Show current and next 2 tracks
                const startIndex = Math.max(0, deckQueue.currentIndex);
                const endIndex = Math.min(deckQueue.tracks.length, startIndex + 3);

                for (let i = startIndex; i < endIndex; i++) {
                    const track = deckQueue.tracks[i];
                    const isCurrent = i === deckQueue.currentIndex;

                    const playIndicator = isCurrent ? `<span class="queue-play-icon">${Icons.get('play')}</span> ` : '';
                    html += `
                        <div class="queue-item ${isCurrent ? 'current' : ''}">
                            <span class="queue-track-name">${playIndicator}${track.name}</span>
                            <span class="queue-position">${i + 1}/${deckQueue.tracks.length}</span>
                        </div>
                    `;
                }

                html += '</div>';
            }
        });

        if (html === '') {
            html = `
                <div class="library-empty" style="padding: 20px;">
                    <p class="library-empty-hint">No playlists loaded to decks</p>
                </div>
            `;
        }

        queueContainer.innerHTML = html;
    }

    toggle() {
        this.isOpen = !this.isOpen;

        const panel = document.getElementById('library-panel');
        const toggleBtn = document.getElementById('library-toggle');

        if (panel) {
            panel.classList.toggle('open', this.isOpen);
        }

        if (toggleBtn) {
            toggleBtn.classList.toggle('active', this.isOpen);
        }

        console.log(`[Library] Panel ${this.isOpen ? 'opened' : 'closed'}`);
    }

    formatDuration(seconds) {
        if (!seconds || seconds === 0) return '--:--';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    showError(message) {
        console.error('[Library]', message);

        if (window.app) {
            window.app.showNotification(message, 'error');
        }
    }
}

// Export for use in main.js
window.LibraryManager = LibraryManager;
