document.addEventListener('DOMContentLoaded', function() {
    const player = {
        // DOM Elements
        container: document.querySelector('.music-player'),
        playButton: document.querySelector('.player-button[data-action="play"]'),
        prevButton: document.querySelector('.player-button[data-action="previous"]'),
        nextButton: document.querySelector('.player-button[data-action="next"]'),
        volumeSlider: document.querySelector('.volume-slider'),
        progressBar: document.querySelector('.progress-bar'),
        progressCurrent: document.querySelector('.progress-current'),
        trackTitle: document.querySelector('.track-title'),
        trackArtist: document.querySelector('.track-artist'),
        volumeIcon: document.querySelector('.volume-control i'),

        // Player state
        isPlaying: false,
        currentTrack: null,
        volume: 50,
        progress: 0,
        spotifyPlayer: null,

        init: function() {
            this.setupEventListeners();
            this.initSpotifySDK();
        },

        setupEventListeners: function() {
            // Play/Pause
            this.playButton.addEventListener('click', () => {
                if (this.isPlaying) {
                    this.pause();
                } else {
                    this.play();
                }
            });

            // Previous/Next
            this.prevButton.addEventListener('click', () => this.previous());
            this.nextButton.addEventListener('click', () => this.next());

            // Volume
            this.volumeSlider.addEventListener('input', (e) => {
                this.setVolume(e.target.value);
            });

            // Progress bar
            this.progressBar.addEventListener('click', (e) => {
                const rect = this.progressBar.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                this.seekTo(percent);
            });
        },

        initSpotifySDK: function() {
            window.onSpotifyWebPlaybackSDKReady = () => {
                // Initialize Spotify Player here when we have authentication
                console.log('Spotify SDK Ready');
            };
        },

        play: function() {
            // For now, just toggle play state
            this.isPlaying = true;
            this.playButton.querySelector('i').classList.replace('fa-play', 'fa-pause');
            // Start progress animation
            this.updateProgress();
        },

        pause: function() {
            this.isPlaying = false;
            this.playButton.querySelector('i').classList.replace('fa-pause', 'fa-play');
        },

        previous: function() {
            // Implement previous track functionality
            console.log('Previous track');
        },

        next: function() {
            // Implement next track functionality
            console.log('Next track');
        },

        setVolume: function(value) {
            this.volume = value;
            // Update volume icon based on level
            if (value == 0) {
                this.volumeIcon.className = 'fas fa-volume-mute';
            } else if (value < 50) {
                this.volumeIcon.className = 'fas fa-volume-down';
            } else {
                this.volumeIcon.className = 'fas fa-volume-up';
            }
        },

        seekTo: function(percent) {
            this.progress = percent * 100;
            this.progressCurrent.style.width = `${this.progress}%`;
        },

        updateProgress: function() {
            if (this.isPlaying) {
                this.progress = (this.progress + 0.1) % 100;
                this.progressCurrent.style.width = `${this.progress}%`;
                setTimeout(() => this.updateProgress(), 100);
            }
        },

        updateTrackInfo: function(title, artist) {
            this.trackTitle.textContent = title || 'No track selected';
            this.trackArtist.textContent = artist || '-';
        }
    };

    // Initialize player
    player.init();
});
