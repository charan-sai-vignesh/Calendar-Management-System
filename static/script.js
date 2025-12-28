// Calendar Management System - Frontend JavaScript

const API_BASE = '/api/events';
let currentWeekStart = null;
let editingEventId = null;
let currentTimezone = 'UTC';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeCalendar();
    setupEventListeners();
    setupNLP();
    loadWeeklyView();
});

function initializeCalendar() {
    // Set current week start (Monday of current week)
    const now = new Date();
    const day = now.getDay();
    const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust to Monday
    currentWeekStart = new Date(now.setDate(diff));
    currentWeekStart.setHours(0, 0, 0, 0);
    
    // Set default dates in form to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('event-start-date').value = today;
    document.getElementById('event-end-date').value = today;
}

function setupEventListeners() {
    document.getElementById('prev-week').addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() - 7);
        loadWeeklyView();
    });
    
    document.getElementById('next-week').addEventListener('click', () => {
        currentWeekStart.setDate(currentWeekStart.getDate() + 7);
        loadWeeklyView();
    });
    
    document.getElementById('timezone').addEventListener('change', (e) => {
        currentTimezone = e.target.value;
        loadWeeklyView();
    });
    
    document.getElementById('event-form').addEventListener('submit', handleFormSubmit);
    document.getElementById('cancel-btn').addEventListener('click', resetForm);
    document.getElementById('delete-btn').addEventListener('click', handleDeleteEvent);
}

function setupNLP() {
    const nlpInput = document.getElementById('nlp-input');
    const nlpParseBtn = document.getElementById('nlp-parse-btn');
    const nlpToggle = document.getElementById('toggle-nlp');
    const nlpContainer = document.getElementById('nlp-container');
    
    // Toggle NLP box
    nlpToggle.addEventListener('click', () => {
        if (nlpContainer.classList.contains('hidden')) {
            nlpContainer.classList.remove('hidden');
            nlpToggle.textContent = 'Hide';
        } else {
            nlpContainer.classList.add('hidden');
            nlpToggle.textContent = 'Show';
        }
    });
    
    // Parse on button click
    nlpParseBtn.addEventListener('click', parseNaturalLanguage);
    
    // Parse on Enter key
    nlpInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            parseNaturalLanguage();
        }
    });
}

function parseNaturalLanguage() {
    const nlpInput = document.getElementById('nlp-input');
    const nlpParseBtn = document.getElementById('nlp-parse-btn');
    const nlpPreview = document.getElementById('nlp-preview');
    const text = nlpInput.value.trim();
    
    if (!text) {
        showMessage('Please enter some text to parse', true);
        return;
    }
    
    nlpParseBtn.disabled = true;
    nlpParseBtn.textContent = 'Parsing...';
    nlpPreview.style.display = 'none';
    
    fetch('/api/nlp/parse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text,
            timezone: currentTimezone || 'UTC'
        })
    })
    .then(async response => {
        const data = await response.json();
        if (response.ok) {
            displayNLPPreview(data, text);
        } else {
            showMessage(data.error || 'Failed to parse text', true);
        }
    })
    .catch(error => {
        console.error('NLP parse error:', error);
        showMessage('Error parsing natural language', true);
    })
    .finally(() => {
        nlpParseBtn.disabled = false;
        nlpParseBtn.textContent = 'Parse';
    });
}

function displayNLPPreview(parsed, originalText) {
    const nlpPreview = document.getElementById('nlp-preview');
    
    // Store parsed data in a data attribute for safer access
    const parsedJson = JSON.stringify(parsed);
    nlpPreview.setAttribute('data-parsed', parsedJson);
    
    let html = `<h4>Parsed Event Details (Confidence: ${(parsed.confidence * 100).toFixed(0)}%)</h4>`;
    html += `<div class="nlp-preview-item"><strong>Title:</strong> ${parsed.title}</div>`;
    html += `<div class="nlp-preview-item"><strong>Date:</strong> ${parsed.start_date} ${parsed.start_time ? '(' + parsed.start_time + ')' : ''}</div>`;
    if (parsed.end_time && parsed.end_time !== parsed.start_time) {
        html += `<div class="nlp-preview-item"><strong>End:</strong> ${parsed.end_time}</div>`;
    }
    
    html += `<div class="nlp-preview-actions">`;
    html += `<button class="nlp-action-btn primary" onclick="fillFormFromNLPData()">Use This → Fill Form</button>`;
    html += `<button class="nlp-action-btn secondary" onclick="createEventFromNLPData()">Create Directly</button>`;
    html += `</div>`;
    
    nlpPreview.innerHTML = html;
    nlpPreview.style.display = 'block';
}

