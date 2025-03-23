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

        this.clockDisplay.dataset.mode = 'digital';
        this.digitalClock.style.display = 'block';
        this.digitalClock.classList.add('visible');
        this.analogClock.style.display = 'none';

        window.addEventListener('resize', this.handleResize.bind(this));
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', this.handleReducedMotion.bind(this));
        
        requestAnimationFrame(() => {
            this.clockDisplay.classList.add('visible');
        });
    }

    createClockElements() {
        this.clockDisplay = document.createElement('div');
        this.clockDisplay.className = 'clock-display';
        this.clockDisplay.style.opacity = '1';
        this.container.appendChild(this.clockDisplay);

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

        this.analogClock = document.createElement('div');
        this.analogClock.className = 'analog-clock';
        this.analogClock.setAttribute('role', 'presentation');
        this.clockDisplay.appendChild(this.analogClock);

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
        for (let i = 1; i <= 12; i++) {
            const number = document.createElement('div');
            number.className = 'clock-number';
            const angle = (i * 30 - 90) * (Math.PI / 180);
            const x = this.radius * 0.92 * Math.cos(angle);
            const y = this.radius * 0.92 * Math.sin(angle);
            number.style.transform = `translate(${x}px, ${y}px)`;
            number.textContent = i;
            this.analogClock.appendChild(number);
        }

        ['hour', 'minute', 'second'].forEach(hand => {
            const element = document.createElement('div');
            element.className = `clock-hand ${hand}-hand`;
            this.analogClock.appendChild(element);
        });
    }

    handleResize() {
        const containerSize = Math.min(
            this.container.offsetWidth,
            this.container.offsetHeight
        );
        this.radius = containerSize * 0.45;
        this.analogClock.style.width = `${containerSize * 0.8}px`;
        this.analogClock.style.height = `${containerSize * 0.8}px`;
    }

    // Rest of the existing methods remain unchanged
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

    toggleMode() {
        if (this.isTransitioning) return;
        this.isTransitioning = true;

        const isAnalog = this.clockDisplay.dataset.mode === 'analog';
        const newMode = isAnalog ? 'digital' : 'analog';
        
        this.clockDisplay.classList.add('transitioning');
        this.clockDisplay.dataset.mode = newMode;
        
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

        setTimeout(() => {
            this.clockDisplay.classList.remove('transitioning');
            this.isTransitioning = false;
            
            if (isAnalog) {
                this.digitalClock.querySelector('.format-toggle').focus();
            } else {
                this.analogClock.querySelector('.clock-face').focus();
            }
        }, 300);
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
            formatToggle.setAttribute('aria-label', 
                `Toggle to ${this.is24Hour ? '12' : '24'} hour format`
            );
            setTimeout(() => formatToggle.classList.remove('clicked'), 200);
            this.updateDigitalDisplay(new Date());
        });
    }

    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        window.removeEventListener('resize', this.handleResize);
        window.matchMedia('(prefers-reduced-motion: reduce)').removeEventListener('change', this.handleReducedMotion);
        
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

document.addEventListener('DOMContentLoaded', () => {
    const clockContainer = document.getElementById('clockContainer');
    if (clockContainer) {
        const clock = new Clock(clockContainer);
        window.clockInstance = clock;

        window.addEventListener('error', (event) => {
            if (event.target.matches && event.target.matches('.clock-container, .clock-container *')) {
                console.error('Clock error:', event.error);
                if (window.clockInstance) {
                    window.clockInstance.destroy();
                    window.clockInstance = new Clock(clockContainer);
                }
            }
        });
    }
});
