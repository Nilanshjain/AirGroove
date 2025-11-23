/**
 * Library Page Manager
 * Manages the comprehensive library interface for viewing and managing songs and playlists
 */

class LibraryPage {
    constructor() {
        this.library = null;
        this.currentView = 'all-songs';
        this.currentPlaylist = null;
        this.searchTerm = '';
        this.selectedSongs = new Set();

        this.init();
    }

    async init() {
        console.log('[LibraryPage] Initializing...');

        // Load library data
        await this.loadLibrary();

        // Set up event listeners
        this.setupEventListeners();

        // Show initial view
        this.showView('all-songs');

        console.log('[LibraryPage] Initialized');
    }

    async loadLibrary() {
        try {
            const response = await fetch('../library.json');
            this.library = await response.json();
            console.log('[LibraryPage] Library loaded:', this.library);

            this.updateCounts();
            this.renderAllSongs();
            this.renderPlaylists();
            this.renderLikedSongs();
        } catch (error) {
            console.error('[LibraryPage] Failed to load library:', error);
            this.showNotification('Failed to load library', 'error');
        }
    }

    setupEventListeners() {
        // Sidebar navigation
        document.getElementById('nav-all-songs')?.addEventListener('click', () => {
            this.showView('all-songs');
        });

        document.getElementById('nav-playlists')?.addEventListener('click', () => {
            this.showView('playlists');
        });

        document.getElementById('nav-liked-songs')?.addEventListener('click', () => {
            this.showView('liked-songs');
        });

        // Create playlist buttons
        document.getElementById('create-playlist-btn')?.addEventListener('click', () => {
            this.openCreatePlaylistModal();
        });

        document.getElementById('create-playlist-btn-header')?.addEventListener('click', () => {
            this.openCreatePlaylistModal();
        });

        // Add songs button (on library page)
        document.getElementById('add-songs-btn')?.addEventListener('click', () => {
            this.showNotification('Add songs from your local storage', 'info');
        });

        // Create playlist modal
        document.getElementById('modal-close')?.addEventListener('click', () => {
            this.closeCreatePlaylistModal();
        });

        document.getElementById('modal-overlay')?.addEventListener('click', () => {
            this.closeCreatePlaylistModal();
        });

        document.getElementById('cancel-create-playlist')?.addEventListener('click', () => {
            this.closeCreatePlaylistModal();
        });

        document.getElementById('confirm-create-playlist')?.addEventListener('click', () => {
            this.createPlaylist();
        });

        // Add to playlist modal
        document.getElementById('add-modal-close')?.addEventListener('click', () => {
            this.closeAddToPlaylistModal();
        });

        document.getElementById('add-modal-overlay')?.addEventListener('click', () => {
            this.closeAddToPlaylistModal();
        });

        document.getElementById('cancel-add-songs')?.addEventListener('click', () => {
            this.closeAddToPlaylistModal();
        });

        document.getElementById('confirm-add-songs')?.addEventListener('click', () => {
            this.addSongsToPlaylist();
        });

        // Search inputs
        document.getElementById('search-all-songs')?.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.renderAllSongs();
        });

        document.getElementById('search-liked-songs')?.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.renderLikedSongs();
        });

        document.getElementById('search-songs-to-add')?.addEventListener('input', (e) => {
            this.filterSongSelection(e.target.value.toLowerCase());
        });

        // Play all buttons
        document.getElementById('play-all-songs')?.addEventListener('click', () => {
            this.playAllSongs();
        });

        document.getElementById('play-liked-songs')?.addEventListener('click', () => {
            this.playLikedSongs();
        });

        // Playlist detail actions
        document.getElementById('back-to-playlists')?.addEventListener('click', () => {
            this.showView('playlists');
        });

        document.getElementById('add-to-playlist-btn')?.addEventListener('click', () => {
            this.openAddToPlaylistModal();
        });

        document.getElementById('play-playlist')?.addEventListener('click', () => {
            this.playCurrentPlaylist();
        });
    }

    showView(viewName) {
        // Update sidebar active state
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        document.getElementById(`nav-${viewName}`)?.classList.add('active');

        // Update view visibility
        document.querySelectorAll('.library-view').forEach(view => {
            view.classList.add('hidden');
        });
        document.getElementById(`view-${viewName}`)?.classList.remove('hidden');

        this.currentView = viewName;
        this.searchTerm = '';
    }

    updateCounts() {
        if (!this.library) return;

        const totalSongs = Object.keys(this.library.tracks).length;
        const totalPlaylists = Object.keys(this.library.playlists).length;
        const totalLiked = this.library.likedSongs?.tracks?.length || 0;

        document.getElementById('count-all-songs').textContent = totalSongs;
        document.getElementById('count-playlists').textContent = totalPlaylists;
        document.getElementById('count-liked').textContent = totalLiked;

        document.getElementById('subtitle-all-songs').textContent = `${totalSongs} song${totalSongs !== 1 ? 's' : ''} in your library`;
        document.getElementById('subtitle-playlists').textContent = `${totalPlaylists} playlist${totalPlaylists !== 1 ? 's' : ''}`;
        document.getElementById('subtitle-liked').textContent = `${totalLiked} liked song${totalLiked !== 1 ? 's' : ''}`;
    }

    renderAllSongs() {
        const container = document.getElementById('songs-list');
        if (!container || !this.library) return;

        const tracks = Object.values(this.library.tracks);
        const filteredTracks = this.searchTerm
            ? tracks.filter(t =>
                t.name.toLowerCase().includes(this.searchTerm) ||
                t.artist.toLowerCase().includes(this.searchTerm))
            : tracks;

        if (filteredTracks.length === 0) {
            container.innerHTML = `
                <div class="library-empty">
                    <div class="library-empty-icon">🔍</div>
                    <p class="library-empty-text">No songs found</p>
                    <p class="library-empty-hint">Try a different search term</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredTracks.map((track, index) => `
            <div class="song-row" data-track-id="${track.id}">
                <div class="col-index">${index + 1}</div>
                <div class="col-title">${track.name}</div>
                <div class="col-artist">${track.artist}</div>
                <div class="col-bpm">${track.bpm.toFixed(1)}</div>
                <div class="col-date">${track.addedDate || 'Unknown'}</div>
                <div class="col-actions">
                    <button class="song-action-btn ${track.liked ? 'liked' : ''}" onclick="libraryPage.toggleLike('${track.id}')" title="${track.liked ? 'Unlike' : 'Like'}">
                        ${track.liked ? Icons.get('heart') : Icons.get('heartOutline')}
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'a')" title="Load to Deck A">
                        A
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'b')" title="Load to Deck B">
                        B
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderLikedSongs() {
        const container = document.getElementById('liked-songs-list');
        if (!container || !this.library) return;

        const likedTrackIds = this.library.likedSongs?.tracks || [];
        const likedTracks = likedTrackIds.map(id => this.library.tracks[id]).filter(t => t);

        const filteredTracks = this.searchTerm
            ? likedTracks.filter(t =>
                t.name.toLowerCase().includes(this.searchTerm) ||
                t.artist.toLowerCase().includes(this.searchTerm))
            : likedTracks;

        if (filteredTracks.length === 0) {
            container.innerHTML = `
                <div class="library-empty">
                    <div class="library-empty-icon">${Icons.get('heart')}</div>
                    <p class="library-empty-text">No liked songs yet</p>
                    <p class="library-empty-hint">Like songs from your library</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredTracks.map((track, index) => `
            <div class="song-row" data-track-id="${track.id}">
                <div class="col-index">${index + 1}</div>
                <div class="col-title">${track.name}</div>
                <div class="col-artist">${track.artist}</div>
                <div class="col-bpm">${track.bpm.toFixed(1)}</div>
                <div class="col-date">${track.addedDate || 'Unknown'}</div>
                <div class="col-actions">
                    <button class="song-action-btn liked" onclick="libraryPage.toggleLike('${track.id}')" title="Unlike">
                        ${Icons.get('heart')}
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'a')" title="Load to Deck A">
                        A
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'b')" title="Load to Deck B">
                        B
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderPlaylists() {
        const container = document.getElementById('playlists-grid');
        if (!container || !this.library) return;

        const playlists = Object.values(this.library.playlists);

        if (playlists.length === 0) {
            container.innerHTML = `
                <div class="library-empty">
                    <div class="library-empty-icon">${Icons.get('folder')}</div>
                    <p class="library-empty-text">No playlists yet</p>
                    <p class="library-empty-hint">Create a playlist to get started</p>
                </div>
            `;
            return;
        }

        container.innerHTML = playlists.map(playlist => `
            <div class="playlist-card" onclick="libraryPage.openPlaylist('${playlist.id}')">
                <div class="playlist-card-icon">${Icons.get('folder')}</div>
                <div class="playlist-card-title">${playlist.name}</div>
                <div class="playlist-card-subtitle">${playlist.description || 'No description'}</div>
                <div class="playlist-card-meta">
                    <span>${playlist.tracks.length} song${playlist.tracks.length !== 1 ? 's' : ''}</span>
                    <span>${playlist.createdDate || ''}</span>
                </div>
            </div>
        `).join('');
    }

    openPlaylist(playlistId) {
        this.currentPlaylist = this.library.playlists[playlistId];
        if (!this.currentPlaylist) return;

        document.getElementById('playlist-detail-title').textContent = this.currentPlaylist.name;
        document.getElementById('playlist-detail-subtitle').textContent =
            `${this.currentPlaylist.tracks.length} song${this.currentPlaylist.tracks.length !== 1 ? 's' : ''}`;

        this.renderPlaylistSongs();
        this.showView('playlist-detail');
    }

    renderPlaylistSongs() {
        const container = document.getElementById('playlist-detail-songs');
        if (!container || !this.currentPlaylist) return;

        const tracks = this.currentPlaylist.tracks.map(id => this.library.tracks[id]).filter(t => t);

        if (tracks.length === 0) {
            container.innerHTML = `
                <div class="library-empty">
                    <div class="library-empty-icon">${Icons.get('music')}</div>
                    <p class="library-empty-text">No songs in this playlist</p>
                    <p class="library-empty-hint">Add songs to get started</p>
                </div>
            `;
            return;
        }

        container.innerHTML = tracks.map((track, index) => `
            <div class="song-row" data-track-id="${track.id}">
                <div class="col-index">${index + 1}</div>
                <div class="col-title">${track.name}</div>
                <div class="col-artist">${track.artist}</div>
                <div class="col-bpm">${track.bpm.toFixed(1)}</div>
                <div class="col-actions">
                    <button class="song-action-btn" onclick="libraryPage.removeFromPlaylist('${track.id}')" title="Remove from playlist">
                        ${Icons.get('trash')}
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'a')" title="Load to Deck A">
                        A
                    </button>
                    <button class="song-action-btn" onclick="libraryPage.loadTrack('${track.id}', 'b')" title="Load to Deck B">
                        B
                    </button>
                </div>
            </div>
        `).join('');
    }

    openCreatePlaylistModal() {
        document.getElementById('playlist-name').value = '';
        document.getElementById('playlist-description').value = '';
        document.getElementById('create-playlist-modal').classList.remove('hidden');
    }

    closeCreatePlaylistModal() {
        document.getElementById('create-playlist-modal').classList.add('hidden');
    }

    createPlaylist() {
        const name = document.getElementById('playlist-name').value.trim();
        const description = document.getElementById('playlist-description').value.trim();

        if (!name) {
            this.showNotification('Please enter a playlist name', 'error');
            return;
        }

        const playlistId = name.toLowerCase().replace(/\s+/g, '_');

        if (this.library.playlists[playlistId]) {
            this.showNotification('A playlist with this name already exists', 'error');
            return;
        }

        // Create new playlist
        this.library.playlists[playlistId] = {
            id: playlistId,
            name: name,
            description: description,
            tracks: [],
            createdDate: new Date().toISOString().split('T')[0]
        };

        // Save to library
        this.saveLibrary();

        // Update UI
        this.updateCounts();
        this.renderPlaylists();
        this.closeCreatePlaylistModal();

        this.showNotification(`Playlist "${name}" created successfully`, 'success');
    }

    openAddToPlaylistModal() {
        if (!this.currentPlaylist) return;

        this.selectedSongs.clear();
        this.renderSongSelection();
        document.getElementById('add-to-playlist-modal').classList.remove('hidden');
    }

    closeAddToPlaylistModal() {
        document.getElementById('add-to-playlist-modal').classList.add('hidden');
    }

    renderSongSelection() {
        const container = document.getElementById('songs-selection-list');
        if (!container || !this.library) return;

        const tracks = Object.values(this.library.tracks);
        const playlistTrackIds = this.currentPlaylist.tracks;

        container.innerHTML = tracks.map(track => {
            const alreadyInPlaylist = playlistTrackIds.includes(track.id);
            return `
                <div class="song-selection-item ${alreadyInPlaylist ? 'disabled' : ''}" data-track-id="${track.id}">
                    <input type="checkbox"
                        id="select-${track.id}"
                        ${alreadyInPlaylist ? 'disabled checked' : ''}
                        onchange="libraryPage.toggleSongSelection('${track.id}')">
                    <div class="song-selection-info">
                        <div class="song-selection-name">${track.name}</div>
                        <div class="song-selection-artist">${track.artist}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    filterSongSelection(searchTerm) {
        const items = document.querySelectorAll('.song-selection-item');
        items.forEach(item => {
            const trackId = item.dataset.trackId;
            const track = this.library.tracks[trackId];
            const matches = track.name.toLowerCase().includes(searchTerm) ||
                          track.artist.toLowerCase().includes(searchTerm);
            item.style.display = matches ? 'flex' : 'none';
        });
    }

    toggleSongSelection(trackId) {
        if (this.selectedSongs.has(trackId)) {
            this.selectedSongs.delete(trackId);
        } else {
            this.selectedSongs.add(trackId);
        }
    }

    addSongsToPlaylist() {
        if (this.selectedSongs.size === 0) {
            this.showNotification('Please select at least one song', 'error');
            return;
        }

        // Add selected songs to current playlist
        this.selectedSongs.forEach(trackId => {
            if (!this.currentPlaylist.tracks.includes(trackId)) {
                this.currentPlaylist.tracks.push(trackId);
            }
        });

        // Save and update
        this.saveLibrary();
        this.renderPlaylistSongs();
        this.closeAddToPlaylistModal();

        this.showNotification(`${this.selectedSongs.size} song(s) added to playlist`, 'success');
        this.selectedSongs.clear();
    }

    removeFromPlaylist(trackId) {
        if (!this.currentPlaylist) return;

        const index = this.currentPlaylist.tracks.indexOf(trackId);
        if (index > -1) {
            this.currentPlaylist.tracks.splice(index, 1);
            this.saveLibrary();
            this.renderPlaylistSongs();
            this.showNotification('Song removed from playlist', 'success');
        }
    }

    toggleLike(trackId) {
        const track = this.library.tracks[trackId];
        if (!track) return;

        track.liked = !track.liked;

        // Update liked songs list
        if (!this.library.likedSongs) {
            this.library.likedSongs = { tracks: [] };
        }

        if (track.liked) {
            if (!this.library.likedSongs.tracks.includes(trackId)) {
                this.library.likedSongs.tracks.push(trackId);
            }
        } else {
            const index = this.library.likedSongs.tracks.indexOf(trackId);
            if (index > -1) {
                this.library.likedSongs.tracks.splice(index, 1);
            }
        }

        this.saveLibrary();
        this.updateCounts();
        this.renderAllSongs();
        this.renderLikedSongs();
    }

    loadTrack(trackId, deck) {
        const track = this.library.tracks[trackId];
        if (!track) return;

        console.log(`[LibraryPage] Loading "${track.name}" to Deck ${deck.toUpperCase()}`);
        this.showNotification(`Loading "${track.name}" to Deck ${deck.toUpperCase()}`, 'info');

        // In a real implementation, this would send a command to the backend
        // For now, we just show a notification
    }

    playAllSongs() {
        const tracks = Object.values(this.library.tracks);
        if (tracks.length === 0) return;

        this.showNotification(`Playing all ${tracks.length} songs`, 'info');
        // Load first track to Deck A
        this.loadTrack(tracks[0].id, 'a');
    }

    playLikedSongs() {
        const likedTrackIds = this.library.likedSongs?.tracks || [];
        if (likedTrackIds.length === 0) return;

        this.showNotification(`Playing ${likedTrackIds.length} liked songs`, 'info');
        // Load first liked track to Deck A
        this.loadTrack(likedTrackIds[0], 'a');
    }

    playCurrentPlaylist() {
        if (!this.currentPlaylist || this.currentPlaylist.tracks.length === 0) return;

        this.showNotification(`Playing playlist "${this.currentPlaylist.name}"`, 'info');
        // Load first track to Deck A
        this.loadTrack(this.currentPlaylist.tracks[0], 'a');
    }

    saveLibrary() {
        // In a real implementation, this would save to the backend
        // For now, we just update localStorage
        try {
            localStorage.setItem('airgroove_library', JSON.stringify(this.library));
            console.log('[LibraryPage] Library saved to localStorage');
        } catch (error) {
            console.error('[LibraryPage] Failed to save library:', error);
        }
    }

    showNotification(message, type = 'info') {
        console.log(`[LibraryPage] ${type.toUpperCase()}: ${message}`);
        // In a real implementation, this would show a toast notification
        // For now, we just log to console
    }
}

// Initialize library page when DOM is loaded
let libraryPage;
document.addEventListener('DOMContentLoaded', () => {
    libraryPage = new LibraryPage();
    window.libraryPage = libraryPage; // Make it globally accessible
});
