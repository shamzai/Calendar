class Clock {
    constructor(container, type = 'digital') {
        this.container = container;
        this.type = type;
        this.radius = 85;
        this.isTransitioning = false;
        this.init();
    }

    init() {
        this.createClockElements();
        this.createClockFace();
        this.setupAnimationFrame();
        this.setupToggle();
        this.handleResize();
        this.setupTouchSupport();
        this.addA11yFeatures();
        this.setupKeyboardNavigation();

        // Set initial mode and visibility
        this.clockDisplay.dataset.mode = 'digital';
        this.digitalClock.style.display = 'block';
        this.digitalClock.classList.add('visible');
        this.analogClock.style.display = 'none';

        // Add event listeners
        window.addEventListener('resize', this.handleResize.bind(this));
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', this.handleReducedMotion.bind(this));
        
        // Initial fade in
        requestAnimationFrame(() => {
            this.clockDisplay.classList.add('visible');
        });
    }

    setupKeyboardNavigation() {
        const focusableElements = this.clockDisplay.querySelectorAll(
            'button, [role="button"], input[type="checkbox"]'
        );

        // Create focus trap
        focusableElements.forEach(element => {
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    const firstFocusable = focusableElements[0];
                    const lastFocusable = focusableElements[focusableElements.length - 1];

                    if (e.shiftKey) {
                        if (document.activeElement === firstFocusable) {
                            e.preventDefault();
                            lastFocusable.focus();
                        }
                    } else {
                        if (document.activeElement === lastFocusable) {
                            e.preventDefault();
                            firstFocusable.focus();
                        }
                    }
                }
            });
        });

        // Add keyboard support for mode toggle
        const clockToggle = this.clockDisplay.querySelector('#clockToggle');
        clockToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleMode();
            }
        });
    }

    toggleMode() {
        if (this.isTransitioning) return;
        this.isTransitioning = true;

        const isAnalog = this.clockDisplay.dataset.mode === 'analog';
        const newMode = isAnalog ? 'digital' : 'analog';
        
        // Start transition
        this.clockDisplay.classList.add('transitioning');
        
        // Update mode
        this.clockDisplay.dataset.mode = newMode;
        
        // Toggle visibility with proper timing
        if (isAnalog) {
            this.analogClock.style.display = 'none';
            this.digitalClock.style.display = 'block';
            requestAnimationFrame(() => {
                this.digitalClock.classList.add('visible');
            });
        } else {
            this.digitalClock.style.display = 'none';
            this.analogClock.style.display = 'block';
            requestAnimationFrame(() => {
                this.analogClock.classList.add('visible');
            });
        }

        // Complete transition
        setTimeout(() => {
            this.clockDisplay.classList.remove('transitioning');
            this.isTransitioning = false;
            
            // Focus management
            if (isAnalog) {
                this.digitalClock.querySelector('.format-toggle').focus();
            } else {
                this.analogClock.querySelector('.clock-face').focus();
            }
        }, 300);
    }

    createClockElements() {
        // Create main clock container
        this.clockDisplay = document.createElement('div');
        this.clockDisplay.className = 'clock-display';
        this.clockDisplay.style.opacity = '1'; // Ensure initial visibility
        this.container.appendChild(this.clockDisplay);

        // Create digital clock
        this.digitalClock = document.createElement('div');
        this.digitalClock.className = 'digital-clock';
        this.digitalClock.innerHTML = `
            <div class="time" role="timer" aria-label="Digital clock">00:00:00</div>
            <div class="date"></div>
            <button class="format-toggle" aria-label="Toggle 12/24 hour format">
                <i class="fas fa-sync-alt"></i>
            </button>
        `;
        this.clockDisplay.appendChild(this.digitalClock);

        // Create analog clock
        this.analogClock = document.createElement('div');
        this.analogClock.className = 'analog-clock';
        this.analogClock.setAttribute('role', 'presentation');
        this.clockDisplay.appendChild(this.analogClock);

        // Create mode toggle
        const toggleContainer = document.createElement('div');
        toggleContainer.className = 'clock-toggle';
        toggleContainer.innerHTML = `
            <label class="toggle-label" for="clockToggle">
                Clock Mode
            </label>
            <input type="checkbox" id="clockToggle" 
                   aria-label="Toggle between digital and analog clock">
        `;
        this.clockDisplay.appendChild(toggleContainer);
    }

    createClockFace() {
        // Create clock numbers
        for (let i = 1; i <= 12; i++) {
            const number = document.createElement('div');
            number.className = 'clock-number';
            const angle = (i * 30 - 90) * (Math.PI / 180);
            const x = this.radius * 0.85 * Math.cos(angle);
            const y = this.radius * 0.85 * Math.sin(angle);
            number.style.transform = `translate(${x}px, ${y}px)`;
            number.textContent = i;
            this.analogClock.appendChild(number);
        }

        // Create clock hands
        ['hour', 'minute', 'second'].forEach(hand => {
            const element = document.createElement('div');
            element.className = `clock-hand ${hand}-hand`;
            this.analogClock.appendChild(element);
        });
    }

    setupAnimationFrame() {
        const updateClock = () => {
            const now = new Date();
            if (this.clockDisplay.dataset.mode === 'digital') {
                this.updateDigitalDisplay(now);
            } else {
                this.updateAnalogDisplay(now);
            }
            this.animationFrame = requestAnimationFrame(updateClock);
        };
        this.animationFrame = requestAnimationFrame(updateClock);
    }

    updateDigitalDisplay(now) {
        const timeDiv = this.digitalClock.querySelector('.time');
        const dateDiv = this.digitalClock.querySelector('.date');
        
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();
        
        let timeString;
        if (this.is24Hour) {
            timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            const period = hours >= 12 ? 'PM' : 'AM';
            const displayHours = hours % 12 || 12;
            timeString = `${displayHours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')} ${period}`;
        }
        
        const dateString = now.toLocaleDateString(undefined, { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        timeDiv.textContent = timeString;
        dateDiv.textContent = dateString;
    }

    updateAnalogDisplay(now) {
        const hours = now.getHours() % 12;
        const minutes = now.getMinutes();
        const seconds = now.getSeconds();

        const hourAngle = (hours + minutes / 60) * 30 - 90;
        const minuteAngle = (minutes + seconds / 60) * 6 - 90;
        const secondAngle = seconds * 6 - 90;

        const hourHand = this.analogClock.querySelector('.hour-hand');
        const minuteHand = this.analogClock.querySelector('.minute-hand');
        const secondHand = this.analogClock.querySelector('.second-hand');

        hourHand.style.transform = `rotate(${hourAngle}deg)`;
        minuteHand.style.transform = `rotate(${minuteAngle}deg)`;
        secondHand.style.transform = `rotate(${secondAngle}deg)`;
    }

    handleResize() {
        const containerSize = Math.min(
            this.container.offsetWidth,
            this.container.offsetHeight
        );
        this.radius = containerSize * 0.4;
        this.analogClock.style.width = `${containerSize * 0.8}px`;
        this.analogClock.style.height = `${containerSize * 0.8}px`;
    }

    handleReducedMotion(e) {
        if (e.matches) {
            // Disable animations for clock hands
            this.analogClock.style.transition = 'none';
        } else {
            this.analogClock.style.transition = '';
        }
    }

    setupTouchSupport() {
        let startX;
        let startY;

        this.clockDisplay.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        this.clockDisplay.addEventListener('touchmove', (e) => {
            if (!startX || !startY) return;

            const diffX = startX - e.touches[0].clientX;
            const diffY = startY - e.touches[0].clientY;

            if (Math.abs(diffX) > 50 || Math.abs(diffY) > 50) {
                this.toggleMode();
                startX = null;
                startY = null;
            }
        });
    }

    addA11yFeatures() {
        // Add ARIA labels and roles
        this.clockDisplay.setAttribute('role', 'region');
        this.clockDisplay.setAttribute('aria-label', 'Interactive clock');
        
        // Add keyboard shortcuts
        this.clockDisplay.addEventListener('keydown', (e) => {
            if (e.key === 'm' || e.key === 'M') {
                this.toggleMode();
            }
        });
    }

    setupToggle() {
        const clockToggle = this.clockDisplay.querySelector('#clockToggle');
        const formatToggle = this.digitalClock.querySelector('.format-toggle');

        clockToggle.addEventListener('change', () => {
            this.toggleMode();
        });

        formatToggle.addEventListener('click', () => {
            this.is24Hour = !this.is24Hour;
            formatToggle.classList.add('clicked');
            // Update aria-label
            formatToggle.setAttribute('aria-label', 
                `Toggle to ${this.is24Hour ? '12' : '24'} hour format`
            );
            setTimeout(() => formatToggle.classList.remove('clicked'), 200);
            this.updateDigitalDisplay(new Date());
        });
    }

    // [Rest of the previous methods remain unchanged...]

    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        window.removeEventListener('resize', this.handleResize);
        window.matchMedia('(prefers-reduced-motion: reduce)').removeEventListener('change', this.handleReducedMotion);
        
        // Remove event listeners from focusable elements
        const focusableElements = this.clockDisplay.querySelectorAll(
            'button, [role="button"], input[type="checkbox"]'
        );
        focusableElements.forEach(element => {
            element.removeEventListener('keydown', null);
        });

        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Initialize clock when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const clockContainer = document.getElementById('clockContainer');
    if (clockContainer) {
        const clock = new Clock(clockContainer);
        
        // Store clock instance for potential cleanup
        window.clockInstance = clock;

        // Add error boundary
        window.addEventListener('error', (event) => {
            if (event.target.matches && event.target.matches('.clock-container, .clock-container *')) {
                console.error('Clock error:', event.error);
                
                // Attempt to recover by reinitializing
                if (window.clockInstance) {
                    window.clockInstance.destroy();
                    window.clockInstance = new Clock(clockContainer);
                }
            }
        });
    }
});