function fillFormFromNLPData() {
    const nlpPreview = document.getElementById('nlp-preview');
    const parsedJson = nlpPreview.getAttribute('data-parsed');
    if (!parsedJson) return;
    
    try {
        const parsed = JSON.parse(parsedJson);
        fillFormFromNLP(parsed);
    } catch (e) {
        console.error('Error parsing NLP data:', e);
        showMessage('Error loading parsed data', true);
    }
}

function createEventFromNLPData() {
    const nlpPreview = document.getElementById('nlp-preview');
    const parsedJson = nlpPreview.getAttribute('data-parsed');
    if (!parsedJson) return;
    
    try {
        const parsed = JSON.parse(parsedJson);
        createEventFromNLP(parsed);
    } catch (e) {
        console.error('Error parsing NLP data:', e);
        showMessage('Error loading parsed data', true);
    }
}

function fillFormFromNLP(parsed) {
    document.getElementById('event-title').value = parsed.title || '';
    document.getElementById('event-start-date').value = parsed.start_date || '';
    document.getElementById('event-start-time').value = parsed.start_time || '14:00';
    document.getElementById('event-end-date').value = parsed.end_date || parsed.start_date || '';
    document.getElementById('event-end-time').value = parsed.end_time || parsed.start_time || '15:00';
    
    // Clear NLP input
    document.getElementById('nlp-input').value = '';
    document.getElementById('nlp-preview').style.display = 'none';
    
    // Focus on form
    document.getElementById('event-title').focus();
    showMessage('Form filled! Review and click "Create Event"');
}

async function createEventFromNLP(parsed) {
    if (!parsed.start_date || !parsed.start_time) {
        showMessage('Missing required date/time information', true);
        return;
    }
    
    console.log('Creating event from NLP:', parsed);
    
    const startDateTime = combineDateTime(parsed.start_date, parsed.start_time);
    const endDateTime = combineDateTime(parsed.end_date || parsed.start_date, parsed.end_time || parsed.start_time);
    
    const eventData = {
        title: parsed.title || 'Untitled Event',
        description: '',
        start_time: startDateTime,
        end_time: endDateTime,
        timezone: currentTimezone || 'UTC'
    };
    
    console.log('Event data to send:', eventData);
    
    try {
        const response = await fetch(API_BASE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        });
        
        const data = await response.json();
        console.log('API Response:', response.status, data);
        
        if (response.ok) {
            showMessage('Event created successfully from natural language!');
            document.getElementById('nlp-input').value = '';
            document.getElementById('nlp-preview').style.display = 'none';
            resetForm();
            
            // Navigate to the week containing the event date
            const eventDateStr = parsed.start_date; // YYYY-MM-DD format
            const eventDate = new Date(eventDateStr + 'T00:00:00');
            
            // Calculate Monday of that week (weekday 0 = Monday)
            const day = eventDate.getDay();
            const diff = eventDate.getDate() - day + (day === 0 ? -6 : 1); // Adjust to Monday
            const eventWeekStart = new Date(eventDate);
            eventWeekStart.setDate(diff);
            eventWeekStart.setHours(0, 0, 0, 0);
            
            // Update current week and reload
            currentWeekStart = eventWeekStart;
            loadWeeklyView();
        } else {
            if (data.conflicts) {
                displayConflictError(data);
            } else {
                showMessage(data.error || 'Error creating event', true);
                console.error('Error response:', data);
            }
        }
    } catch (error) {
        console.error('Error creating event:', error);
        showMessage('Error creating event: ' + error.message, true);
    }
}

