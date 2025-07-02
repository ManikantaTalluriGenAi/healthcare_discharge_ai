"""
Telegram Message Sender Module
"""

import os
import requests
import json
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import schedule
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramSender:
    """
    A class to send messages via Telegram Bot API.
    """
    
    def __init__(self):
        """
        Initialize the Telegram sender with credentials from environment variables.
        """
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Validate Telegram credentials."""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID not found in environment variables")
        
        # Test the bot token
        try:
            response = requests.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Telegram bot initialized: @{bot_info['result']['username']}")
            else:
                raise ValueError(f"Invalid bot token: {response.status_code}")
        except Exception as e:
            logger.error(f"Error validating Telegram credentials: {e}")
            raise
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a text message via Telegram.
        
        Args:
            message (str): Message text to send
            parse_mode (str): Parse mode ('HTML', 'Markdown', or 'MarkdownV2')
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            if not message or not message.strip():
                logger.warning("Empty message, not sending")
                return False
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_medication_reminder(self, 
                               chat_id: str,
                               medication_name: str,
                               dosage: str,
                               time_to_take: str,
                               additional_notes: str = "") -> bool:
        """
        Send a medication reminder message.
        
        Args:
            chat_id (str): Telegram chat ID to send to
            medication_name (str): Name of the medication
            dosage (str): Dosage information
            time_to_take (str): When to take the medication
            additional_notes (str): Additional instructions
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            message = f"""
💊 <b>Medication Reminder</b>\n\n<b>Medication:</b> {medication_name}\n<b>Dosage:</b> {dosage}\n<b>Time:</b> {time_to_take}\n\n{additional_notes if additional_notes else ""}\n\nPlease take your medication as prescribed.""".strip()
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                logger.info(f"Medication reminder sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to send medication reminder: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending medication reminder: {e}")
            return False
    
    def send_follow_up_reminder(self, 
                              appointment_type: str,
                              date: str,
                              time: str,
                              location: str = "",
                              notes: str = "") -> bool:
        """
        Send a follow-up appointment reminder.
        
        Args:
            appointment_type (str): Type of appointment
            date (str): Appointment date
            time (str): Appointment time
            location (str): Appointment location
            notes (str): Additional notes
            
        Returns:
            bool: True if message sent successfully
        """
        message = f"""
📅 <b>Follow-up Appointment Reminder</b>

<b>Type:</b> {appointment_type}
<b>Date:</b> {date}
<b>Time:</b> {time}

{f"<b>Location:</b> {location}" if location else ""}

{notes if notes else ""}

Please confirm your appointment or contact us if you need to reschedule.
        """.strip()
        
        return self.send_message(message)
    
    def send_discharge_summary(self, 
                             chat_id: str,
                             patient_name: str,
                             summary: str,
                             instructions: str = "") -> bool:
        """
        Send a discharge summary message.
        
        Args:
            chat_id (str): Telegram chat ID to send to
            patient_name (str): Patient's name
            summary (str): Discharge summary
            instructions (str): Discharge instructions
            
        Returns:
            bool: True if message sent successfully
        """
        try:
            message = f"""
🏥 <b>Discharge Summary</b>

<b>Patient:</b> {patient_name}

<b>Summary:</b>
{summary}

{f"<b>Instructions:</b>\n{instructions}" if instructions else ""}

Please review and follow the instructions carefully.
            """.strip()
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info(f"Discharge summary sent to chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to send discharge summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending discharge summary: {e}")
            return False
    
    def send_emergency_alert(self, 
                           alert_type: str,
                           message: str,
                           urgency: str = "normal") -> bool:
        """
        Send an emergency or urgent alert.
        
        Args:
            alert_type (str): Type of alert
            message (str): Alert message
            urgency (str): Urgency level ('low', 'normal', 'high', 'emergency')
            
        Returns:
            bool: True if message sent successfully
        """
        urgency_icons = {
            'low': '🔵',
            'normal': '🟡',
            'high': '🟠',
            'emergency': '🔴'
        }
        
        icon = urgency_icons.get(urgency, '🟡')
        
        message_text = f"""
{icon} <b>{alert_type.upper()} ALERT</b>

{message}

Please respond immediately if this requires attention.
        """.strip()
        
        return self.send_message(message_text)
    
    def send_health_tip(self, tip: str, category: str = "General") -> bool:
        """
        Send a health tip or educational message.
        
        Args:
            tip (str): Health tip content
            category (str): Category of the tip
            
        Returns:
            bool: True if message sent successfully
        """
        message = f"""
💡 <b>Health Tip - {category}</b>

{tip}

Stay healthy! 🌟
        """.strip()
        
        return self.send_message(message)
    
    def send_formatted_message(self, 
                             title: str,
                             content: str,
                             message_type: str = "info") -> bool:
        """
        Send a formatted message with title and content.
        
        Args:
            title (str): Message title
            content (str): Message content
            message_type (str): Type of message ('info', 'warning', 'success', 'error')
            
        Returns:
            bool: True if message sent successfully
        """
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'success': '✅',
            'error': '❌'
        }
        
        icon = icons.get(message_type, 'ℹ️')
        
        message = f"""
{icon} <b>{title}</b>

{content}
        """.strip()
        
        return self.send_message(message)
    
    def schedule_message(self, 
                        message: str,
                        send_time: datetime,
                        message_type: str = "scheduled") -> bool:
        """
        Schedule a message to be sent at a specific time.
        
        Args:
            message (str): Message to send
            send_time (datetime): When to send the message
            message_type (str): Type of scheduled message
            
        Returns:
            bool: True if scheduled successfully
        """
        try:
            # Calculate delay until send time
            now = datetime.now()
            if send_time <= now:
                logger.warning("Send time is in the past, sending immediately")
                return self.send_message(message)
            
            delay = (send_time - now).total_seconds()
            
            # Schedule the message
            def send_scheduled_message():
                time.sleep(delay)
                self.send_message(message)
                logger.info(f"Scheduled {message_type} message sent")
            
            # Start thread for scheduled message
            thread = threading.Thread(target=send_scheduled_message)
            thread.daemon = True
            thread.start()
            
            logger.info(f"Message scheduled for {send_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling message: {e}")
            return False
    
    def schedule_recurring_medication_reminder(self,
                                             medication_name: str,
                                             dosage: str,
                                             times: List[str],
                                             additional_notes: str = "") -> bool:
        """
        Schedule recurring medication reminders.
        
        Args:
            medication_name (str): Name of the medication
            dosage (str): Dosage information
            times (List[str]): List of times to send reminders (format: "HH:MM")
            additional_notes (str): Additional instructions
            
        Returns:
            bool: True if scheduled successfully
        """
        try:
            for time_str in times:
                schedule.every().day.at(time_str).do(
                    self.send_medication_reminder,
                    chat_id=self.chat_id,
                    medication_name=medication_name,
                    dosage=dosage,
                    time_to_take=time_str,
                    additional_notes=additional_notes
                )
            
            logger.info(f"Scheduled recurring medication reminders for {medication_name} at {times}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling recurring medication reminder: {e}")
            return False
    
    def get_bot_info(self) -> Dict[str, Any]:
        """
        Get information about the bot.
        
        Returns:
            Dict containing bot information
        """
        try:
            response = requests.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                return response.json()['result']
            else:
                return {"error": f"Failed to get bot info: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error getting bot info: {e}"}
    
    def get_chat_info(self) -> Dict[str, Any]:
        """
        Get information about the chat.
        
        Returns:
            Dict containing chat information
        """
        try:
            response = requests.get(f"{self.base_url}/getChat", params={'chat_id': self.chat_id})
            if response.status_code == 200:
                return response.json()['result']
            else:
                return {"error": f"Failed to get chat info: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error getting chat info: {e}"}


