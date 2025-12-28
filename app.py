"""
Calendar Management System - Backend API
Main Flask application for handling calendar events
"""

from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta
import pytz
import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from nlp_parser import parse_natural_language, format_parsed_result

app = Flask(__name__, static_folder='static', static_url_path='')

# Database file
DATABASE = 'calendar.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with events table"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_time_utc TEXT NOT NULL,
            end_time_utc TEXT NOT NULL,
            timezone TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def parse_datetime_with_timezone(dt_str: str, tz_str: str) -> datetime:
    """Parse datetime string with timezone"""
    try:
        tz = pytz.timezone(tz_str)
        
        # Normalize the datetime string
        dt_str_normalized = dt_str.replace('Z', '+00:00')
        
        # Try to parse the datetime
        try:
            dt = datetime.fromisoformat(dt_str_normalized)
        except ValueError:
            # If that fails, try the original string
            dt = datetime.fromisoformat(dt_str)
        
        # If datetime is naive (no timezone), localize it to the specified timezone
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        
        # Convert to UTC
        return dt.astimezone(pytz.UTC)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format '{dt_str}': {e}")
    except pytz.UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone '{tz_str}': {e}")
    except Exception as e:
        raise ValueError(f"Error parsing datetime: {e}")

def format_datetime_utc(dt_utc: datetime) -> str:
    """Format UTC datetime as ISO string"""
    return dt_utc.isoformat().replace('+00:00', 'Z')

def check_conflicts(start_utc: datetime, end_utc: datetime, exclude_id: Optional[int] = None) -> List[Dict]:
    """Check for overlapping events"""
    if start_utc >= end_utc:
        return [{"error": "Start time must be before end time"}]
    
    conn = get_db()
    query = '''
        SELECT id, title, start_time_utc, end_time_utc, timezone
        FROM events
        WHERE (
            (start_time_utc < ? AND end_time_utc > ?) OR
            (start_time_utc < ? AND end_time_utc > ?) OR
            (start_time_utc >= ? AND end_time_utc <= ?)
        )
    '''
    params = [format_datetime_utc(end_utc), format_datetime_utc(start_utc),
              format_datetime_utc(start_utc), format_datetime_utc(end_utc),
              format_datetime_utc(start_utc), format_datetime_utc(end_utc)]
    
    if exclude_id:
        query += ' AND id != ?'
        params.append(exclude_id)
    
    cursor = conn.execute(query, params)
    conflicts = []
    for row in cursor.fetchall():
        conflicts.append({
            'id': row['id'],
            'title': row['title'],
            'start_time_utc': row['start_time_utc'],
            'end_time_utc': row['end_time_utc'],
            'timezone': row['timezone']
        })
    conn.close()
    return conflicts

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get events within a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    timezone = request.args.get('timezone', 'UTC')
    
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return jsonify({'error': f'Invalid timezone: {timezone}'}), 400
    
    conn = get_db()
    query = 'SELECT * FROM events WHERE 1=1'
    params = []
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        start_utc = start_dt.astimezone(pytz.UTC)
        query += ' AND end_time_utc >= ?'
        params.append(format_datetime_utc(start_utc))
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        if end_dt.tzinfo is None:
            end_dt = tz.localize(end_dt)
        end_utc = end_dt.astimezone(pytz.UTC)
        query += ' AND start_time_utc <= ?'
        params.append(format_datetime_utc(end_utc))
    
    query += ' ORDER BY start_time_utc ASC'
    cursor = conn.execute(query, params)
    
    events = []
    for row in cursor.fetchall():
        start_utc = datetime.fromisoformat(row['start_time_utc'].replace('Z', '+00:00'))
        end_utc = datetime.fromisoformat(row['end_time_utc'].replace('Z', '+00:00'))
        
        events.append({
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'start_time': start_utc.astimezone(tz).isoformat(),
            'end_time': end_utc.astimezone(tz).isoformat(),
            'timezone': row['timezone'],
            'start_time_utc': row['start_time_utc'],
            'end_time_utc': row['end_time_utc']
        })
    
    conn.close()
    return jsonify(events)

@app.route('/api/events/week', methods=['GET'])
def get_weekly_events():
    """Get events for a specific week"""
    start_date_str = request.args.get('start_date')
    timezone = request.args.get('timezone', 'UTC')
    
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        return jsonify({'error': f'Invalid timezone: {timezone}'}), 400
    
    if not start_date_str:
        # Default to current week in the specified timezone
        now = datetime.now(tz)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Parse the date string as a date in the specified timezone
        # start_date_str is in format YYYY-MM-DD
        try:
            date_parts = start_date_str.split('-')
            year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
            start_of_week = tz.localize(datetime(year, month, day, 0, 0, 0))
        except (ValueError, IndexError):
            # Fallback to isoformat parsing
            start_of_week = datetime.fromisoformat(start_date_str)
            if start_of_week.tzinfo is None:
                start_of_week = tz.localize(start_of_week)
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_of_week = start_of_week + timedelta(days=7)
    
    start_utc = start_of_week.astimezone(pytz.UTC)
    end_utc = end_of_week.astimezone(pytz.UTC)
    
    conn = get_db()
    cursor = conn.execute('''
        SELECT * FROM events
        WHERE end_time_utc >= ? AND start_time_utc < ?
        ORDER BY start_time_utc ASC
    ''', [format_datetime_utc(start_utc), format_datetime_utc(end_utc)])
    
    events = []
    for row in cursor.fetchall():
        start_event_utc = datetime.fromisoformat(row['start_time_utc'].replace('Z', '+00:00'))
        end_event_utc = datetime.fromisoformat(row['end_time_utc'].replace('Z', '+00:00'))
        
        events.append({
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'start_time': start_event_utc.astimezone(tz).isoformat(),
            'end_time': end_event_utc.astimezone(tz).isoformat(),
            'timezone': row['timezone'],
            'start_time_utc': row['start_time_utc'],
            'end_time_utc': row['end_time_utc']
        })
    
    conn.close()
    
    return jsonify({
        'start_of_week': start_of_week.isoformat(),
        'end_of_week': end_of_week.isoformat(),
        'events': events
    })

