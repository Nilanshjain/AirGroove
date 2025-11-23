/**
 * AirGroove Profile Page Management
 */

class ProfileManager {
    constructor() {
        this.profile = this.loadProfile();
        this.selectedGenres = new Set(this.profile.genres || []);
        this.init();
    }

    init() {
        this.renderGenreCategories();
        this.renderSelectedGenres();
        this.updateStats();
        this.setupEventListeners();
        this.updateProfileUI();
    }

    loadProfile() {
        try {
            const stored = localStorage.getItem('airgroove_profile');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.error('[Profile] Error loading profile:', error);
        }

        // Default profile
        return {
            username: 'User',
            bio: '',
            genres: [],
            stats: {
                tracks: 0,
                playlists: 0,
                liked: 0,
                mixTimeHours: 0
            }
        };
    }

    saveProfile() {
        try {
            this.profile.genres = Array.from(this.selectedGenres);
            localStorage.setItem('airgroove_profile', JSON.stringify(this.profile));
            console.log('[Profile] Profile saved');
        } catch (error) {
            console.error('[Profile] Error saving profile:', error);
        }
    }

    renderGenreCategories() {
        const container = document.getElementById('genre-categories');
        if (!container) return;

        let html = '';

        for (const [categoryKey, categoryData] of Object.entries(GenreSystem)) {
            const totalGenres = 1 + categoryData.subgenres.length; // Main + subgenres
            const selectedInCategory = [categoryData.name, ...categoryData.subgenres]
                .filter(genre => this.selectedGenres.has(genre)).length;

            html += `
                <div class="genre-category">
                    <div class="genre-category-header">
                        <div class="genre-category-name">
                            <span class="genre-color-indicator" style="background: ${categoryData.color}"></span>
                            ${categoryData.name}
                        </div>
                        <span class="genre-category-count">${selectedInCategory} / ${totalGenres}</span>
                    </div>
                    <div class="genre-tags">
                        <div class="genre-tag ${this.selectedGenres.has(categoryData.name) ? 'selected' : ''}"
                             data-genre="${categoryData.name}">
                            ${categoryData.name}
                        </div>
                        ${categoryData.subgenres.map(subgenre => `
                            <div class="genre-tag ${this.selectedGenres.has(subgenre) ? 'selected' : ''}"
                                 data-genre="${subgenre}">
                                ${subgenre}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;

        // Add click listeners
        const genreTags = container.querySelectorAll('.genre-tag');
        genreTags.forEach(tag => {
            tag.addEventListener('click', () => {
                const genre = tag.dataset.genre;
                this.toggleGenre(genre);
            });
        });
    }

    toggleGenre(genre) {
        if (this.selectedGenres.has(genre)) {
            this.selectedGenres.delete(genre);
        } else {
            this.selectedGenres.add(genre);
        }

        // Update UI
        this.renderGenreCategories();
        this.renderSelectedGenres();
    }

    renderSelectedGenres() {
        const container = document.getElementById('selected-genres-list');
        const count = document.getElementById('selected-count');

        if (!container || !count) return;

        count.textContent = this.selectedGenres.size;

        if (this.selectedGenres.size === 0) {
            container.innerHTML = '<p class="empty-message">No genres selected yet</p>';
            return;
        }

        let html = '';
        this.selectedGenres.forEach(genre => {
            html += `
                <div class="selected-genre-tag">
                    <span>${genre}</span>
                    <button class="remove-genre-btn" data-genre="${genre}">×</button>
                </div>
            `;
        });

        container.innerHTML = html;

        // Add remove listeners
        const removeButtons = container.querySelectorAll('.remove-genre-btn');
        removeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const genre = btn.dataset.genre;
                this.toggleGenre(genre);
            });
        });
    }

    updateStats() {
        // Get stats from localStorage
        const tracks = this.getTracksCount();
        const playlists = this.getPlaylistsCount();
        const liked = this.getLikedCount();
        const mixTime = this.getMixTime();

        // Update profile stats
        this.profile.stats = {
            tracks,
            playlists,
            liked,
            mixTimeHours: mixTime
        };

        // Update UI
        const statTracks = document.getElementById('stat-tracks');
        const statPlaylists = document.getElementById('stat-playlists');
        const statLiked = document.getElementById('stat-liked');
        const statHours = document.getElementById('stat-hours');

        if (statTracks) statTracks.textContent = tracks;
        if (statPlaylists) statPlaylists.textContent = playlists;
        if (statLiked) statLiked.textContent = liked;
        if (statHours) statHours.textContent = `${mixTime}h`;
    }

    getTracksCount() {
        try {
            const library = localStorage.getItem('airgroove_library');
            if (library) {
                const data = JSON.parse(library);
                return data.tracks ? data.tracks.length : 0;
            }
        } catch (error) {
            console.error('[Profile] Error getting tracks count:', error);
        }
        return 0;
    }

    getPlaylistsCount() {
        try {
            const library = localStorage.getItem('airgroove_library');
            if (library) {
                const data = JSON.parse(library);
                return data.playlists ? data.playlists.length : 0;
            }
        } catch (error) {
            console.error('[Profile] Error getting playlists count:', error);
        }
        return 0;
    }

    getLikedCount() {
        try {
            const library = localStorage.getItem('airgroove_library');
            if (library) {
                const data = JSON.parse(library);
                if (data.tracks) {
                    return data.tracks.filter(track => track.liked).length;
                }
            }
        } catch (error) {
            console.error('[Profile] Error getting liked count:', error);
        }
        return 0;
    }

    getMixTime() {
        // Placeholder - in a real app, this would track actual mix time
        return this.profile.stats.mixTimeHours || 0;
    }

    updateProfileUI() {
        const usernameEl = document.getElementById('profile-username');
        const avatarEl = document.getElementById('profile-avatar-text');

        if (usernameEl) {
            usernameEl.textContent = this.profile.username;
        }

        if (avatarEl) {
            avatarEl.textContent = this.profile.username.charAt(0).toUpperCase();
        }
    }

    setupEventListeners() {
        // Save preferences button
        const saveBtn = document.getElementById('save-preferences-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveProfile();
                this.showNotification('Preferences saved successfully!', 'success');
            });
        }

        // Edit profile button
        const editBtn = document.getElementById('edit-profile-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.showEditProfileModal();
            });
        }

        // Modal close
        const modalClose = document.getElementById('modal-close');
        const modalOverlay = document.getElementById('modal-overlay');
        const cancelBtn = document.getElementById('cancel-edit-profile');

        if (modalClose) {
            modalClose.addEventListener('click', () => {
                this.hideEditProfileModal();
            });
        }

        if (modalOverlay) {
            modalOverlay.addEventListener('click', () => {
                this.hideEditProfileModal();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hideEditProfileModal();
            });
        }

        // Save profile changes
        const confirmBtn = document.getElementById('confirm-edit-profile');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.saveProfileChanges();
            });
        }
    }

    showEditProfileModal() {
        const modal = document.getElementById('edit-profile-modal');
        const usernameInput = document.getElementById('username-input');
        const bioInput = document.getElementById('bio-input');

        if (usernameInput) {
            usernameInput.value = this.profile.username;
        }

        if (bioInput) {
            bioInput.value = this.profile.bio || '';
        }

        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    hideEditProfileModal() {
        const modal = document.getElementById('edit-profile-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    saveProfileChanges() {
        const usernameInput = document.getElementById('username-input');
        const bioInput = document.getElementById('bio-input');

        if (usernameInput) {
            this.profile.username = usernameInput.value.trim() || 'User';
        }

        if (bioInput) {
            this.profile.bio = bioInput.value.trim();
        }

        this.saveProfile();
        this.updateProfileUI();
        this.hideEditProfileModal();
        this.showNotification('Profile updated successfully!', 'success');
    }

    showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a notification component
        console.log(`[Profile] ${type.toUpperCase()}: ${message}`);

        // Create temporary notification element
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${type === 'success' ? 'rgba(34, 197, 94, 0.9)' : 'rgba(59, 130, 246, 0.9)'};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            z-index: 2000;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize profile manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.profileManager = new ProfileManager();
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