# Convenience function for quick message sending
def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """
    Convenience function to send a Telegram message.
    
    Args:
        message (str): Message to send
        parse_mode (str): Parse mode for formatting
        
    Returns:
        bool: True if sent successfully
    """
    sender = TelegramSender()
    return sender.send_message(message, parse_mode)


def send_medication_reminder(medication_name: str, dosage: str, time_to_take: str, additional_notes: str = "") -> bool:
    """
    Convenience function to send a medication reminder.
    
    Args:
        medication_name (str): Name of the medication
        dosage (str): Dosage information
        time_to_take (str): When to take the medication
        additional_notes (str): Additional instructions
        
    Returns:
        bool: True if sent successfully
    """
    sender = TelegramSender()
    return sender.send_medication_reminder(sender.chat_id, medication_name, dosage, time_to_take, additional_notes)


if __name__ == "__main__":
    # Example usage
    sender = TelegramSender()
    
    # Test basic message sending
    success = sender.send_message("Hello from the Healthcare Discharge Assistant! 🏥")
    print(f"Message sent: {success}")
    
    # Test medication reminder
    sender.send_medication_reminder(
        "Lisinopril",
        "10mg",
        "8:00 AM",
        "Take with food, avoid if blood pressure is too low"
    )
    
    # Test follow-up reminder
    sender.send_follow_up_reminder(
        "Cardiology Follow-up",
        "2024-01-25",
        "2:30 PM",
        "Cardiology Clinic, Room 302",
        "Please bring your medication list"
    )
    
    # Test health tip
    sender.send_health_tip(
        "Remember to stay hydrated! Drink at least 8 glasses of water daily.",
        "Hydration"
    )
    
    # Get bot info
    bot_info = sender.get_bot_info()
    print(f"Bot info: {bot_info}") 