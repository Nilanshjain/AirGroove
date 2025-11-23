/**
 * AirGroove Comprehensive Genre System
 * 50+ genres organized by category with sub-genres
 */

const GenreSystem = {
    // Electronic Dance Music (EDM)
    electronic: {
        name: 'Electronic',
        color: '#7c3aed',
        subgenres: [
            'House',
            'Deep House',
            'Tech House',
            'Progressive House',
            'Electro House',
            'Future House',
            'Techno',
            'Minimal Techno',
            'Detroit Techno',
            'Trance',
            'Progressive Trance',
            'Psytrance',
            'Uplifting Trance',
            'Dubstep',
            'Drum and Bass',
            'Liquid DnB',
            'Neurofunk',
            'Breakbeat',
            'Garage',
            'UK Garage',
            'Future Garage',
            'Ambient',
            'Downtempo',
            'Chillwave'
        ]
    },

    // Hip Hop & Rap
    hiphop: {
        name: 'Hip Hop',
        color: '#ef4444',
        subgenres: [
            'Boom Bap',
            'Trap',
            'Drill',
            'Cloud Rap',
            'Mumble Rap',
            'Conscious Hip Hop',
            'Gangsta Rap',
            'East Coast Hip Hop',
            'West Coast Hip Hop',
            'Southern Hip Hop',
            'Jazz Rap',
            'Alternative Hip Hop',
            'Lo-fi Hip Hop'
        ]
    },

    // Pop
    pop: {
        name: 'Pop',
        color: '#ec4899',
        subgenres: [
            'Dance Pop',
            'Electropop',
            'Synthpop',
            'Indie Pop',
            'K-Pop',
            'J-Pop',
            'Teen Pop',
            'Art Pop',
            'Power Pop',
            'Bubblegum Pop'
        ]
    },

    // Rock
    rock: {
        name: 'Rock',
        color: '#f97316',
        subgenres: [
            'Classic Rock',
            'Hard Rock',
            'Alternative Rock',
            'Indie Rock',
            'Punk Rock',
            'Post-Punk',
            'Grunge',
            'Progressive Rock',
            'Psychedelic Rock',
            'Garage Rock',
            'Blues Rock',
            'Folk Rock'
        ]
    },

    // R&B & Soul
    rnb: {
        name: 'R&B / Soul',
        color: '#a855f7',
        subgenres: [
            'Contemporary R&B',
            'Neo Soul',
            'Alternative R&B',
            'Motown',
            'Funk',
            'Disco',
            'Smooth R&B',
            'Gospel'
        ]
    },

    // Jazz
    jazz: {
        name: 'Jazz',
        color: '#3b82f6',
        subgenres: [
            'Bebop',
            'Cool Jazz',
            'Modal Jazz',
            'Free Jazz',
            'Fusion',
            'Latin Jazz',
            'Smooth Jazz',
            'Swing',
            'Ragtime',
            'Acid Jazz',
            'Nu Jazz'
        ]
    },

    // Latin
    latin: {
        name: 'Latin',
        color: '#f59e0b',
        subgenres: [
            'Reggaeton',
            'Salsa',
            'Bachata',
            'Merengue',
            'Cumbia',
            'Latin Pop',
            'Banda',
            'Norteño',
            'Tejano',
            'Bossa Nova',
            'Samba'
        ]
    },

    // Reggae & Caribbean
    reggae: {
        name: 'Reggae',
        color: '#10b981',
        subgenres: [
            'Roots Reggae',
            'Dancehall',
            'Dub',
            'Ska',
            'Rocksteady',
            'Reggae Fusion',
            'Lovers Rock'
        ]
    },

    // Country
    country: {
        name: 'Country',
        color: '#92400e',
        subgenres: [
            'Contemporary Country',
            'Country Pop',
            'Outlaw Country',
            'Bluegrass',
            'Honky Tonk',
            'Country Rock',
            'Americana'
        ]
    },

    // Metal
    metal: {
        name: 'Metal',
        color: '#1f2937',
        subgenres: [
            'Heavy Metal',
            'Thrash Metal',
            'Death Metal',
            'Black Metal',
            'Power Metal',
            'Progressive Metal',
            'Metalcore',
            'Deathcore',
            'Doom Metal',
            'Nu Metal'
        ]
    },

    // Classical
    classical: {
        name: 'Classical',
        color: '#6366f1',
        subgenres: [
            'Baroque',
            'Classical Period',
            'Romantic',
            'Modern Classical',
            'Chamber Music',
            'Opera',
            'Symphony',
            'Concerto',
            'Minimalism'
        ]
    },

    // World Music
    world: {
        name: 'World',
        color: '#14b8a6',
        subgenres: [
            'Afrobeat',
            'Afrobeats',
            'African Traditional',
            'Indian Classical',
            'Bollywood',
            'Middle Eastern',
            'Celtic',
            'Flamenco',
            'Fado',
            'K-Traditional'
        ]
    }
};

// Flat list of all genres for easy access
const AllGenres = Object.keys(GenreSystem).reduce((acc, category) => {
    const categoryData = GenreSystem[category];
    acc.push(categoryData.name);
    acc.push(...categoryData.subgenres);
    return acc;
}, []);

// Get genre color based on genre name
function getGenreColor(genreName) {
    for (const category in GenreSystem) {
        const categoryData = GenreSystem[category];
        if (categoryData.name === genreName || categoryData.subgenres.includes(genreName)) {
            return categoryData.color;
        }
    }
    return '#71717a'; // Default gray color
}

// Get main category for a genre
function getGenreCategory(genreName) {
    for (const category in GenreSystem) {
        const categoryData = GenreSystem[category];
        if (categoryData.name === genreName || categoryData.subgenres.includes(genreName)) {
            return category;
        }
    }
    return null;
}

// Search genres
function searchGenres(query) {
    const lowercaseQuery = query.toLowerCase();
    return AllGenres.filter(genre =>
        genre.toLowerCase().includes(lowercaseQuery)
    );
}

// Get suggested genres based on selected genres (for recommendations)
function getSuggestedGenres(selectedGenres, limit = 5) {
    const categories = new Set();

    // Find categories of selected genres
    selectedGenres.forEach(genre => {
        const category = getGenreCategory(genre);
        if (category) categories.add(category);
    });

    // Get genres from same categories
    const suggestions = [];
    categories.forEach(category => {
        const categoryData = GenreSystem[category];
        suggestions.push(categoryData.name);
        suggestions.push(...categoryData.subgenres);
    });

    // Filter out already selected genres
    return suggestions
        .filter(genre => !selectedGenres.includes(genre))
        .slice(0, limit);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        GenreSystem,
        AllGenres,
        getGenreColor,
        getGenreCategory,
        searchGenres,
        getSuggestedGenres
    };
}

// Make available globally
window.GenreSystem = GenreSystem;
window.AllGenres = AllGenres;
window.getGenreColor = getGenreColor;
window.getGenreCategory = getGenreCategory;
window.searchGenres = searchGenres;
window.getSuggestedGenres = getSuggestedGenres;