@app.route('/api/events', methods=['POST'])
def create_event():
    """Create a new event"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title')
    description = data.get('description', '')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    timezone = data.get('timezone', 'UTC')
    
    if not all([title, start_time, end_time]):
        return jsonify({'error': 'Missing required fields: title, start_time, end_time'}), 400
    
    try:
        tz = pytz.timezone(timezone)
        start_utc = parse_datetime_with_timezone(start_time, timezone)
        end_utc = parse_datetime_with_timezone(end_time, timezone)
    except (ValueError, pytz.UnknownTimeZoneError) as e:
        return jsonify({'error': str(e)}), 400
    
    # Check for conflicts
    conflicts = check_conflicts(start_utc, end_utc)
    if conflicts:
        if 'error' in conflicts[0]:
            return jsonify(conflicts[0]), 400
        else:
            # Real conflicts found
            return jsonify({
                'error': 'Event conflicts with existing events',
                'conflicts': conflicts
            }), 409
    
    # Create event
    conn = get_db()
    created_at = datetime.now(pytz.UTC)
    conn.execute('''
        INSERT INTO events (title, description, start_time_utc, end_time_utc, timezone, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [title, description, format_datetime_utc(start_utc), format_datetime_utc(end_utc), timezone, format_datetime_utc(created_at)])
    conn.commit()
    event_id = conn.lastrowid
    conn.close()
    
    return jsonify({
        'id': event_id,
        'title': title,
        'description': description,
        'start_time': start_utc.astimezone(tz).isoformat(),
        'end_time': end_utc.astimezone(tz).isoformat(),
        'timezone': timezone,
        'message': 'Event created successfully'
    }), 201

@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an existing event"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    conn = get_db()
    # Check if event exists
    cursor = conn.execute('SELECT * FROM events WHERE id = ?', [event_id])
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Event not found'}), 404
    
    title = data.get('title', existing['title'])
    description = data.get('description', existing['description'])
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    timezone = data.get('timezone', existing['timezone'])
    
    try:
        tz = pytz.timezone(timezone)
        if start_time:
            start_utc = parse_datetime_with_timezone(start_time, timezone)
        else:
            start_utc = datetime.fromisoformat(existing['start_time_utc'].replace('Z', '+00:00'))
        
        if end_time:
            end_utc = parse_datetime_with_timezone(end_time, timezone)
        else:
            end_utc = datetime.fromisoformat(existing['end_time_utc'].replace('Z', '+00:00'))
    except (ValueError, pytz.UnknownTimeZoneError) as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    
    # Check for conflicts (excluding current event)
    conflicts = check_conflicts(start_utc, end_utc, exclude_id=event_id)
    if conflicts:
        if 'error' in conflicts[0]:
            conn.close()
            return jsonify(conflicts[0]), 400
        else:
            # Real conflicts found
            conn.close()
            return jsonify({
                'error': 'Event conflicts with existing events',
                'conflicts': conflicts
            }), 409
    
    # Update event
    conn.execute('''
        UPDATE events
        SET title = ?, description = ?, start_time_utc = ?, end_time_utc = ?, timezone = ?
        WHERE id = ?
    ''', [title, description, format_datetime_utc(start_utc), format_datetime_utc(end_utc), timezone, event_id])
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': event_id,
        'title': title,
        'description': description,
        'start_time': start_utc.astimezone(tz).isoformat(),
        'end_time': end_utc.astimezone(tz).isoformat(),
        'timezone': timezone,
        'message': 'Event updated successfully'
    })

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    conn = get_db()
    cursor = conn.execute('SELECT id FROM events WHERE id = ?', [event_id])
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Event not found'}), 404
    
    conn.execute('DELETE FROM events WHERE id = ?', [event_id])
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Event deleted successfully'})

@app.route('/api/nlp/parse', methods=['POST'])
def parse_natural_language_endpoint():
    """Parse natural language input into event structure"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data.get('text')
    timezone = data.get('timezone', 'UTC')
    
    try:
        parsed = parse_natural_language(text, timezone)
        formatted = format_parsed_result(parsed)
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': f'Failed to parse: {str(e)}'}), 400

if __name__ == '__main__':
    init_db()
    print("Database initialized")
    print("Starting server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

