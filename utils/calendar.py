"""
Google Calendar Integration Module
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    """
    A class to manage Google Calendar events for healthcare follow-ups.
    """
    
    def __init__(self):
        """
        Initialize the Google Calendar manager.
        """
        self.creds = None
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar by default
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        try:
            # First try Service Account authentication (for server-to-server)
            if os.path.exists('credentials.json'):
                try:
                    self.creds = service_account.Credentials.from_service_account_file(
                        'credentials.json', scopes=SCOPES)
                    logger.info("Using Service Account authentication")
                except Exception as service_account_error:
                    logger.warning(f"Service Account auth failed: {service_account_error}")
                    # Fall back to OAuth 2.0 if service account fails
                    self.creds = None
            
            # If Service Account failed or doesn't exist, try OAuth 2.0
            if not self.creds:
                # The file token.json stores the user's access and refresh tokens,
                # and is created automatically when the authorization flow completes for the first time.
                if os.path.exists('token.json'):
                    self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                
                # If there are no (valid) credentials available, let the user log in.
                if not self.creds or not self.creds.valid:
                    if self.creds and self.creds.expired and self.creds.refresh_token:
                        self.creds.refresh(Request())
                    else:
                        if not os.path.exists('credentials.json'):
                            raise FileNotFoundError("credentials.json not found. Please download it from Google Cloud Console.")
                        
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        self.creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for the next run
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("Google Calendar authentication successful")
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {e}")
            raise
    
    def create_followup_event(self,
                            patient_name: str,
                            discharge_date: datetime,
                            appointment_type: str = "Follow-up",
                            duration_minutes: int = 30,
                            location: str = "",
                            description: str = "",
                            reminder_minutes: int = 60) -> Optional[str]:
        """
        Create a follow-up event 7 days after discharge.
        
        Args:
            patient_name (str): Patient's name
            discharge_date (datetime): Date of discharge
            appointment_type (str): Type of follow-up appointment
            duration_minutes (int): Duration of appointment in minutes
            location (str): Location of appointment
            description (str): Additional description
            reminder_minutes (int): Minutes before event to send reminder
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            # Calculate follow-up date (7 days after discharge)
            followup_date = discharge_date + timedelta(days=7)
            
            # Set default time to 2:00 PM if not specified
            followup_datetime = followup_date.replace(hour=14, minute=0, second=0, microsecond=0)
            
            # Create event
            event_id = self._create_calendar_event(
                summary=f"{appointment_type} - {patient_name}",
                start_datetime=followup_datetime,
                end_datetime=followup_datetime + timedelta(minutes=duration_minutes),
                location=location,
                description=description,
                reminder_minutes=reminder_minutes
            )
            
            if event_id:
                logger.info(f"Created follow-up event for {patient_name} on {followup_datetime.strftime('%Y-%m-%d %H:%M')}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating follow-up event: {e}")
            return None
    
    def create_custom_followup_event(self,
                                   patient_name: str,
                                   appointment_date: datetime,
                                   appointment_type: str = "Follow-up",
                                   duration_minutes: int = 30,
                                   location: str = "",
                                   description: str = "",
                                   reminder_minutes: int = 60) -> Optional[str]:
        """
        Create a custom follow-up event on a specific date.
        
        Args:
            patient_name (str): Patient's name
            appointment_date (datetime): Date and time of appointment
            appointment_type (str): Type of appointment
            duration_minutes (int): Duration of appointment in minutes
            location (str): Location of appointment
            description (str): Additional description
            reminder_minutes (int): Minutes before event to send reminder
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            event_id = self._create_calendar_event(
                summary=f"{appointment_type} - {patient_name}",
                start_datetime=appointment_date,
                end_datetime=appointment_date + timedelta(minutes=duration_minutes),
                location=location,
                description=description,
                reminder_minutes=reminder_minutes
            )
            
            if event_id:
                logger.info(f"Created custom follow-up event for {patient_name} on {appointment_date.strftime('%Y-%m-%d %H:%M')}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating custom follow-up event: {e}")
            return None
    
    def create_medication_review_event(self,
                                     patient_name: str,
                                     review_date: datetime,
                                     medication_list: List[str] = None,
                                     location: str = "",
                                     reminder_minutes: int = 60) -> Optional[str]:
        """
        Create a medication review event.
        
        Args:
            patient_name (str): Patient's name
            review_date (datetime): Date and time of medication review
            medication_list (List[str]): List of medications to review
            location (str): Location of review
            reminder_minutes (int): Minutes before event to send reminder
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            description = "Medication Review Appointment"
            if medication_list:
                description += f"\n\nMedications to review:\n" + "\n".join([f"• {med}" for med in medication_list])
            
            event_id = self._create_calendar_event(
                summary=f"Medication Review - {patient_name}",
                start_datetime=review_date,
                end_datetime=review_date + timedelta(minutes=45),
                location=location,
                description=description,
                reminder_minutes=reminder_minutes
            )
            
            if event_id:
                logger.info(f"Created medication review event for {patient_name}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating medication review event: {e}")
            return None
    
    def create_discharge_summary_event(self,
                                     patient_name: str,
                                     discharge_date: datetime,
                                     summary_notes: str = "",
                                     location: str = "",
                                     reminder_minutes: int = 30) -> Optional[str]:
        """
        Create a discharge summary event.
        
        Args:
            patient_name (str): Patient's name
            discharge_date (datetime): Date of discharge
            summary_notes (str): Discharge summary notes
            location (str): Location
            reminder_minutes (int): Minutes before event to send reminder
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            description = f"Discharge Summary for {patient_name}"
            if summary_notes:
                description += f"\n\nSummary:\n{summary_notes}"
            
            event_id = self._create_calendar_event(
                summary=f"Discharge Summary - {patient_name}",
                start_datetime=discharge_date,
                end_datetime=discharge_date + timedelta(minutes=15),
                location=location,
                description=description,
                reminder_minutes=reminder_minutes
            )
            
            if event_id:
                logger.info(f"Created discharge summary event for {patient_name}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating discharge summary event: {e}")
            return None
    
    def _create_calendar_event(self,
                             summary: str,
                             start_datetime: datetime,
                             end_datetime: datetime,
                             location: str = "",
                             description: str = "",
                             reminder_minutes: int = 60) -> Optional[str]:
        """
        Create a calendar event.
        
        Args:
            summary (str): Event summary/title
            start_datetime (datetime): Start date and time
            end_datetime (datetime): End date and time
            location (str): Event location
            description (str): Event description
            reminder_minutes (int): Minutes before event to send reminder
            
        Returns:
            str: Event ID if created successfully, None otherwise
        """
        try:
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Adjust timezone as needed
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Adjust timezone as needed
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': reminder_minutes},
                        {'method': 'popup', 'minutes': reminder_minutes},
                    ],
                },
            }
            
            event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            return event.get('id')
            
        except HttpError as error:
            logger.error(f"Error creating calendar event: {error}")
            return None
    
    def get_upcoming_events(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get upcoming calendar events.
        
        Args:
            max_results (int): Maximum number of events to return
            
        Returns:
            List[Dict]: List of upcoming events
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                logger.info('No upcoming events found.')
                return []
            
            return events
            
        except HttpError as error:
            logger.error(f"Error getting upcoming events: {error}")
            return []
    
    def get_events_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Get events for a specific date.
        
        Args:
            date (datetime): Date to get events for
            
        Returns:
            List[Dict]: List of events for the specified date
        """
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as error:
            logger.error(f"Error getting events for date: {error}")
            return []
    
    def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing calendar event.
        
        Args:
            event_id (str): ID of the event to update
            updates (Dict): Dictionary of fields to update
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get the existing event
            event = self.service.events().get(
                calendarId=self.calendar_id, 
                eventId=event_id
            ).execute()
            
            # Update the event with new data
            for key, value in updates.items():
                if key in event:
                    event[key] = value
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Updated event: {updated_event.get('summary')}")
            return True
            
        except HttpError as error:
            logger.error(f"Error updating event: {error}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id, 
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted event: {event_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Error deleting event: {error}")
            return False
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List available calendars.
        
        Returns:
            List[Dict]: List of available calendars
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            logger.info(f"Found {len(calendars)} calendars")
            return calendars
            
        except HttpError as error:
            logger.error(f"Error listing calendars: {error}")
            return []
    
    def set_calendar(self, calendar_id: str):
        """
        Set the calendar to use for events.
        
        Args:
            calendar_id (str): Calendar ID to use
        """
        self.calendar_id = calendar_id
        logger.info(f"Set calendar to: {calendar_id}")


# Convenience functions
def create_followup_event(patient_name: str, discharge_date: datetime, 
                         appointment_type: str = "Follow-up") -> Optional[str]:
    """
    Convenience function to create a follow-up event 7 days after discharge.
    
    Args:
        patient_name (str): Patient's name
        discharge_date (datetime): Date of discharge
        appointment_type (str): Type of follow-up appointment
        
    Returns:
        str: Event ID if created successfully, None otherwise
    """
    calendar_manager = GoogleCalendarManager()
    return calendar_manager.create_followup_event(patient_name, discharge_date, appointment_type)


def create_custom_appointment(patient_name: str, appointment_date: datetime,
                            appointment_type: str = "Follow-up") -> Optional[str]:
    """
    Convenience function to create a custom appointment.
    
    Args:
        patient_name (str): Patient's name
        appointment_date (datetime): Date and time of appointment
        appointment_type (str): Type of appointment
        
    Returns:
        str: Event ID if created successfully, None otherwise
    """
    calendar_manager = GoogleCalendarManager()
    return calendar_manager.create_custom_followup_event(
        patient_name, appointment_date, appointment_type
    )


if __name__ == "__main__":
    # Example usage
    calendar_manager = GoogleCalendarManager()
    
    # Create a follow-up event 7 days after discharge
    discharge_date = datetime.now()
    event_id = calendar_manager.create_followup_event(
        patient_name="John Doe",
        discharge_date=discharge_date,
        appointment_type="Cardiology Follow-up",
        location="Cardiology Clinic, Room 302",
        description="Follow-up appointment after discharge. Please bring medication list."
    )
    
    if event_id:
        print(f"Created follow-up event with ID: {event_id}")
    
    # Create a medication review event
    review_date = datetime.now() + timedelta(days=14)
    med_event_id = calendar_manager.create_medication_review_event(
        patient_name="John Doe",
        review_date=review_date,
        medication_list=["Lisinopril 10mg", "Metoprolol 25mg"],
        location="Pharmacy Department"
    )
    
    if med_event_id:
        print(f"Created medication review event with ID: {med_event_id}")
    
    # Get upcoming events
    upcoming_events = calendar_manager.get_upcoming_events(max_results=5)
    print(f"Found {len(upcoming_events)} upcoming events")
    
    for event in upcoming_events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start} - {event['summary']}") 