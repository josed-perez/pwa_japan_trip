# App update: deduplicate calendar items and sort by time

This change fixes the duplicate itinerary entries caused by overlapping Google Calendar and itinerary data.

## What changed
- Deduplicates events by similarity in title/date before rendering a day
- Merges Google Calendar details into the matching itinerary item instead of leaving a second copy
- Sorts each day's schedule by time so the day reads from earliest to latest as intended

## Notes
- This update is limited to the client-side itinerary rendering in `app.js`
- The logic keeps the synced calendar event metadata attached to the surviving item so the schedule still shows the calendar context
