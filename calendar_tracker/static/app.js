document.addEventListener('DOMContentLoaded', function() {
    // Calendar initialization with monthly view
    var calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: function(info, successCallback, failureCallback) {
            const filters = {
                start: info.startStr,
                end: info.endStr,
                category: document.getElementById('filterCategory')?.value || '',
                priority: document.getElementById('filterPriority')?.value || '',
            };
            
            const params = new URLSearchParams(filters);
            fetch(`/habits?${params.toString()}`)
                .then(response => response.json())
                .then(events => successCallback(events))
                .catch(error => failureCallback(error));
        },
        editable: true,
        selectable: true,
        height: 'auto',
        slotMinTime: '06:00:00',
        slotMaxTime: '22:00:00',
        allDaySlot: true,
        eventDisplay: 'block',
        eventTimeFormat: {
            hour: 'numeric',
            minute: '2-digit',
            meridiem: 'short'
        },
        dateClick: function(info) {
            showDateFilters(info.date);
        },
        eventClick: showEventDetails,
        eventDrop: handleEventDrop,
        eventResize: handleEventResize
    });
    calendar.render();

    // Event handlers
    function handleEventDrop(info) {
        const event = info.event;
        const newDate = event.start.toISOString().split('T')[0];
        const newStart = event.start.toTimeString().split(' ')[0].substring(0, 5);
        const newEnd = event.end ? event.end.toTimeString().split(' ')[0].substring(0, 5) : null;

        fetch('/rescheduleHabit', {
            method: 'POST',
            body: new URLSearchParams({
                'id': event.id,
                'date': newDate,
                'start_time': newStart,
                'end_time': newEnd
            })
        }).then(response => {
            if (!response.ok) {
                info.revert();
                showError('Failed to reschedule');
            }
        });
    }

    function handleEventResize(info) {
        const event = info.event;
        const newEnd = event.end.toTimeString().split(' ')[0].substring(0, 5);

        fetch('/rescheduleHabit', {
            method: 'POST',
            body: new URLSearchParams({
                'id': event.id,
                'date': event.start.toISOString().split('T')[0],
                'start_time': event.start.toTimeString().split(' ')[0].substring(0, 5),
                'end_time': newEnd
            })
        }).then(response => {
            if (!response.ok) {
                info.revert();
                showError('Failed to update duration');
            }
        });
    }

    function showEventDetails(info) {
        const event = info.event;
        const descriptions = [
            event.extendedProps.description,
            `Category: ${event.extendedProps.category || 'None'}`,
            `Priority: ${event.extendedProps.priority || 'Normal'}`
        ].filter(Boolean).join('<br>');

        Swal.fire({
            title: event.title,
            html: `
                <div class="mb-3">
                    <p class="mb-2">${event.start.toLocaleDateString()}</p>
                    ${event.allDay ? '' : `
                        <p class="mb-2">${event.start.toLocaleTimeString()} - 
                        ${event.end ? event.end.toLocaleTimeString() : 'No end time'}</p>
                    `}
                    ${descriptions ? `<div class="mt-3">${descriptions}</div>` : ''}
                </div>
            `,
            icon: 'info',
            showDenyButton: true,
            showCancelButton: true,
            confirmButtonText: 'Edit',
            denyButtonText: 'Delete',
            cancelButtonText: 'Close',
            confirmButtonColor: '#1e40af',
            denyButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                showEditEventModal(event);
            } else if (result.isDenied) {
                deleteEvent(event);
            }
        });
    }

    function deleteEvent(event) {
        Swal.fire({
            title: 'Delete Habit?',
            text: 'This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it',
            cancelButtonText: 'Cancel',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch('/removeHabit', {
                    method: 'POST',
                    body: new URLSearchParams({ 'id': event.id })
                }).then(response => {
                    if (response.ok) {
                        event.remove();
                        calendar.refetchEvents();
                        Swal.fire('Deleted!', 'Habit has been removed.', 'success');
                    }
                });
            }
        });
    }

    // Chatbot functionality
    const chatbot = {
        modal: document.getElementById('chatbotModal'),
        messages: document.getElementById('chat-messages'),
        input: document.getElementById('chat-input'),
        sendBtn: document.getElementById('send-message'),
        icon: document.getElementById('chatbot-icon'),
        suggestions: document.querySelectorAll('.chat-suggestion'),
        bsModal: null,

        serviceMode: 'normal',

        init: function() {
            if (this.modal) {
                this.bsModal = new bootstrap.Modal(this.modal);
                this.setupEventListeners();
                this.setupSuggestions();
                this.checkServiceStatus();
            }
        },

        checkServiceStatus: function() {
            const statusElement = document.querySelector('.service-status');
            if (statusElement) {
                this.serviceMode = statusElement.textContent.includes('basic mode') ? 'fallback' : 'normal';
                if (this.serviceMode === 'fallback') {
                    this.addMessage("I'm currently running in basic mode. Some advanced features might be limited, but I can still help with your calendar and habits! 🤖", 'bot', 'status');
                }
            }
        },

        setupEventListeners: function() {
            this.icon.addEventListener('click', () => this.bsModal.show());
            this.sendBtn.addEventListener('click', () => this.sendMessage());
            this.input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            this.messages.addEventListener('scroll', () => {
                const isScrolledToBottom = this.messages.scrollHeight - this.messages.clientHeight <= this.messages.scrollTop + 1;
                this.messages.classList.toggle('scroll-indicator', !isScrolledToBottom);
            });

            this.modal.addEventListener('shown.bs.modal', () => {
                this.scrollToBottom();
                this.input.focus();
            });
        },

        setupSuggestions: function() {
            this.suggestions.forEach(suggestion => {
                suggestion.addEventListener('click', () => {
                    this.input.value = suggestion.textContent.trim();
                    this.sendMessage();
                });
            });
        },

        addMessage: function(text, sender, type = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender}-message`;
            if (type) messageDiv.setAttribute('data-type', type);
            messageDiv.textContent = text;

            if (sender === 'bot') {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing-indicator';
                for (let i = 0; i < 3; i++) {
                    const dot = document.createElement('div');
                    dot.className = 'typing-dot';
                    typingDiv.appendChild(dot);
                }
                this.messages.appendChild(typingDiv);

                setTimeout(() => {
                    typingDiv.remove();
                    this.messages.appendChild(messageDiv);
                    this.scrollToBottom();
                }, 1000);
            } else {
                this.messages.appendChild(messageDiv);
                this.scrollToBottom();
            }
        },

        sendMessage: function() {
            const message = this.input.value.trim();
            if (!message) return;

            this.addMessage(message, 'user');
            this.input.value = '';
            this.input.focus();

            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                setTimeout(() => {
                    let type = '';
                    if (data.response.includes('scheduled') || data.response.includes('Schedule')) {
                        type = 'calendar';
                        calendar.refetchEvents();
                    } else if (data.response.includes('🌟') || data.response.includes('✨')) {
                        type = 'motivation';
                    }
                    this.addMessage(data.response, 'bot', type);
                }, 500);
            })
            .catch(() => {
                setTimeout(() => {
                    this.addMessage(
                        "I apologize, but I'm having trouble responding right now. Please try again.",
                        'bot',
                        'error'
                    );
                }, 500);
            });
        },

        scrollToBottom: function() {
            this.messages.scrollTop = this.messages.scrollHeight;
        }
    };

    // Initialize chatbot
    chatbot.init();

    // Filter functionality
    const filterElements = {
        category: document.getElementById('filterCategory'),
        priority: document.getElementById('filterPriority'),
        startDate: document.getElementById('filterStartDate'),
        endDate: document.getElementById('filterEndDate'),
        applyBtn: document.getElementById('applyFilters'),
        clearBtn: document.getElementById('clearFilters')
    };

    if (filterElements.applyBtn) {
        filterElements.applyBtn.addEventListener('click', function() {
            calendar.refetchEvents();
        });
    }

    if (filterElements.clearBtn) {
        filterElements.clearBtn.addEventListener('click', function() {
            if (filterElements.category) filterElements.category.value = '';
            if (filterElements.priority) filterElements.priority.value = '';
            if (filterElements.startDate) filterElements.startDate.value = '';
            if (filterElements.endDate) filterElements.endDate.value = '';

            calendar.refetchEvents();

            Swal.fire({
                icon: 'success',
                title: 'Filters Cleared',
                text: 'Showing all events',
                timer: 1500,
                showConfirmButton: false
            });
        });
    }

    // Form submission
    const habitForm = document.getElementById('habitForm');
    if (habitForm) {
        habitForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const startTime = document.getElementById('start_time').value;
            const endTime = document.getElementById('end_time').value;
            const category = document.getElementById('category').value;
            
            if (startTime && endTime && startTime >= endTime) {
                showError('End time must be after start time');
                return;
            }

            const formData = new FormData(this);
            const categoryColors = {
                'health': '#10b981',
                'work': '#3b82f6',
                'personal': '#8b5cf6'
            };
            formData.append('color', categoryColors[category] || '#1e40af');

            fetch('/addHabit', {
                method: 'POST',
                body: formData
            })
            .then(response => response.ok ? response : Promise.reject())
            .then(() => {
                calendar.refetchEvents();
                habitForm.reset();
                document.getElementById('date').valueAsDate = new Date();
                
                Swal.fire({
                    icon: 'success',
                    title: 'Success!',
                    text: 'Habit added successfully',
                    timer: 2000,
                    showConfirmButton: false
                });
            })
            .catch(() => showError('Failed to add habit'));
        });
    }

    function showError(message) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message,
            timer: 2000
        });
    }

    // Date filter dialog
    function showDateFilters(date) {
        Swal.fire({
            title: 'Filter Events',
            html: `
                <div class="mb-3">
                    <h6>${date.toLocaleDateString()}</h6>
                    <div class="mb-3">
                        <label class="form-label">Category</label>
                        <select class="form-control" id="quickFilterCategory">
                            <option value="">All Categories</option>
                            <option value="health">Health</option>
                            <option value="work">Work</option>
                            <option value="personal">Personal</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Priority</label>
                        <select class="form-control" id="quickFilterPriority">
                            <option value="">All Priorities</option>
                            <option value="1">Low</option>
                            <option value="2">Medium</option>
                            <option value="3">High</option>
                        </select>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Apply Filters',
            confirmButtonColor: '#1e40af'
        }).then((result) => {
            if (result.isConfirmed) {
                const category = document.getElementById('quickFilterCategory').value;
                const priority = document.getElementById('quickFilterPriority').value;
                
                if (filterElements.category) {
                    filterElements.category.value = category;
                    filterElements.priority.value = priority;
                    calendar.refetchEvents();
                }
            }
        });
    }
});
