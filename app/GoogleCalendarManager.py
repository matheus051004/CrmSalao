from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build


class GoogleCalendarManager:
    def __init__(self, credentials_path, calendar_id='primary'):
        """
        Initialize the Google Calendar Manager.

        Args:
            credentials_path (str): Path to the service account credentials JSON file
            calendar_id (str): ID of the calendar to manage (default is 'primary')
        """
        self.calendar_id = calendar_id
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)

    def create_event(self, summary, start_time, end_time, description=None, location=None, attendees=None):
        """
        Create a new calendar event.

        Args:
            summary (str): Title of the event
            start_time (datetime): Start time of the event
            end_time (datetime): End time of the event
            description (str, optional): Description of the event
            location (str, optional): Location of the event
            attendees (list, optional): List of attendee email addresses

        Returns:
            dict: Created event details
        """
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            }
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        try:
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            print(f'Event created: {event.get("htmlLink")}')
            return event
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def delete_event(self, event_id):
        """
        Delete a calendar event.

        Args:
            event_id (str): ID of the event to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            print(f'Event {event_id} deleted successfully')
            return True
        except Exception as e:
            print(f'An error occurred: {e}')
            return False

    def list_events(self, max_results=10):
        """
        List upcoming calendar events.

        Args:
            max_results (int): Maximum number of events to retrieve

        Returns:
            list: List of upcoming events
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f'An error occurred: {e}')
            return []
