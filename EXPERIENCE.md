# Experience Working on Calendar Management System

## Overview

Building a calendar management system from scratch was an insightful experience that highlighted both the apparent simplicity and hidden complexity of time-based applications. While calendars seem straightforward on the surface, working through the implementation revealed numerous edge cases and design challenges.

## Key Challenges Encountered

### 1. Timezone Handling

**Challenge**: The most complex aspect was handling timezones correctly. Initially, I considered storing times in the user's local timezone, but this approach would cause issues when:
- Users switch timezones
- Events span DST transitions
- Multiple users in different timezones view the same event (future multi-user scenario)

**Solution**: I adopted the industry-standard approach of storing all timestamps in UTC and converting to the user's timezone only for display. This required careful parsing and formatting at every API boundary.

**Learning**: Timezone handling is non-trivial and requires understanding of:
- UTC vs local time
- ISO 8601 datetime formats
- Timezone-aware vs naive datetimes
- DST transition behavior

### 2. Conflict Detection Logic

**Challenge**: Detecting overlapping events seems simple, but edge cases abound:
- What if two events have the same start time?
- What if one event completely contains another?
- Should events that touch at boundaries (no gap) be considered conflicts?

**Solution**: I implemented interval overlap detection using standard mathematical logic: two intervals overlap if `start1 < end2 AND end1 > start2`. I chose to allow events that touch at exact boundaries (e.g., one ends at 2:00 PM, another starts at 2:00 PM) as this seems more user-friendly.

**Learning**: Edge case handling requires explicit decisions. Documenting these choices in code comments helps future maintainers.

### 3. Data Model Design

**Challenge**: Deciding what to store and how to structure the database. Key questions:
- Should we store original timezone or always convert to UTC?
- Do we need to store timezone for each event or use a global setting?
- How to handle events that span multiple days?

**Solution**: I stored:
- UTC timestamps (for consistency)
- Original timezone (for context and future features)
- Separate start/end times (handles multi-day events naturally)

**Learning**: Good data modeling balances current needs with future extensibility. Over-engineering can be as harmful as under-engineering.

### 4. User Interface Design

**Challenge**: Creating an intuitive calendar view that works across different screen sizes and shows enough information without clutter.

**Solution**: I chose a weekly grid layout as a balance between detail and overview. Events show title and time on hover. The form is separate from the calendar view to avoid layout complexity.

**Learning**: Simple, focused interfaces are often better than feature-rich but complex ones. The user can accomplish all tasks without confusion.

### 5. API Design

**Challenge**: Designing RESTful endpoints that are intuitive, consistent, and handle errors gracefully.

**Solution**: I followed REST conventions:
- GET for retrieval
- POST for creation
- PUT for updates
- DELETE for removal
- Consistent error response format
- HTTP status codes appropriately used (409 for conflicts, 400 for validation errors)

**Learning**: Consistent API design reduces cognitive load for API consumers. Clear error messages are crucial for debugging.

## Technical Decisions and Trade-offs

### Chosen: SQLite over PostgreSQL

**Reasoning**: For this assignment scope, SQLite is perfect - no setup, file-based, sufficient performance. PostgreSQL would add complexity without benefits at this scale.

**Trade-off**: Would need migration if scaling to thousands of concurrent users, but that's outside current scope.

### Chosen: Flask over Django/FastAPI

**Reasoning**: Flask is lightweight, simple, and sufficient for REST API needs. Django would be overkill; FastAPI would add async complexity unnecessarily.

**Trade-off**: Flask is synchronous, but for this use case, performance is more than adequate.

### Chosen: Vanilla JavaScript over React/Vue

**Reasoning**: No build step, easier to understand, faster development for simple UI. React would add unnecessary complexity for this scope.

**Trade-off**: Code can become harder to maintain as it grows, but the UI is simple enough that this isn't an issue.

### Chosen: UTC Storage

**Reasoning**: Industry best practice, avoids timezone bugs, enables future multi-timezone features.

**Trade-off**: Requires conversion at API boundaries, but this is a small complexity cost for correctness.

## What Went Well

1. **Incremental Development**: Building features one at a time (database → API → frontend) made debugging easier.

2. **Early Testing**: Manually testing each endpoint as I built it caught bugs before they compounded.

3. **Clear Separation**: Separating backend (API) from frontend made each easier to reason about.

4. **Documentation**: Writing README as I built helped clarify my own thinking and will help users.

## What Could Be Improved

1. **Testing**: I focused on manual testing, but automated unit tests would catch regressions faster.

2. **Error Messages**: Some error messages could be more user-friendly (e.g., showing conflict details in a more readable format).

3. **Validation**: Frontend validation could be more sophisticated (e.g., preventing end time before start time before submission).

4. **Code Organization**: As the codebase grows, splitting `app.py` into modules (models, routes, utils) would improve maintainability.

## Insights and Learnings

### Time is Complex

The most surprising insight was how complex time handling is. What seems simple (storing a date and time) requires careful consideration of:
- Timezones
- Daylight Saving Time
- Calendar systems
- Leap years/seconds
- Locale-specific formatting

This is why libraries like `pytz` exist and why datetime handling is a common source of bugs in production systems.

### Simplicity vs. Features

Throughout development, I had to resist adding features (recurring events, multiple calendars, etc.) to focus on core functionality. This taught me the value of a minimal viable implementation that works correctly over a feature-rich but buggy system.

### Conflict Resolution is a Design Choice

Preventing overlaps entirely is one approach, but real calendar systems offer alternatives:
- Suggesting alternative times
- Showing all conflicts and letting user decide
- Allowing "soft" conflicts with warnings

I chose prevention for simplicity, but this is a design decision that affects user experience significantly.

### API Design Matters

Spending time thinking about API endpoints, request/response formats, and error handling upfront paid off. Changes to the API would require frontend changes, so getting it right early was important.

## Reflection on the Problem

This assignment excellently demonstrated how "simple" problems have hidden complexity. A calendar seems like a basic CRUD application, but it touches on:
- Time mathematics
- Conflict detection algorithms
- Data modeling
- API design
- User experience
- Edge case handling

Working through this systematically helped me appreciate why tools like Google Calendar, despite seeming simple, are actually sophisticated systems.

## Conclusion

Building this calendar system was a valuable exercise in:
- Identifying and handling edge cases
- Making thoughtful design decisions
- Balancing simplicity with functionality
- Understanding time-related complexity

The final system is functional and correct, though there's always room for improvement. The experience reinforced that good software requires careful thought about edge cases, user experience, and system design, even for seemingly simple problems.

