// Get DOM elements
const modal = document.getElementById('bookingModal');
const closeBtn = document.querySelector('.close-modal');
const bookingForm = document.getElementById('bookingForm');
const activityIdInput = document.getElementById('activityId');
const activityNameSpan = document.getElementById('activityName');
const dateInput = document.getElementById('bookingDate');
const timeSelect = document.getElementById('bookingTime');
const participantsInput = document.getElementById('participants');

// Helper function to check if a date is in the current week
function isCurrentWeek(date) {
    const today = new Date();
    const firstDayOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
    const lastDayOfWeek = new Date(firstDayOfWeek);
    lastDayOfWeek.setDate(lastDayOfWeek.getDate() + 6);
    
    return date >= firstDayOfWeek && date <= lastDayOfWeek;
}

// Helper function to format time
function formatTime(time) {
    const [hours, minutes] = time.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
    });
}

// Helper function to format time range
function formatTimeRange(startTime, endTime) {
    return `${formatTime(startTime)} - ${formatTime(endTime)}`;
}

// Set minimum date to today
const today = new Date().toISOString().split('T')[0];
dateInput.min = today;

// Time slots
const timeSlots = [
    '09:00', '10:00', '11:00', '12:00', '13:00', 
    '14:00', '15:00', '16:00', '17:00'
];

let selectedActivity = null;
let selectedTimeSlot = null;
let flatpickrInstance = null;
let currentActivity = null;
let maxParticipants = 1;

// Activity Category Filtering
document.addEventListener('DOMContentLoaded', function() {
    // Initialize activity filters
    const filterButtons = document.querySelectorAll('.filter-btn');
    const activitySections = document.querySelectorAll('.activity-type-section');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filter = button.dataset.filter;
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Filter activity sections
            activitySections.forEach(section => {
                if (filter === 'all' || section.dataset.type === filter) {
                    section.style.display = 'flex';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    });

    // Check activity availability on page load
    checkActivitiesAvailability();
});

function checkActivitiesAvailability() {
    const activities = document.querySelectorAll('.activity-card');
    activities.forEach(activity => {
        const activityId = activity.dataset.activityId;
        fetch(`/check-activity-availability?activity_id=${activityId}`)
            .then(response => response.json())
            .then(data => {
                const statusBadge = activity.querySelector('.activity-status');
                const bookBtn = activity.querySelector('.book-btn');
                
                if (!data.available) {
                    statusBadge.className = 'activity-status status-booked';
                    statusBadge.textContent = 'Booked';
                    bookBtn.disabled = true;
                    bookBtn.textContent = data.message;
                    bookBtn.classList.add('disabled');
                } else if (data.unavailable) {
                    statusBadge.className = 'activity-status status-unavailable';
                    statusBadge.textContent = 'Unavailable';
                    bookBtn.disabled = true;
                    bookBtn.textContent = 'Not Available';
                    bookBtn.classList.add('disabled');
                }
            })
            .catch(error => console.error('Error checking activity availability:', error));
    });
}

// Participant controls
function incrementParticipants() {
    const input = document.getElementById('participants');
    const currentValue = parseInt(input.value);
    const maxValue = parseInt(input.max);
    
    if (currentValue < maxValue) {
        input.value = currentValue + 1;
        animateValue(input);
    }
}

function decrementParticipants() {
    const input = document.getElementById('participants');
    const currentValue = parseInt(input.value);
    const minValue = parseInt(input.min);
    
    if (currentValue > minValue) {
        input.value = currentValue - 1;
        animateValue(input);
    }
}

// Helper function to animate value changes
function animateValue(element) {
    element.style.transform = 'scale(1.2)';
    setTimeout(() => {
        element.style.transform = 'scale(1)';
    }, 200);
}

// Initialize date picker
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Flatpickr with custom styling for next week dates
    const bookingDatePicker = flatpickr("#bookingDate", {
        inline: true,
        mode: "single",
        dateFormat: "Y-m-d",
        minDate: "today",
        showMonths: 1,
        disable: [
            function(date) {
                // Disable if not in current week
                return !isCurrentWeek(date);
            }
        ],
        onChange: function(selectedDates, dateStr) {
            if (selectedDates.length > 0) {
                const activityId = activityIdInput.value;
                loadTimeSlots(activityId, dateStr);
            }
        },
        onMonthChange: function(selectedDates, dateStr, instance) {
            // Refresh the disabled dates when month changes
            instance.redraw();
        }
    });

    // Add custom CSS for the disabled next week dates
    const style = document.createElement('style');
    style.textContent = `
        .nextWeek-disabled {
            color: #ccc !important;
            cursor: not-allowed !important;
            background-color: #f5f5f5 !important;
        }
        .nextWeek-disabled:hover {
            background-color: #f5f5f5 !important;
        }
    `;
    document.head.appendChild(style);

    // Initialize activity filters
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterActivities(btn.dataset.type);
        });
    });

    // Initialize participants input
    document.getElementById('participants').value = 1;
    updateSummary('participants', 1);
});

