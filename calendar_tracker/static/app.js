document.addEventListener('DOMContentLoaded', function() {
    // Calendar initialization
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

    // Event click handler
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

    // Show date filters
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
                
                if (document.getElementById('filterCategory')) {
                    document.getElementById('filterCategory').value = category;
                    document.getElementById('filterPriority').value = priority;
                    calendar.refetchEvents();
                }
            }
        });
    }

    // Event drag and drop handler
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

    // Event resize handler
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

    // Delete event handler
    function deleteEvent(event) {
        Swal.fire({
            title: 'Delete Habit?',
            text: 'This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it',
            cancelButtonText: 'Cancel',
            confirmButtonColor: '#dc3545'
        }).then((deleteResult) => {
            if (deleteResult.isConfirmed) {
                fetch('/removeHabit', {
                    method: 'POST',
                    body: new URLSearchParams({ 'id': event.id })
                }).then(response => {
                    if (response.ok) {
                        event.remove();
                        Swal.fire('Deleted!', 'Habit has been removed.', 'success');
                    }
                });
            }
        });
    }

    // Show error message
    function showError(message) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message,
            timer: 2000
        });
    }

    // Filter handlers
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
            // Reset all filter values
            if (filterElements.category) filterElements.category.value = '';
            if (filterElements.priority) filterElements.priority.value = '';
            if (filterElements.startDate) filterElements.startDate.value = '';
            if (filterElements.endDate) filterElements.endDate.value = '';

            // Refresh calendar events
            calendar.refetchEvents();

            // Show feedback
            Swal.fire({
                icon: 'success',
                title: 'Filters Cleared',
                text: 'Showing all events',
                timer: 1500,
                showConfirmButton: false
            });
        });
    }

    // Add event handler
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
            
            // Add color based on category
            const categoryColors = {
                'health': '#10b981',
                'work': '#3b82f6',
                'personal': '#8b5cf6'
            };
            formData.append('color', categoryColors[category] || '#1e40af');

            fetch('/addHabit', {
                method: 'POST',
                body: formData
            }).then(response => response.ok ? response : Promise.reject())
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
});
