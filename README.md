# Calendar Management System

A minimal calendar management system that allows users to create, view, and manage calendar events while correctly handling time conflicts and time zones.

## Features

- **Event Management**: Create, update, and delete calendar events
- **Conflict Detection**: Automatically prevents overlapping events
- **Weekly Calendar View**: Navigate forward and backward through weeks
- **Timezone Support**: Full timezone-aware date/time handling
- **User-Friendly UI**: Clean, modern interface for managing events

## Architecture Overview
### Tech Stack

- **Backend**: Python 3.x with Flask (RESTful API)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Database**: SQLite (file-based, no external dependencies)
- **Timezone Handling**: Python `pytz` library

### System Components

#### 1. Backend API (`app.py`)

The Flask application provides RESTful endpoints:

- `GET /api/events` - Retrieve events within a date range
- `GET /api/events/week` - Get weekly view with timezone support
- `POST /api/events` - Create a new event
- `PUT /api/events/<id>` - Update an existing event
- `DELETE /api/events/<id>` - Delete an event

**Key Design Decisions:**

- **UTC Storage**: All timestamps are stored in UTC in the database to ensure consistency
- **Timezone Conversion**: User timezone preferences are applied at the API layer when returning data
- **Conflict Detection**: Overlap checking is performed in UTC to avoid timezone-related bugs
- **Validation**: Start time must be before end time; conflicts are detected before save

#### 2. Database Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_time_utc TEXT NOT NULL,  -- ISO format UTC datetime
    end_time_utc TEXT NOT NULL,     -- ISO format UTC datetime
    timezone TEXT NOT NULL,         -- Original timezone of creation
    created_at TEXT NOT NULL
)
```

**Storage Strategy:**
- ISO 8601 format strings for UTC timestamps (e.g., "2024-01-15T10:30:00Z")
- Timezone string stored separately (e.g., "America/New_York")
- Enables timezone conversions without data loss

#### 3. Frontend (`static/`)

- **Single Page Application**: No page reloads, smooth user experience
- **Weekly Grid View**: Visual calendar showing 7 days with events
- **Event Form**: Create/edit events with date/time pickers
- **Conflict Display**: Clear error messages when conflicts occur

**User Interactions:**
- Navigate weeks with Previous/Next buttons
- Select timezone from dropdown (affects all views)
- Click events to edit or delete
- Form validation prevents invalid submissions

### Conflict Detection Algorithm

The system detects overlapping events using interval overlap logic:

```python
Two events overlap if:
- Event A starts before Event B ends AND
- Event A ends after Event B starts
```

This is checked in UTC to avoid timezone edge cases. The algorithm handles:
- Partial overlaps (one event starts during another)
- Complete containment (one event entirely within another)
- Adjacent events (no overlap, but touching at boundaries)

### Timezone Handling

**Challenge**: Users may create events in different timezones, and we need to display them correctly.

**Solution**:
1. **Input**: User provides date/time in their selected timezone
2. **Conversion**: Backend converts to UTC before storage
3. **Display**: Backend converts UTC back to user's selected timezone for display
4. **Consistency**: All conflict checks performed in UTC

**Example Flow**:
- User in PST (UTC-8) creates event: "2024-01-15 14:00" PST
- Stored as: "2024-01-15T22:00:00Z" (UTC)
- User switches to EST (UTC-5) and views
- Displayed as: "2024-01-15 17:00" EST

## Setup and Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone or navigate to the project directory**:
   ```bash
   cd Calendar
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Open your browser**:
   Navigate to `http://127.0.0.1:5000`

The database (`calendar.db`) will be automatically created on first run.

## Usage Examples

### Creating an Event

1. Fill in the event form:
   - **Title**: "Team Meeting"
   - **Description**: "Weekly sync"
   - **Start Date**: 2024-01-15
   - **Start Time**: 14:00
   - **End Date**: 2024-01-15
   - **End Time**: 15:00
   - **Timezone**: (selected from dropdown)

2. Click "Create Event"

3. The event appears in the weekly calendar view

### Viewing Events

- Use "Previous Week" and "Next Week" buttons to navigate
- Events are displayed in the calendar grid
- Click any event to edit or delete

### Handling Conflicts

If you try to create an overlapping event:
- System shows error message with conflicting event details
- Event is not created
- Modify times to resolve conflict

## API Examples

### Create Event (cURL)

```bash
curl -X POST http://127.0.0.1:5000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting",
    "description": "Team sync",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T15:00:00",
    "timezone": "America/New_York"
  }'
```

### Get Weekly View

```bash
curl "http://127.0.0.1:5000/api/events/week?start_date=2024-01-15&timezone=America/New_York"
```

### Update Event

```bash
curl -X PUT http://127.0.0.1:5000/api/events/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Meeting",
    "start_time": "2024-01-15T15:00:00",
    "end_time": "2024-01-15T16:00:00",
    "timezone": "America/New_York"
  }'
```

### Delete Event

```bash
curl -X DELETE http://127.0.0.1:5000/api/events/1
```

## Key Design Decisions

### 1. Why SQLite?

- **Simplicity**: No server setup required, file-based
- **Persistence**: Data survives application restarts
- **Portability**: Single file, easy to backup/move
- **Sufficient**: Handles the scale requirements for this project

### 2. Why UTC Storage?

- **Consistency**: All comparisons in same timezone
- **Accuracy**: Avoids DST and timezone conversion bugs
- **Standards**: Industry best practice for datetime storage

### 3. Why RESTful API?

- **Separation**: Clear boundary between frontend and backend
- **Testability**: Easy to test endpoints independently
- **Extensibility**: Can build mobile apps, CLI tools, etc.

### 4. Why Vanilla JavaScript?

- **Simplicity**: No build process or framework overhead
- **Clarity**: Easy to understand and modify
- **Performance**: Fast load times, no dependencies

## Current Limitations

1. **No Recurring Events**: Each event must be created individually
2. **Single User**: No multi-user or shared calendar support
3. **No Notifications**: No reminders or alerts for upcoming events
4. **Limited Views**: Only weekly view; no daily or monthly views
5. **No Event Categories**: Cannot tag or categorize events
6. **No Search**: Cannot search events by title or description
7. **No Import/Export**: Cannot import from other calendar systems
8. **DST Edge Cases**: Some edge cases with Daylight Saving Time transitions may not be perfectly handled
9. **No Validation for Past Dates**: System allows creating events in the past
10. **In-Memory Conflict Checking**: No optimistic locking for concurrent updates


### Technical Improvements

1. **Unit Tests**: Comprehensive test coverage for conflict detection and timezone handling
2. **API Documentation**: OpenAPI/Swagger documentation
3. **Error Handling**: More graceful error messages and recovery
4. **Performance**: Database indexing for faster queries on large datasets
5. **Deployment**: Docker containerization, production-ready configuration

## Testing Recommendations

To test the system thoroughly:

1. **Conflict Detection**:
   - Create overlapping events (should fail)
   - Create adjacent events (should succeed)
   - Update event to create conflict (should fail)

2. **Timezone Handling**:
   - Create event in one timezone, view in another
   - Test DST transition dates
   - Test events crossing midnight in different timezones

3. **Weekly Navigation**:
   - Navigate forward/backward multiple weeks
   - Ensure events persist correctly
   - Test events spanning multiple days

4. **Edge Cases**:
   - Event at exact same start/end time
   - Very long events (multiple days)
   - Events at timezone boundaries



