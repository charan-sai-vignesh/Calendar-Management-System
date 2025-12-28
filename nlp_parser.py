"""
Natural Language Processing for Calendar Event Creation
Converts natural language text into structured event data
"""

from datetime import datetime, timedelta
import re
import pytz

def parse_natural_language(text, timezone_str='UTC'):
    """
    Parse natural language input to extract event details
    
    Examples:
    - "Meeting tomorrow at 2pm"
    - "Lunch with John next Friday at 12:30"
    - "Call client on Dec 30 at 3pm"
    - "Team standup every day at 9am"
    - "Dentist appointment next Monday at 10:30am"
    """
    text = text.strip().lower()
    
    # Initialize result
    result = {
        'title': '',
        'description': '',
        'start_date': None,
        'start_time': None,
        'end_date': None,
        'end_time': None,
        'duration_minutes': 60,  # Default 1 hour
        'confidence': 0
    }
    
    # Extract title (usually everything before date/time keywords)
    title_match = re.match(r'^(.+?)(?:\s+(?:tomorrow|today|next|on|at|from|until))', text)
    if title_match:
        result['title'] = title_match.group(1).strip().title()
    else:
        # If no date/time keywords, try to extract title before common patterns
        title_match = re.match(r'^(.+?)(?:\s+(?:at|from|until)\s+)', text)
        if title_match:
            result['title'] = title_match.group(1).strip().title()
        else:
            result['title'] = text.split(' at ')[0].strip().title()
    
    # Extract date references
    today = datetime.now(pytz.timezone(timezone_str))
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # Helper function to calculate days until next weekday
    def days_until_weekday(target_weekday):
        """Calculate days until next occurrence of target weekday (0=Mon, 6=Sun)"""
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7  # Target day already passed this week, move to next week
        return days_ahead
    
    # Date patterns
    if 'today' in text:
        result['start_date'] = today.date()
        result['confidence'] += 0.3
    elif 'tomorrow' in text:
        result['start_date'] = (today + timedelta(days=1)).date()
        result['confidence'] += 0.3
    elif 'next week' in text:
        days_until_next_week = 7 - current_weekday
        if days_until_next_week == 0:
            days_until_next_week = 7
        result['start_date'] = (today + timedelta(days=days_until_next_week)).date()
        result['confidence'] += 0.2
    elif 'next monday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(0))).date()
        result['confidence'] += 0.3
    elif 'next tuesday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(1))).date()
        result['confidence'] += 0.3
    elif 'next wednesday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(2))).date()
        result['confidence'] += 0.3
    elif 'next thursday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(3))).date()
        result['confidence'] += 0.3
    elif 'next friday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(4))).date()
        result['confidence'] += 0.3
    elif 'next saturday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(5))).date()
        result['confidence'] += 0.3
    elif 'next sunday' in text:
        result['start_date'] = (today + timedelta(days=days_until_weekday(6))).date()
        result['confidence'] += 0.3
    
    # Extract specific dates (MM/DD, Dec 30, December 30, 30 Dec, etc.)
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})',  # 12/30 or 12-30
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})',  # Dec 30
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # 30 Dec
    ]
    
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if '/' in match.group(0) or '-' in match.group(0):
                    month, day = int(match.group(1)), int(match.group(2))
                else:
                    if match.group(1).lower() in month_map:
                        month = month_map[match.group(1).lower()]
                        day = int(match.group(2))
                    else:
                        month = month_map[match.group(2).lower()]
                        day = int(match.group(1))
                
                year = today.year
                # If date has passed this year, assume next year
                try_date = datetime(year, month, day).date()
                if try_date < today.date():
                    year += 1
                
                result['start_date'] = datetime(year, month, day).date()
                result['confidence'] += 0.4
                break
            except (ValueError, KeyError):
                continue
    
    # Default to today if no date found
    if result['start_date'] is None:
        result['start_date'] = today.date()
        result['confidence'] += 0.1
    
    result['end_date'] = result['start_date']
    
    # Extract time patterns (order matters - AM/PM patterns first)
    time_patterns = [
        (r'(\d{1,2}):(\d{2})\s*(am|pm)', True),  # 2:30pm, 2:30 pm
        (r'(\d{1,2})\s*(am|pm)', True),  # 2pm, 2 pm, 10am (no minutes)
        (r'at\s+(\d{1,2}):(\d{2})', False),  # at 14:30 (24-hour format)
        (r'at\s+(\d{1,2})', False),  # at 2 (default to PM if ambiguous)
    ]
    
    time_found = False
    for pattern_tuple in time_patterns:
        pattern, has_ampm = pattern_tuple
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                groups = match.groups()
                hour = int(groups[0])
                
                # Check if minutes present
                if len(groups) > 1 and groups[1].isdigit():
                    minute = int(groups[1])
                elif has_ampm and len(groups) > 2:
                    # Pattern like "2:30pm" - minute is in group 2, am/pm in group 3
                    minute = int(groups[1]) if groups[1].isdigit() else 0
                else:
                    minute = 0
                
                # Handle AM/PM
                period = None
                if has_ampm:
                    # Find am/pm in groups
                    for g in groups:
                        if isinstance(g, str) and g.lower() in ['am', 'pm']:
                            period = g.lower()
                            break
                
                # Apply AM/PM conversion
                if period:
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                elif not has_ampm and hour < 12 and 'at' in text.lower():
                    # Default to PM for ambiguous times like "at 2" (only if "at" keyword present)
                    hour += 12
                    if hour == 24:
                        hour = 0
                
                # Validate time
                if 0 <= hour < 24 and 0 <= minute < 60:
                    result['start_time'] = f"{hour:02d}:{minute:02d}"
                    result['confidence'] += 0.3
                    time_found = True
                    break
            except (ValueError, IndexError, AttributeError) as e:
                continue
    
    # Default time if not found
    if not time_found:
        result['start_time'] = "14:00"  # Default 2:00 PM
        result['confidence'] += 0.1
    
    # Extract duration
    duration_patterns = [
        r'for\s+(\d+)\s*(min|minutes|hour|hours|hr|hrs)',
        r'(\d+)\s*(min|minutes|hour|hours|hr|hrs)',
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                duration_val = int(match.group(1))
                unit = match.group(2).lower()
                
                if 'min' in unit:
                    result['duration_minutes'] = duration_val
                elif 'hour' in unit or 'hr' in unit:
                    result['duration_minutes'] = duration_val * 60
                
                # Calculate end time
                if result['start_time']:
                    hour, minute = map(int, result['start_time'].split(':'))
                    start_dt = datetime.combine(result['start_date'], datetime.min.time().replace(hour=hour, minute=minute))
                    end_dt = start_dt + timedelta(minutes=result['duration_minutes'])
                    result['end_time'] = f"{end_dt.hour:02d}:{end_dt.minute:02d}"
                
                result['confidence'] += 0.2
                break
            except (ValueError, IndexError):
                continue
    
    # Calculate end time if not set
    if not result.get('end_time') and result['start_time']:
        hour, minute = map(int, result['start_time'].split(':'))
        start_dt = datetime.combine(result['start_date'], datetime.min.time().replace(hour=hour, minute=minute))
        end_dt = start_dt + timedelta(minutes=result['duration_minutes'])
        result['end_time'] = f"{end_dt.hour:02d}:{end_dt.minute:02d}"
    else:
        result['end_time'] = result['start_time']
    
    return result

def format_parsed_result(result):
    """Format parsed result for display"""
    return {
        'title': result['title'] or 'Untitled Event',
        'start_date': result['start_date'].strftime('%Y-%m-%d') if result['start_date'] else None,
        'start_time': result['start_time'],
        'end_date': result['end_date'].strftime('%Y-%m-%d') if result['end_date'] else None,
        'end_time': result['end_time'],
        'confidence': round(result['confidence'], 2)
    }

