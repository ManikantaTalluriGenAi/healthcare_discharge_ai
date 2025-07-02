"""
Healthcare Scheduler Module for Medication and Follow-up Reminders
"""

import os
import schedule
import threading
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from dotenv import load_dotenv
import json
import uuid

# Import our Telegram sender
from utils.telegram_sender import TelegramSender

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MedicationSchedule:
    """Data class for medication schedule information."""
    id: str
    medication_name: str
    dosage: str
    times: List[str]  # List of times in "HH:MM" format
    duration_days: int
    start_date: datetime
    end_date: datetime
    additional_notes: str
    is_active: bool = True
    created_at: datetime = None
    chat_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.end_date is None:
            self.end_date = self.start_date + timedelta(days=self.duration_days)

@dataclass
class FollowUpSchedule:
    """Data class for follow-up appointment schedule information."""
    id: str
    appointment_type: str
    appointment_date: datetime
    appointment_time: str
    location: str
    notes: str
    reminder_days_before: List[int]  # Days before appointment to send reminders
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class HealthcareScheduler:
    """
    A class to manage healthcare schedules including medications and follow-ups.
    """
    
    def __init__(self):
        """
        Initialize the healthcare scheduler.
        """
        self.telegram_sender = TelegramSender()
        self.medication_schedules: Dict[str, MedicationSchedule] = {}
        self.followup_schedules: Dict[str, FollowUpSchedule] = {}
        self.scheduler_thread = None
        self.is_running = False
        self._load_schedules()
    
    def _load_schedules(self):
        """Load existing schedules from file if available."""
        try:
            if os.path.exists('schedules.json'):
                with open('schedules.json', 'r') as f:
                    data = json.load(f)
                    
                # Load medication schedules
                for med_data in data.get('medications', []):
                    schedule = MedicationSchedule(
                        id=med_data['id'],
                        medication_name=med_data['medication_name'],
                        dosage=med_data['dosage'],
                        times=med_data['times'],
                        duration_days=med_data['duration_days'],
                        start_date=datetime.fromisoformat(med_data['start_date']),
                        end_date=datetime.fromisoformat(med_data['end_date']),
                        additional_notes=med_data['additional_notes'],
                        is_active=med_data['is_active'],
                        created_at=datetime.fromisoformat(med_data['created_at'])
                    )
                    self.medication_schedules[schedule.id] = schedule
                
                # Load follow-up schedules
                for followup_data in data.get('followups', []):
                    schedule = FollowUpSchedule(
                        id=followup_data['id'],
                        appointment_type=followup_data['appointment_type'],
                        appointment_date=datetime.fromisoformat(followup_data['appointment_date']),
                        appointment_time=followup_data['appointment_time'],
                        location=followup_data['location'],
                        notes=followup_data['notes'],
                        reminder_days_before=followup_data['reminder_days_before'],
                        is_active=followup_data['is_active'],
                        created_at=datetime.fromisoformat(followup_data['created_at'])
                    )
                    self.followup_schedules[schedule.id] = schedule
                    
                logger.info(f"Loaded {len(self.medication_schedules)} medication schedules and {len(self.followup_schedules)} follow-up schedules")
                
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
    
    def _save_schedules(self):
        """Save current schedules to file."""
        try:
            data = {
                'medications': [],
                'followups': []
            }
            
            # Save medication schedules
            for schedule in self.medication_schedules.values():
                data['medications'].append({
                    'id': schedule.id,
                    'medication_name': schedule.medication_name,
                    'dosage': schedule.dosage,
                    'times': schedule.times,
                    'duration_days': schedule.duration_days,
                    'start_date': schedule.start_date.isoformat(),
                    'end_date': schedule.end_date.isoformat(),
                    'additional_notes': schedule.additional_notes,
                    'is_active': schedule.is_active,
                    'created_at': schedule.created_at.isoformat()
                })
            
            # Save follow-up schedules
            for schedule in self.followup_schedules.values():
                data['followups'].append({
                    'id': schedule.id,
                    'appointment_type': schedule.appointment_type,
                    'appointment_date': schedule.appointment_date.isoformat(),
                    'appointment_time': schedule.appointment_time,
                    'location': schedule.location,
                    'notes': schedule.notes,
                    'reminder_days_before': schedule.reminder_days_before,
                    'is_active': schedule.is_active,
                    'created_at': schedule.created_at.isoformat()
                })
            
            with open('schedules.json', 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")
    
    def add_medication_schedule(self,
                               medication_name: str,
                               dosage: str,
                               times: List[str],
                               duration_days: int,
                               start_date: Optional[datetime] = None,
                               additional_notes: str = "",
                               chat_id: Optional[str] = None) -> str:
        """
        Add a new medication schedule.
        
        Args:
            medication_name (str): Name of the medication
            dosage (str): Dosage information
            times (List[str]): List of times in "HH:MM" format
            duration_days (int): Duration in days
            start_date (datetime, optional): Start date (default: today)
            additional_notes (str): Additional instructions
            
        Returns:
            str: Schedule ID
        """
        try:
            if start_date is None:
                start_date = datetime.now()
            
            schedule_id = str(uuid.uuid4())
            
            schedule = MedicationSchedule(
                id=schedule_id,
                medication_name=medication_name,
                dosage=dosage,
                times=times,
                duration_days=duration_days,
                start_date=start_date,
                end_date=start_date + timedelta(days=duration_days),
                additional_notes=additional_notes
            )
            
            # Store chat_id for this schedule
            if chat_id:
                schedule.chat_id = chat_id
            
            self.medication_schedules[schedule_id] = schedule
            
            # Schedule the reminders
            self._schedule_medication_reminders(schedule)
            
            # Save schedules
            self._save_schedules()
            
            logger.info(f"Added medication schedule: {medication_name} for {duration_days} days")
            
            return schedule_id
            
        except Exception as e:
            logger.error(f"Error adding medication schedule: {e}")
            raise
    
    def add_followup_schedule(self,
                             appointment_type: str,
                             appointment_date: datetime,
                             appointment_time: str,
                             location: str = "",
                             notes: str = "",
                             reminder_days_before: List[int] = None) -> str:
        """
        Add a new follow-up appointment schedule.
        
        Args:
            appointment_type (str): Type of appointment
            appointment_date (datetime): Appointment date
            appointment_time (str): Appointment time
            location (str): Appointment location
            notes (str): Additional notes
            reminder_days_before (List[int]): Days before appointment to send reminders
            
        Returns:
            str: Schedule ID
        """
        try:
            if reminder_days_before is None:
                reminder_days_before = [1, 3, 7]  # Default reminders
            
            schedule_id = str(uuid.uuid4())
            
            schedule = FollowUpSchedule(
                id=schedule_id,
                appointment_type=appointment_type,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                location=location,
                notes=notes,
                reminder_days_before=reminder_days_before
            )
            
            self.followup_schedules[schedule_id] = schedule
            
            # Schedule the reminders
            self._schedule_followup_reminders(schedule)
            
            # Save schedules
            self._save_schedules()
            
            logger.info(f"Added follow-up schedule: {appointment_type} on {appointment_date}")
            
            return schedule_id
            
        except Exception as e:
            logger.error(f"Error adding follow-up schedule: {e}")
            raise
    
    def _schedule_medication_reminders(self, medication_schedule: MedicationSchedule):
        """Schedule medication reminders for a given schedule."""
        try:
            for time_str in medication_schedule.times:
                # Schedule daily reminder at the specified time
                schedule.every().day.at(time_str).do(
                    self._send_medication_reminder,
                    schedule_id=medication_schedule.id
                )
            
            logger.info(f"Scheduled medication reminders for {medication_schedule.medication_name}")
            
        except Exception as e:
            logger.error(f"Error scheduling medication reminders: {e}")
    
    def _schedule_followup_reminders(self, followup_schedule: FollowUpSchedule):
        """Schedule follow-up appointment reminders."""
        try:
            for days_before in followup_schedule.reminder_days_before:
                reminder_date = followup_schedule.appointment_date - timedelta(days=days_before)
                
                if reminder_date > datetime.now():
                    # Schedule reminder for specific date at 9 AM
                    schedule.every().day.at("09:00").do(
                        self._send_followup_reminder,
                        schedule_id=followup_schedule.id,
                        days_before=days_before
                    ).tag(f"followup_{followup_schedule.id}_{days_before}")
            
            logger.info(f"Scheduled follow-up reminders for {followup_schedule.appointment_type}")
            
        except Exception as e:
            logger.error(f"Error scheduling follow-up reminders: {e}")
    
    def _send_medication_reminder(self, schedule_id: str):
        """Send medication reminder for a specific schedule."""
        try:
            schedule = self.medication_schedules.get(schedule_id)
            if not schedule or not schedule.is_active:
                return
            
            # Check if schedule is still active
            if datetime.now() > schedule.end_date:
                schedule.is_active = False
                self._save_schedules()
                logger.info(f"Medication schedule {schedule_id} has ended")
                return
            
            # Send reminder
            success = self.telegram_sender.send_medication_reminder(
                chat_id=schedule.chat_id,
                medication_name=schedule.medication_name,
                dosage=schedule.dosage,
                time_to_take=datetime.now().strftime("%I:%M %p"),
                additional_notes=schedule.additional_notes
            )
            
            if success:
                logger.info(f"Sent medication reminder for {schedule.medication_name}")
            else:
                logger.error(f"Failed to send medication reminder for {schedule.medication_name}")
                
        except Exception as e:
            logger.error(f"Error sending medication reminder: {e}")
    
    def _send_followup_reminder(self, schedule_id: str, days_before: int):
        """Send follow-up appointment reminder."""
        try:
            schedule = self.followup_schedules.get(schedule_id)
            if not schedule or not schedule.is_active:
                return
            
            # Check if it's the right day to send this reminder
            reminder_date = schedule.appointment_date - timedelta(days=days_before)
            if reminder_date.date() != datetime.now().date():
                return
            
            # Send reminder
            success = self.telegram_sender.send_follow_up_reminder(
                appointment_type=schedule.appointment_type,
                date=schedule.appointment_date.strftime("%Y-%m-%d"),
                time=schedule.appointment_time,
                location=schedule.location,
                notes=schedule.notes
            )
            
            if success:
                logger.info(f"Sent follow-up reminder for {schedule.appointment_type}")
            else:
                logger.error(f"Failed to send follow-up reminder for {schedule.appointment_type}")
                
        except Exception as e:
            logger.error(f"Error sending follow-up reminder: {e}")
    
    def stop_medication_schedule(self, schedule_id: str) -> bool:
        """
        Stop a medication schedule.
        
        Args:
            schedule_id (str): Schedule ID to stop
            
        Returns:
            bool: True if stopped successfully
        """
        try:
            if schedule_id in self.medication_schedules:
                self.medication_schedules[schedule_id].is_active = False
                self._save_schedules()
                logger.info(f"Stopped medication schedule: {schedule_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error stopping medication schedule: {e}")
            return False
    
    def stop_followup_schedule(self, schedule_id: str) -> bool:
        """
        Stop a follow-up schedule.
        
        Args:
            schedule_id (str): Schedule ID to stop
            
        Returns:
            bool: True if stopped successfully
        """
        try:
            if schedule_id in self.followup_schedules:
                self.followup_schedules[schedule_id].is_active = False
                self._save_schedules()
                logger.info(f"Stopped follow-up schedule: {schedule_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error stopping follow-up schedule: {e}")
            return False
    
    def get_active_schedules(self) -> Dict[str, Any]:
        """
        Get all active schedules.
        
        Returns:
            Dict containing active medication and follow-up schedules
        """
        active_medications = {
            k: v for k, v in self.medication_schedules.items() 
            if v.is_active and datetime.now() <= v.end_date
        }
        
        active_followups = {
            k: v for k, v in self.followup_schedules.items() 
            if v.is_active and v.appointment_date > datetime.now()
        }
        
        return {
            'medications': active_medications,
            'followups': active_followups
        }
    
    def start_scheduler(self):
        """Start the scheduler in a separate thread."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("Healthcare scheduler started")
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Healthcare scheduler stopped")
    
    def send_summary(self):
        """Send a summary of all active schedules."""
        try:
            active_schedules = self.get_active_schedules()
            
            summary = "📋 <b>Healthcare Schedule Summary</b>\n\n"
            
            # Medication summary
            if active_schedules['medications']:
                summary += "💊 <b>Active Medications:</b>\n"
                for schedule in active_schedules['medications'].values():
                    days_left = (schedule.end_date - datetime.now()).days
                    summary += f"• {schedule.medication_name} ({schedule.dosage}) - {days_left} days left\n"
                summary += "\n"
            
            # Follow-up summary
            if active_schedules['followups']:
                summary += "📅 <b>Upcoming Appointments:</b>\n"
                for schedule in active_schedules['followups'].values():
                    days_until = (schedule.appointment_date - datetime.now()).days
                    summary += f"• {schedule.appointment_type} - {days_until} days until appointment\n"
            
            if not active_schedules['medications'] and not active_schedules['followups']:
                summary += "No active schedules at the moment."
            
            self.telegram_sender.send_message(summary)
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")


# Convenience functions
def create_medication_schedule(medication_name: str, dosage: str, times: List[str], 
                              duration_days: int, additional_notes: str = "") -> str:
    """
    Convenience function to create a medication schedule.
    
    Args:
        medication_name (str): Name of the medication
        dosage (str): Dosage information
        times (List[str]): List of times in "HH:MM" format
        duration_days (int): Duration in days
        additional_notes (str): Additional instructions
        
    Returns:
        str: Schedule ID
    """
    scheduler = HealthcareScheduler()
    return scheduler.add_medication_schedule(
        medication_name, dosage, times, duration_days, 
        additional_notes=additional_notes
    )


def create_followup_schedule(appointment_type: str, appointment_date: datetime,
                           appointment_time: str, location: str = "", notes: str = "") -> str:
    """
    Convenience function to create a follow-up schedule.
    
    Args:
        appointment_type (str): Type of appointment
        appointment_date (datetime): Appointment date
        appointment_time (str): Appointment time
        location (str): Appointment location
        notes (str): Additional notes
        
    Returns:
        str: Schedule ID
    """
    scheduler = HealthcareScheduler()
    return scheduler.add_followup_schedule(
        appointment_type, appointment_date, appointment_time, location, notes
    )


if __name__ == "__main__":
    # Example usage
    scheduler = HealthcareScheduler()
    
    # Start the scheduler
    scheduler.start_scheduler()
    
    # Add a medication schedule
    med_id = scheduler.add_medication_schedule(
        medication_name="Lisinopril",
        dosage="10mg",
        times=["08:00", "20:00"],
        duration_days=30,
        additional_notes="Take with food, avoid if blood pressure is too low"
    )
    
    # Add a follow-up schedule
    followup_date = datetime.now() + timedelta(days=7)
    followup_id = scheduler.add_followup_schedule(
        appointment_type="Cardiology Follow-up",
        appointment_date=followup_date,
        appointment_time="2:30 PM",
        location="Cardiology Clinic, Room 302",
        notes="Please bring your medication list"
    )
    
    # Send summary
    scheduler.send_summary()
    
    # Keep the scheduler running
    try:
        while True:
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        scheduler.stop_scheduler()
        print("Scheduler stopped") 