function loadWeeklyView() {
    // Convert current week start to selected timezone's date
    const tz = currentTimezone || 'UTC';
    const localDateStr = currentWeekStart.toLocaleDateString('en-CA', { timeZone: tz }); // YYYY-MM-DD
    const url = `${API_BASE}/week?start_date=${localDateStr}&timezone=${encodeURIComponent(tz)}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayWeekRange(data.start_of_week, data.end_of_week);
            renderCalendar(data.events, data.start_of_week);
        })
        .catch(error => {
            console.error('Error loading weekly view:', error);
            showMessage('Error loading calendar', true);
        });
}

function displayWeekRange(startStr, endStr) {
    const tz = currentTimezone || 'UTC';
    const start = new Date(startStr);
    const end = new Date(endStr);
    const options = { 
        timeZone: tz,
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    };
    const rangeText = `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`;
    document.getElementById('week-range').textContent = rangeText;
}

function renderCalendar(events, weekStartStr) {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    
    const tz = currentTimezone || 'UTC';
    const weekStart = new Date(weekStartStr);
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    for (let i = 0; i < 7; i++) {
        // Create date for this day in the selected timezone
        const dayDate = new Date(weekStart);
        dayDate.setUTCDate(weekStart.getUTCDate() + i);
        
        // Get the date string in the selected timezone
        const dayDateStr = dayDate.toLocaleDateString('en-CA', { timeZone: tz }); // YYYY-MM-DD format
        
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        dayHeader.textContent = days[i];
        
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = dayDate.toLocaleDateString('en-US', { 
            timeZone: tz,
            month: 'short', 
            day: 'numeric' 
        });
        
        dayElement.appendChild(dayHeader);
        dayElement.appendChild(dayNumber);
        
        // Add events for this day (compare dates in the selected timezone)
        const dayEvents = events.filter(event => {
            const eventStart = new Date(event.start_time);
            const eventDateStr = eventStart.toLocaleDateString('en-CA', { timeZone: tz });
            return eventDateStr === dayDateStr;
        });
        
        dayEvents.forEach(event => {
            const eventElement = document.createElement('div');
            eventElement.className = 'event-item';
            eventElement.textContent = `${formatTime(event.start_time)} - ${event.title}`;
            eventElement.title = `${event.title}\n${event.description || ''}\n${formatDateTime(event.start_time)} - ${formatDateTime(event.end_time)}`;
            eventElement.addEventListener('click', () => editEvent(event));
            dayElement.appendChild(eventElement);
        });
        
        grid.appendChild(dayElement);
    }
}

function formatTime(dateTimeStr) {
    const tz = currentTimezone || 'UTC';
    const date = new Date(dateTimeStr);
    return date.toLocaleTimeString('en-US', { 
        timeZone: tz,
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function formatDateTime(dateTimeStr) {
    const tz = currentTimezone || 'UTC';
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', { 
        timeZone: tz,
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    const title = document.getElementById('event-title').value;
    const description = document.getElementById('event-description').value;
    const startDate = document.getElementById('event-start-date').value;
    const startTime = document.getElementById('event-start-time').value;
    const endDate = document.getElementById('event-end-date').value;
    const endTime = document.getElementById('event-end-time').value;
    
    // Combine date and time, then convert to ISO with timezone
    const startDateTime = combineDateTime(startDate, startTime);
    const endDateTime = combineDateTime(endDate, endTime);
    
    const eventData = {
        title,
        description,
        start_time: startDateTime,
        end_time: endDateTime,
        timezone: currentTimezone
    };
    
    const url = editingEventId ? `${API_BASE}/${editingEventId}` : API_BASE;
    const method = editingEventId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(eventData)
    })
    .then(async response => {
        const data = await response.json();
        if (response.ok) {
            showMessage(editingEventId ? 'Event updated successfully' : 'Event created successfully');
            resetForm();
            loadWeeklyView();
            document.getElementById('conflict-message').style.display = 'none';
        } else {
            if (data.conflicts) {
                displayConflictError(data);
            } else {
                const errorMsg = data.error || 'Error saving event';
                console.error('API Error:', errorMsg, data);
                showMessage(errorMsg, true);
            }
        }
    })
    .catch(error => {
        console.error('Error saving event:', error);
        showMessage('Error saving event: ' + error.message, true);
    });
}

function combineDateTime(dateStr, timeStr) {
    // Create ISO string with local date/time, timezone will be handled by backend
    return `${dateStr}T${timeStr}:00`;
}

function displayConflictError(data) {
    const conflictMsg = document.getElementById('conflict-message');
    let html = `<strong>⚠️ Conflict Detected:</strong><br>`;
    
    if (data.conflicts && data.conflicts.length > 0) {
        html += `<p>This event overlaps with existing event(s):</p><ul style="margin: 10px 0; padding-left: 25px;">`;
        data.conflicts.forEach(conflict => {
            try {
                const start = new Date(conflict.start_time_utc);
                const end = new Date(conflict.end_time_utc);
                const tz = document.getElementById('timezone').value || 'UTC';
                
                // Format the dates
                const startTime = start.toLocaleString('en-US', { 
                    timeZone: tz, 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
                const endTime = end.toLocaleString('en-US', { 
                    timeZone: tz, 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
                
                html += `<li style="margin: 8px 0;"><strong>${conflict.title || 'Untitled Event'}</strong><br>${startTime} - ${endTime}</li>`;
            } catch (e) {
                // Fallback if date parsing fails
                html += `<li style="margin: 8px 0;"><strong>${conflict.title || 'Untitled Event'}</strong><br>${conflict.start_time_utc}</li>`;
            }
        });
        html += `</ul><p><strong>Please adjust your event time to avoid conflicts.</strong></p>`;
    } else {
        html += `<p>This event conflicts with an existing event. Please choose a different time.</p>`;
    }
    
    conflictMsg.innerHTML = html;
    conflictMsg.style.display = 'block';
    
    // Scroll to the conflict message
    setTimeout(() => {
        conflictMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

function editEvent(event) {
    editingEventId = event.id;
    document.getElementById('form-title').textContent = 'Edit Event';
    document.getElementById('event-id').value = event.id;
    document.getElementById('event-title').value = event.title;
    document.getElementById('event-description').value = event.description || '';
    
    const tz = currentTimezone || 'UTC';
    const startDate = new Date(event.start_time);
    const endDate = new Date(event.end_time);
    
    // Convert to selected timezone for display
    const startDateStr = startDate.toLocaleDateString('en-CA', { timeZone: tz }); // YYYY-MM-DD
    const startTimeStr = startDate.toLocaleTimeString('en-US', { timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false });
    const endDateStr = endDate.toLocaleDateString('en-CA', { timeZone: tz }); // YYYY-MM-DD
    const endTimeStr = endDate.toLocaleTimeString('en-US', { timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false });
    
    document.getElementById('event-start-date').value = startDateStr;
    document.getElementById('event-start-time').value = startTimeStr;
    document.getElementById('event-end-date').value = endDateStr;
    document.getElementById('event-end-time').value = endTimeStr;
    
    document.getElementById('submit-btn').textContent = 'Update Event';
    document.getElementById('cancel-btn').style.display = 'inline-block';
    document.getElementById('delete-btn').style.display = 'inline-block';
    
    // Scroll to form
    document.querySelector('.event-form-section').scrollIntoView({ behavior: 'smooth' });
}

function resetForm() {
    editingEventId = null;
    document.getElementById('event-form').reset();
    document.getElementById('form-title').textContent = 'Create New Event';
    document.getElementById('submit-btn').textContent = 'Create Event';
    document.getElementById('cancel-btn').style.display = 'none';
    document.getElementById('delete-btn').style.display = 'none';
    document.getElementById('conflict-message').style.display = 'none';
    
    // Reset dates to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('event-start-date').value = today;
    document.getElementById('event-end-date').value = today;
}

function handleDeleteEvent() {
    if (!editingEventId || !confirm('Are you sure you want to delete this event?')) {
        return;
    }
    
    fetch(`${API_BASE}/${editingEventId}`, {
        method: 'DELETE'
    })
    .then(async response => {
        const data = await response.json();
        if (response.ok) {
            showMessage('Event deleted successfully');
            resetForm();
            loadWeeklyView();
        } else {
            showMessage(data.error || 'Error deleting event', true);
        }
    })
    .catch(error => {
        console.error('Error deleting event:', error);
        showMessage('Error deleting event', true);
    });
}

function showMessage(message, isError = false) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = message;
    messageEl.style.display = 'block';
    messageEl.style.background = isError ? '#e74c3c' : '#2ecc71';
    
    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 3000);
}

