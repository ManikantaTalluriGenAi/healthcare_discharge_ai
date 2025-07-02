"""
Email Sender Module using SMTP for Gmail
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email import encoders
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    """
    A class to send emails via Gmail SMTP.
    """
    
    def __init__(self):
        """
        Initialize the email sender with Gmail credentials from environment variables.
        """
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        self._validate_credentials()
    
    def _validate_credentials(self):
        """Validate email credentials."""
        if not self.email:
            raise ValueError("EMAIL not found in environment variables")
        if not self.password:
            raise ValueError("EMAIL_PASSWORD not found in environment variables")
        
        logger.info(f"Email sender initialized for: {self.email}")
    
    def send_discharge_summary_email(self,
                                   recipient_email: str,
                                   patient_name: str,
                                   pdf_path: str,
                                   summary_text: str = "",
                                   additional_notes: str = "") -> bool:
        """
        Send a discharge summary email with PDF attachment.
        
        Args:
            recipient_email (str): Recipient's email address
            patient_name (str): Patient's name
            pdf_path (str): Path to the discharge PDF file
            summary_text (str): Summary text to include in email body
            additional_notes (str): Additional notes or instructions
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = f"Discharge Summary - {patient_name}"
            
            # Create email body
            body = self._create_discharge_email_body(
                patient_name, summary_text, additional_notes
            )
            
            # Send email with PDF attachment
            success = self._send_email_with_attachment(
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                attachment_path=pdf_path,
                attachment_name=f"Discharge_Summary_{patient_name.replace(' ', '_')}.pdf"
            )
            
            if success:
                logger.info(f"Discharge summary email sent to {recipient_email} for {patient_name}")
            else:
                logger.error(f"Failed to send discharge summary email to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending discharge summary email: {e}")
            return False
    
    def send_medication_reminder_email(self,
                                     recipient_email: str,
                                     patient_name: str,
                                     medication_name: str,
                                     dosage: str,
                                     time_to_take: str,
                                     additional_instructions: str = "") -> bool:
        """
        Send a medication reminder email.
        
        Args:
            recipient_email (str): Recipient's email address
            patient_name (str): Patient's name
            medication_name (str): Name of the medication
            dosage (str): Dosage information
            time_to_take (str): When to take the medication
            additional_instructions (str): Additional instructions
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"Medication Reminder - {medication_name}"
            
            body = self._create_medication_reminder_body(
                patient_name, medication_name, dosage, time_to_take, additional_instructions
            )
            
            success = self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                body=body
            )
            
            if success:
                logger.info(f"Medication reminder email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending medication reminder email: {e}")
            return False
    
    def send_followup_reminder_email(self,
                                   recipient_email: str,
                                   patient_name: str,
                                   appointment_type: str,
                                   appointment_date: str,
                                   appointment_time: str,
                                   location: str = "",
                                   notes: str = "") -> bool:
        """
        Send a follow-up appointment reminder email.
        
        Args:
            recipient_email (str): Recipient's email address
            patient_name (str): Patient's name
            appointment_type (str): Type of appointment
            appointment_date (str): Appointment date
            appointment_time (str): Appointment time
            location (str): Appointment location
            notes (str): Additional notes
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"Follow-up Appointment Reminder - {appointment_type}"
            
            body = self._create_followup_reminder_body(
                patient_name, appointment_type, appointment_date, 
                appointment_time, location, notes
            )
            
            success = self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                body=body
            )
            
            if success:
                logger.info(f"Follow-up reminder email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending follow-up reminder email: {e}")
            return False
    
    def send_general_healthcare_email(self,
                                    recipient_email: str,
                                    subject: str,
                                    body: str,
                                    attachments: List[str] = None) -> bool:
        """
        Send a general healthcare email with optional attachments.
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body
            attachments (List[str]): List of file paths to attach
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if attachments:
                success = self._send_email_with_attachments(
                    recipient_email=recipient_email,
                    subject=subject,
                    body=body,
                    attachment_paths=attachments
                )
            else:
                success = self._send_email(
                    recipient_email=recipient_email,
                    subject=subject,
                    body=body
                )
            
            if success:
                logger.info(f"General healthcare email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending general healthcare email: {e}")
            return False
    
    def _send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """
        Send a basic email without attachments.
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add body to email
            message.attach(MIMEText(body, "html"))
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                # Send email
                text = message.as_string()
                server.sendmail(self.email, recipient_email, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _send_email_with_attachment(self, 
                                  recipient_email: str, 
                                  subject: str, 
                                  body: str,
                                  attachment_path: str,
                                  attachment_name: str = None) -> bool:
        """
        Send an email with a single attachment.
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body
            attachment_path (str): Path to attachment file
            attachment_name (str): Name for the attachment
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not os.path.exists(attachment_path):
                logger.error(f"Attachment file not found: {attachment_path}")
                return False
            
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add body to email
            message.attach(MIMEText(body, "html"))
            
            # Add attachment
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            # Encode attachment
            encoders.encode_base64(part)
            
            # Add header
            if attachment_name is None:
                attachment_name = os.path.basename(attachment_path)
            
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment_name}",
            )
            
            message.attach(part)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                # Send email
                text = message.as_string()
                server.sendmail(self.email, recipient_email, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email with attachment: {e}")
            return False
    
    def _send_email_with_attachments(self,
                                   recipient_email: str,
                                   subject: str,
                                   body: str,
                                   attachment_paths: List[str]) -> bool:
        """
        Send an email with multiple attachments.
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            body (str): Email body
            attachment_paths (List[str]): List of attachment file paths
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add body to email
            message.attach(MIMEText(body, "html"))
            
            # Add attachments
            for attachment_path in attachment_paths:
                if not os.path.exists(attachment_path):
                    logger.warning(f"Attachment file not found: {attachment_path}")
                    continue
                
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                # Encode attachment
                encoders.encode_base64(part)
                
                # Add header
                attachment_name = os.path.basename(attachment_path)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attachment_name}",
                )
                
                message.attach(part)
            
            # Create SMTP session
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                
                # Send email
                text = message.as_string()
                server.sendmail(self.email, recipient_email, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email with attachments: {e}")
            return False
    
    def _create_discharge_email_body(self, 
                                   patient_name: str,
                                   summary_text: str,
                                   additional_notes: str) -> str:
        """
        Create HTML body for discharge summary email.
        
        Args:
            patient_name (str): Patient's name
            summary_text (str): Summary text
            additional_notes (str): Additional notes
            
        Returns:
            str: HTML email body
        """
        body = f"""
        <html>
        <body>
            <h2>🏥 Discharge Summary</h2>
            
            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            
            {f'<p><strong>Summary:</strong><br>{summary_text}</p>' if summary_text else ''}
            
            {f'<p><strong>Additional Notes:</strong><br>{additional_notes}</p>' if additional_notes else ''}
            
            <p>The discharge summary PDF is attached to this email.</p>
            
            <p>Please review the information carefully and contact us if you have any questions.</p>
            
            <hr>
            <p><em>This is an automated message from the Healthcare Discharge Assistant.</em></p>
        </body>
        </html>
        """
        
        return body
    
    def _create_medication_reminder_body(self,
                                       patient_name: str,
                                       medication_name: str,
                                       dosage: str,
                                       time_to_take: str,
                                       additional_instructions: str) -> str:
        """
        Create HTML body for medication reminder email.
        
        Args:
            patient_name (str): Patient's name
            medication_name (str): Medication name
            dosage (str): Dosage information
            time_to_take (str): When to take medication
            additional_instructions (str): Additional instructions
            
        Returns:
            str: HTML email body
        """
        body = f"""
        <html>
        <body>
            <h2>💊 Medication Reminder</h2>
            
            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Medication:</strong> {medication_name}</p>
            <p><strong>Dosage:</strong> {dosage}</p>
            <p><strong>Time to Take:</strong> {time_to_take}</p>
            
            {f'<p><strong>Additional Instructions:</strong><br>{additional_instructions}</p>' if additional_instructions else ''}
            
            <p>Please take your medication as prescribed.</p>
            
            <hr>
            <p><em>This is an automated reminder from the Healthcare Discharge Assistant.</em></p>
        </body>
        </html>
        """
        
        return body
    
    def _create_followup_reminder_body(self,
                                     patient_name: str,
                                     appointment_type: str,
                                     appointment_date: str,
                                     appointment_time: str,
                                     location: str,
                                     notes: str) -> str:
        """
        Create HTML body for follow-up reminder email.
        
        Args:
            patient_name (str): Patient's name
            appointment_type (str): Type of appointment
            appointment_date (str): Appointment date
            appointment_time (str): Appointment time
            location (str): Appointment location
            notes (str): Additional notes
            
        Returns:
            str: HTML email body
        """
        body = f"""
        <html>
        <body>
            <h2>📅 Follow-up Appointment Reminder</h2>
            
            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Appointment Type:</strong> {appointment_type}</p>
            <p><strong>Date:</strong> {appointment_date}</p>
            <p><strong>Time:</strong> {appointment_time}</p>
            
            {f'<p><strong>Location:</strong> {location}</p>' if location else ''}
            
            {f'<p><strong>Notes:</strong><br>{notes}</p>' if notes else ''}
            
            <p>Please confirm your appointment or contact us if you need to reschedule.</p>
            
            <hr>
            <p><em>This is an automated reminder from the Healthcare Discharge Assistant.</em></p>
        </body>
        </html>
        """
        
        return body


# Convenience functions
def send_discharge_summary_email(recipient_email: str, patient_name: str, 
                               pdf_path: str, summary_text: str = "") -> bool:
    """
    Convenience function to send a discharge summary email.
    
    Args:
        recipient_email (str): Recipient's email address
        patient_name (str): Patient's name
        pdf_path (str): Path to the discharge PDF file
        summary_text (str): Summary text to include in email body
        
    Returns:
        bool: True if email sent successfully
    """
    sender = EmailSender()
    return sender.send_discharge_summary_email(
        recipient_email, patient_name, pdf_path, summary_text
    )


def send_medication_reminder_email(recipient_email: str, patient_name: str,
                                 medication_name: str, dosage: str, time_to_take: str) -> bool:
    """
    Convenience function to send a medication reminder email.
    
    Args:
        recipient_email (str): Recipient's email address
        patient_name (str): Patient's name
        medication_name (str): Name of the medication
        dosage (str): Dosage information
        time_to_take (str): When to take the medication
        
    Returns:
        bool: True if email sent successfully
    """
    sender = EmailSender()
    return sender.send_medication_reminder_email(
        recipient_email, patient_name, medication_name, dosage, time_to_take
    )


if __name__ == "__main__":
    # Example usage
    sender = EmailSender()
    
    # Test basic email sending
    success = sender.send_general_healthcare_email(
        recipient_email="test@example.com",
        subject="Test Email from Healthcare Assistant",
        body="<h2>Test Email</h2><p>This is a test email from the Healthcare Discharge Assistant.</p>"
    )
    
    print(f"Test email sent: {success}")
    
    # Test discharge summary email (requires actual PDF file)
    # success = sender.send_discharge_summary_email(
    #     recipient_email="patient@example.com",
    #     patient_name="John Doe",
    #     pdf_path="discharge_summary.pdf",
    #     summary_text="Patient discharged after successful treatment."
    # )
    
    # Test medication reminder email
    success = sender.send_medication_reminder_email(
        recipient_email="patient@example.com",
        patient_name="John Doe",
        medication_name="Lisinopril",
        dosage="10mg",
        time_to_take="8:00 AM",
        additional_instructions="Take with food"
    )
    
    print(f"Medication reminder email sent: {success}") 