// Filter activities by type
function filterActivities(type) {
    const cards = document.querySelectorAll('.activity-card');
    cards.forEach(card => {
        if (type === 'all' || card.dataset.type === type) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Open booking modal
function openBookingModal(activityData) {
    try {
        // Parse activity data if it's a string
        currentActivity = typeof activityData === 'string' ? JSON.parse(activityData) : activityData;
        
        // Update modal content
        document.getElementById('modalTitle').textContent = `Book ${currentActivity.name}`;
        document.getElementById('activityId').value = currentActivity.id;
        
        // Set maximum participants
        const participantsInput = document.getElementById('participants');
        participantsInput.max = currentActivity.capacity;
        participantsInput.placeholder = `Max ${currentActivity.capacity} people`;
        
        // Reset form and time slots
        document.getElementById('bookingForm').reset();
        document.getElementById('timeSlots').innerHTML = '';
        selectedTimeSlot = null;
        
        // Show modal
        document.getElementById('bookingModal').style.display = 'block';
        
        // Check initial availability
        checkAvailability();
    } catch (error) {
        console.error('Error opening booking modal:', error);
        alert('Sorry, there was an error. Please try again.');
    }
}

// Close booking modal
function closeBookingModal() {
    document.getElementById('bookingModal').style.display = 'none';
    currentActivity = null;
    selectedTimeSlot = null;
}

// Close success modal
function closeSuccessModal() {
    document.getElementById('successModal').style.display = 'none';
    location.reload(); // Refresh to update availability
}

// Adjust participants
function adjustParticipants(change) {
    const input = document.getElementById('participants');
    const newValue = parseInt(input.value) + change;
    
    if (newValue >= 1 && newValue <= maxParticipants) {
        input.value = newValue;
        updateSummary('participants', newValue);
    }
}

// Load time slots
function loadTimeSlots(activityId, date) {
    const timeSlotsContainer = document.getElementById('timeSlots');
    if (!timeSlotsContainer) return;
    
    timeSlotsContainer.innerHTML = '<div class="loading">Loading available times...</div>';

    fetch(`/get-time-slots?activity_id=${activityId}&date=${date}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Time slots response:', data); // Debug log
            timeSlotsContainer.innerHTML = '';
            
            if (data.error) {
                timeSlotsContainer.innerHTML = `<div class="error">${data.error}</div>`;
                return;
            }

            if (!data.length) {
                timeSlotsContainer.innerHTML = '<div class="no-slots">No available time slots for this date</div>';
                return;
            }

            // Create time slots grid
            const grid = document.createElement('div');
            grid.className = 'time-slots-grid';

            data.forEach(slot => {
                const timeSlot = document.createElement('div');
                timeSlot.className = 'time-slot' + (slot.available ? '' : ' booked');
                
                const time = document.createElement('span');
                time.className = 'time';
                time.textContent = `${formatTime(slot.start_time)} - ${formatTime(slot.end_time)}`;
                
                const status = document.createElement('span');
                status.className = 'status';
                status.textContent = slot.available ? 'Available' : 'Booked';
                
                const icon = document.createElement('i');
                icon.className = slot.available ? 'fas fa-check' : 'fas fa-times';
                icon.style.marginRight = '5px';
                status.prepend(icon);

                timeSlot.appendChild(time);
                timeSlot.appendChild(status);

                if (slot.available) {
                    timeSlot.addEventListener('click', () => {
                        selectTimeSlot(timeSlot, slot.start_time);
                        updateSummary('time', `${formatTime(slot.start_time)} - ${formatTime(slot.end_time)}`);
                    });
                }

                grid.appendChild(timeSlot);
            });

            timeSlotsContainer.appendChild(grid);
        })
        .catch(error => {
            console.error('Error loading time slots:', error);
            timeSlotsContainer.innerHTML = '<div class="error">Failed to load time slots. Please try again.</div>';
        });
}

// Select time slot
function selectTimeSlot(element, time) {
    // Remove selection from all slots
    document.querySelectorAll('.time-slot').forEach(slot => {
        slot.classList.remove('selected');
    });
    
    // Add selection to clicked slot
    element.classList.add('selected');
    
    // Update hidden input
    const timeInput = document.createElement('input');
    timeInput.type = 'hidden';
    timeInput.name = 'time';
    timeInput.value = time;
    
    // Remove any existing time input
    const existingTimeInput = document.querySelector('input[name="time"]');
    if (existingTimeInput) {
        existingTimeInput.remove();
    }
    
    // Add new time input
    document.getElementById('bookingForm').appendChild(timeInput);
}

// Update booking summary
function updateSummary(field, value) {
    const summaryElement = document.getElementById(`summary${field.charAt(0).toUpperCase() + field.slice(1)}`);
    if (summaryElement) {
        summaryElement.textContent = value;
    }
}

// Check activity availability
async function checkAvailability() {
    const date = document.getElementById('bookingDate').value;
    if (!date || !currentActivity) return;

    try {
        const response = await fetch(`/check-activity-availability?activity_id=${currentActivity.id}&date=${date}`, {
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        });

        if (!response.ok) throw new Error('Network response was not ok');
        
        const availableSlots = await response.json();
        displayTimeSlots(availableSlots);
    } catch (error) {
        console.error('Error checking availability:', error);
        document.getElementById('timeSlots').innerHTML = '<p class="error">Error checking availability. Please try again.</p>';
    }
}

// Display time slots
function displayTimeSlots(availableSlots) {
    const timeSlotsContainer = document.getElementById('timeSlots');
    timeSlotsContainer.innerHTML = '';

    if (!availableSlots || availableSlots.length === 0) {
        timeSlotsContainer.innerHTML = '<p>No time slots available for this date.</p>';
        return;
    }

    availableSlots.forEach(slot => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'time-slot';
        button.textContent = slot.time;
        button.dataset.time = slot.time;
        
        if (slot.available) {
            button.addEventListener('click', () => selectTimeSlot(button, slot.start_time));
        } else {
            button.classList.add('unavailable');
            button.disabled = true;
        }
        
        timeSlotsContainer.appendChild(button);
    });
}

// Handle form submission
document.getElementById('bookingForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const selectedTimeSlot = document.querySelector('.time-slot.selected');
    if (!selectedTimeSlot) {
        showError('Please select a time slot');
        return;
    }

    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    fetch('/booking/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessModal();
            setTimeout(() => {
                window.location.href = '/profile';  // Redirect to profile page after successful booking
            }, 2000);
        } else {
            showError(data.error || 'Failed to create booking. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError(error.message || 'Failed to create booking. Please try again.');
    });
});

// Close modals when clicking outside
window.addEventListener('click', function(e) {
    const bookingModal = document.getElementById('bookingModal');
    const successModal = document.getElementById('successModal');
    
    if (e.target === bookingModal) {
        closeBookingModal();
    } else if (e.target === successModal) {
        closeSuccessModal();
    }
});

// Close modals with escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeBookingModal();
        closeSuccessModal();
    }
});

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    const container = document.querySelector('.booking-form');
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => {
        errorDiv.style.opacity = '0';
        setTimeout(() => errorDiv.remove(), 300);
    }, 3000);
}

// Show success modal
function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.add('show');
    
    // Redirect after delay
    setTimeout(() => {
        window.location.href = '/my-bookings';
    }, 2000);
} 