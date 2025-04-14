import base64

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import os


class GoogleCalendarManager:
    def __init__(self, calendar_id='primary', credentials_json_b64:str=None):
        """
        Initialize the Google Calendar Manager using credentials from environment variable.

        Args:
            calendar_id (str): ID of the calendar to manage (default is 'primary')
        """
        self.calendar_id = calendar_id

        try:
            credentials_json = base64.b64decode(credentials_json_b64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=self.credentials)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GOOGLE_CREDENTIALS: {e}")
        except Exception as e:
            raise Exception(f"Error creating credentials: {e}")

    def create_event(self, summary, start_time, end_time, description=None, location=None, attendees=None,
                     timezone='America/Sao_Paulo'):
        """Create a calendar event."""
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': timezone,
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
            print(event)
            print(f'Event created: {event.get("htmlLink")}')
            return event
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def delete_event(self, event_id):
        """Delete a calendar event."""
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
