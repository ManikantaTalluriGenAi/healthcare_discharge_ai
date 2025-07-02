"""
Healthcare Discharge Assistant - Streamlit App
"""

import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
import time
import threading
import certifi

# Set environment variables to help with GPU memory and multiprocessing issues
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

# Import utility modules
from utils.transcriber import AudioTranscriber
from utils.summarizer import DischargeSummarizer
from utils.pdf_generator import PDFGenerator
from utils.telegram_sender import TelegramSender
from utils.email_sender import EmailSender
from utils.calendar import GoogleCalendarManager
from utils.scheduler import HealthcareScheduler
from utils.memory import ChromaDBMemory, create_patient_profile
from utils.encryption import PatientDataEncryption

# Configure page
st.set_page_config(
    page_title="Healthcare Discharge Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: #ecf0f1;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

os.environ["SSL_CERT_FILE"] = certifi.where()

def initialize_session_state():
    """Initialize session state variables."""
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {}
    if 'summary' not in st.session_state:
        st.session_state.summary = ""
    if 'pdf_path' not in st.session_state:
        st.session_state.pdf_path = ""
    if 'medication_reminders' not in st.session_state:
        st.session_state.medication_reminders = []

def main_header():
    """Display main header."""
    st.markdown('<h1 class="main-header">🏥 Healthcare Discharge Assistant</h1>', unsafe_allow_html=True)
    st.markdown("---")

def step_1_audio_upload():
    """Step 1: Audio file upload and transcription."""
    st.markdown('<h2 class="step-header">Step 1: Upload Audio File</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload audio file (MP3, WAV, M4A)",
            type=['mp3', 'wav', 'm4a', 'flac'],
            help="Upload the audio recording of the discharge instructions"
        )
    
    with col2:
        st.info("""
        **Supported formats:**
        - MP3, WAV, M4A, FLAC
        
        **Tips for better transcription:**
        - Clear audio quality
        - Minimal background noise
        - Speak clearly and slowly
        """)
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.1f} KB",
            "File type": uploaded_file.type
        }
        st.json(file_details)
        
        # Transcription options
        st.subheader("Transcription Options")
        col1, col2 = st.columns(2)
        
        with col1:
            model_size = st.selectbox(
                "Whisper Model Size",
                ["base", "small", "medium", "large"],
                index=1,
                help="Larger models are more accurate but slower"
            )
        
        with col2:
            medical_mode = st.checkbox(
                "Medical Mode",
                value=True,
                help="Optimize for medical terminology"
            )
        
        # Transcribe button
        if st.button("🎤 Transcribe Audio", type="primary"):
            with st.spinner("Transcribing audio... This may take a few minutes."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Initialize transcriber
                    transcriber = AudioTranscriber(model_name=model_size)
                    
                    # Transcribe
                    if medical_mode:
                        result = transcriber.transcribe_medical_audio(tmp_file_path)
                    else:
                        result = transcriber.transcribe_audio(tmp_file_path)
                    
                    # Store transcription
                    st.session_state.transcription = result
                    
                    # Clean up temp file
                    os.unlink(tmp_file_path)
                    
                    st.success("✅ Transcription completed successfully!")
                    st.session_state.step = 2
                    
                except Exception as e:
                    st.error(f"❌ Transcription failed: {str(e)}")
    
    # Display transcription if available
    if st.session_state.transcription:
        st.subheader("📝 Transcription Result")
        st.text_area("Transcribed Text", st.session_state.transcription, height=200, disabled=True)
        
        if st.button("🔄 Re-transcribe"):
            st.session_state.transcription = ""
            st.session_state.step = 1
            st.rerun()

def step_2_patient_form():
    """Step 2: Patient information form."""
    st.markdown('<h2 class="step-header">Step 2: Patient Information</h2>', unsafe_allow_html=True)
    
    with st.form("patient_form"):
        st.subheader("Patient Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", value=st.session_state.patient_data.get('name', ''))
            age = st.number_input("Age *", min_value=0, max_value=120, value=st.session_state.patient_data.get('age', 0))
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"], index=0 if st.session_state.patient_data.get('gender') != "Female" else 1)
            diagnosis = st.text_input("Primary Diagnosis *", value=st.session_state.patient_data.get('diagnosis', ''))
        
        with col2:
            admission_date = st.date_input("Admission Date *", value=st.session_state.patient_data.get('admission_date', datetime.now().date()))
            discharge_date = st.date_input("Discharge Date *", value=st.session_state.patient_data.get('discharge_date', datetime.now().date()))
            email = st.text_input("Email Address", value=st.session_state.patient_data.get('email', ''))
            telegram_chat_id = st.text_input("Telegram Chat ID", value=st.session_state.patient_data.get('telegram_chat_id', ''))
        
        st.subheader("Medical History")
        medical_history = st.text_area(
            "Medical History",
            value=st.session_state.patient_data.get('medical_history', ''),
            height=100,
            help="Previous medical conditions, surgeries, etc."
        )
        
        st.subheader("Current Medications")
        medications_input = st.text_area(
            "Current Medications",
            value=st.session_state.patient_data.get('medications', ''),
            height=100,
            help="List current medications with dosages"
        )
        
        st.subheader("Risk Factors")
        risk_factors = st.text_area(
            "Risk Factors",
            value=st.session_state.patient_data.get('risk_factors', ''),
            height=80,
            help="Smoking, diabetes, hypertension, etc."
        )
        
        # Form submission
        submitted = st.form_submit_button("📋 Save Patient Information", type="primary")
        
        if submitted:
            if name and age and diagnosis:
                # Store patient data
                st.session_state.patient_data = {
                    'name': name,
                    'age': age,
                    'gender': gender,
                    'diagnosis': diagnosis,
                    'admission_date': admission_date.strftime("%Y-%m-%d"),
                    'discharge_date': discharge_date.strftime("%Y-%m-%d"),
                    'email': email,
                    'telegram_chat_id': telegram_chat_id,
                    'medical_history': medical_history,
                    'medications': medications_input,
                    'risk_factors': risk_factors
                }
                
                st.success("✅ Patient information saved successfully!")
                st.session_state.step = 3
                st.rerun()
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

def step_3_generate_summary():
    """Step 3: Generate discharge summary."""
    st.markdown('<h2 class="step-header">Step 3: Generate Discharge Summary</h2>', unsafe_allow_html=True)
    
    if not st.session_state.transcription:
        st.error("❌ No transcription available. Please go back to Step 1.")
        return
    
    if not st.session_state.patient_data:
        st.error("❌ No patient data available. Please go back to Step 2.")
        return
    
    st.subheader("Summary Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        summary_type = st.selectbox(
            "Summary Type",
            ["Standard", "Detailed", "Patient-Friendly"],
            help="Choose the level of detail for the summary"
        )
        
        include_medications = st.checkbox("Include Medication Instructions", value=True)
    
    with col2:
        reading_level = st.selectbox(
            "Reading Level",
            ["Basic", "Intermediate", "Advanced"],
            index=1,
            help="Adjust language complexity"
        )
        
        include_follow_up = st.checkbox("Include Follow-up Instructions", value=True)
    
    # Generate summary button
    if st.button("📝 Generate Summary", type="primary"):
        with st.spinner("Generating discharge summary..."):
            try:
                # Initialize summarizer with small model for CPU usage
                try:
                    summarizer = DischargeSummarizer(model_name="google/flan-t5-small")
                except Exception as e:
                    st.error(f"Error loading summarizer model: {e}")
                    st.stop()
                
                # Prepare patient info dictionary
                patient_info = {
                    "name": st.session_state.patient_data['name'],
                    "age": st.session_state.patient_data['age'],
                    "gender": st.session_state.patient_data.get('gender', 'N/A'),
                    "medical_history": st.session_state.patient_data['medical_history'],
                    "current_medications": st.session_state.patient_data['medications'],
                    "allergies": st.session_state.patient_data.get('allergies', 'None')
                }
                
                # Generate summary
                if summary_type == "Standard":
                    summary = summarizer.generate_summary(st.session_state.transcription, patient_info)
                elif summary_type == "Detailed":
                    structured_summary = summarizer.generate_structured_summary(st.session_state.transcription, patient_info)
                    summary = structured_summary.get("main_summary", "Error generating structured summary")
                else:  # Patient-Friendly
                    summary = summarizer.generate_patient_friendly_summary(st.session_state.transcription, patient_info)
                
                st.session_state.summary = summary
                
                st.success("✅ Discharge summary generated successfully!")
                st.session_state.step = 4
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Summary generation failed: {str(e)}")
    
    # Display summary if available
    if st.session_state.summary:
        st.subheader("📋 Generated Summary")
        st.text_area("Discharge Summary", st.session_state.summary, height=300, disabled=True)

def step_4_pdf_generation():
    """Step 4: Generate and download PDF."""
    st.markdown('<h2 class="step-header">Step 4: Generate PDF</h2>', unsafe_allow_html=True)
    
    if not st.session_state.summary:
        st.error("❌ No summary available. Please go back to Step 3.")
        return
    
    st.subheader("PDF Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_medications = st.checkbox("Include Medications Section", value=True)
        include_follow_up = st.checkbox("Include Follow-up Instructions", value=True)
    
    with col2:
        pdf_title = st.text_input("PDF Title", value=f"Discharge Summary - {st.session_state.patient_data.get('name', 'Patient')}")
        include_signatures = st.checkbox("Include Signature Section", value=True)
    
    # Generate PDF button
    if st.button("📄 Generate PDF", type="primary"):
        with st.spinner("Generating PDF..."):
            try:
                # Initialize PDF generator
                generator = PDFGenerator()
                
                # Prepare medications list
                medications = []
                if include_medications and st.session_state.patient_data.get('medications'):
                    med_list = st.session_state.patient_data['medications'].split('\n')
                    medications = [med.strip() for med in med_list if med.strip()]
                
                # Generate PDF
                pdf_path = generator.create_discharge_summary(
                    patient_data=st.session_state.patient_data,
                    discharge_summary=st.session_state.summary,
                    medications=medications if include_medications else None,
                    follow_up_instructions=st.session_state.summary if include_follow_up else ""
                )
                
                st.session_state.pdf_path = pdf_path
                
                st.success("✅ PDF generated successfully!")
                st.session_state.step = 5
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ PDF generation failed: {str(e)}")
    
    # Download PDF if available
    if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
        st.subheader("📄 Download PDF")
        
        with open(st.session_state.pdf_path, "rb") as file:
            pdf_bytes = file.read()
        
        st.download_button(
            label="📥 Download Discharge Summary PDF",
            data=pdf_bytes,
            file_name=os.path.basename(st.session_state.pdf_path),
            mime="application/pdf"
        )
        
        # Display PDF info
        file_size = os.path.getsize(st.session_state.pdf_path) / 1024
        st.info(f"📊 PDF Size: {file_size:.1f} KB")

def step_5_notifications():
    """Step 5: Send notifications via Telegram and Email."""
    st.markdown('<h2 class="step-header">Step 5: Send Notifications</h2>', unsafe_allow_html=True)
    
    if not st.session_state.summary:
        st.error("❌ No summary available. Please go back to Step 3.")
        return
    
    st.subheader("Notification Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        send_telegram = st.checkbox("Send Telegram Message", value=True)
        send_email = st.checkbox("Send Email", value=True)
    
    with col2:
        send_calendar = st.checkbox("Create Google Calendar Event", value=True)
        store_in_memory = st.checkbox("Store in Patient Memory", value=True)
    
    # Notification content
    st.subheader("Notification Content")
    
    telegram_message = st.text_area(
        "Telegram Message",
        value=f"Discharge Summary for {st.session_state.patient_data.get('name', 'Patient')}:\n\n{st.session_state.summary[:500]}...",
        height=150
    )
    
    email_subject = st.text_input(
        "Email Subject",
        value=f"Discharge Summary - {st.session_state.patient_data.get('name', 'Patient')}"
    )
    
    # Send notifications button
    if st.button("📤 Send Notifications", type="primary"):
        with st.spinner("Sending notifications..."):
            success_count = 0
            total_count = 0
            
            try:
                # Send Telegram message
                if send_telegram and st.session_state.patient_data.get('telegram_chat_id'):
                    total_count += 1
                    try:
                        telegram = TelegramSender()
                        telegram.send_discharge_summary(
                            chat_id=st.session_state.patient_data['telegram_chat_id'],
                            patient_name=st.session_state.patient_data['name'],
                            summary=telegram_message
                        )
                        success_count += 1
                        st.success("✅ Telegram message sent successfully!")
                    except Exception as e:
                        st.error(f"❌ Telegram message failed: {str(e)}")
                
                # Send Email
                if send_email and st.session_state.patient_data.get('email'):
                    total_count += 1
                    try:
                        email_sender = EmailSender()
                        if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                                                    email_sender.send_discharge_summary_email(
                            recipient_email=st.session_state.patient_data['email'],
                            patient_name=st.session_state.patient_data['name'],
                            summary_text=st.session_state.summary,
                            pdf_path=st.session_state.pdf_path
                        )
                        else:
                            email_sender.send_healthcare_email(
                                to_email=st.session_state.patient_data['email'],
                                subject=email_subject,
                                message=st.session_state.summary
                            )
                        success_count += 1
                        st.success("✅ Email sent successfully!")
                    except Exception as e:
                        st.error(f"❌ Email failed: {str(e)}")
                
                # Create Google Calendar event
                if send_calendar:
                    total_count += 1
                    try:
                        calendar = GoogleCalendarManager()
                        event_id = calendar.create_followup_event(
                            patient_name=st.session_state.patient_data['name'],
                            discharge_date=datetime.strptime(st.session_state.patient_data['discharge_date'], "%Y-%m-%d"),
                            appointment_type="Follow-up",
                            location="Hospital Outpatient Clinic",
                            description=f"Follow-up appointment for {st.session_state.patient_data['diagnosis']}"
                        )
                        if event_id:
                            success_count += 1
                            st.success("✅ Google Calendar event created successfully!")
                        else:
                            st.error("❌ Google Calendar event creation failed")
                    except Exception as e:
                        st.error(f"❌ Google Calendar failed: {str(e)}")
                
                # Store in memory
                if store_in_memory:
                    total_count += 1
                    try:
                        memory = ChromaDBMemory()
                        # Clean up medications and risk factors
                        medications = []
                        if st.session_state.patient_data.get('medications'):
                            med_list = st.session_state.patient_data['medications'].split('\n')
                            medications = [med.strip() for med in med_list if med.strip()]
                        
                        risk_factors = []
                        if st.session_state.patient_data.get('risk_factors'):
                            risk_list = st.session_state.patient_data['risk_factors'].split('\n')
                            risk_factors = [risk.strip() for risk in risk_list if risk.strip()]
                        
                        patient_profile = create_patient_profile(
                            name=st.session_state.patient_data['name'],
                            age=st.session_state.patient_data['age'],
                            gender=st.session_state.patient_data['gender'],
                            diagnosis=st.session_state.patient_data['diagnosis'],
                            medications=medications,
                            follow_up_notes=st.session_state.summary,
                            risk_factors=risk_factors,
                            comorbidities=[],
                            treatment_plan=st.session_state.summary
                        )
                        if memory.add_patient_profile(patient_profile):
                            success_count += 1
                            st.success("✅ Patient profile stored in memory!")
                        else:
                            st.error("❌ Failed to store patient profile")
                    except Exception as e:
                        st.error(f"❌ Memory storage failed: {str(e)}")
                
                # Summary
                if success_count == total_count and total_count > 0:
                    st.success(f"🎉 All notifications sent successfully! ({success_count}/{total_count})")
                    st.session_state.step = 6
                elif success_count > 0:
                    st.warning(f"⚠️ Some notifications sent successfully ({success_count}/{total_count})")
                    st.session_state.step = 6
                else:
                    st.error("❌ No notifications were sent successfully")
                
            except Exception as e:
                st.error(f"❌ Notification process failed: {str(e)}")

def step_6_medication_reminders():
    """Step 6: Set up medication reminders."""
    st.markdown('<h2 class="step-header">Step 6: Medication Reminders</h2>', unsafe_allow_html=True)
    
    st.subheader("Set Up Medication Reminders")
    st.info("Add medications and set up Telegram reminders for the patient.")
    
    # Add new medication reminder
    with st.form("medication_reminder_form"):
        st.subheader("Add New Medication Reminder")
        
        col1, col2 = st.columns(2)
        
        with col1:
            medication_name = st.text_input("Medication Name *")
            dosage = st.text_input("Dosage (e.g., 500mg twice daily)")
        
        with col2:
            frequency = st.selectbox(
                "Frequency (times per day) *",
                options=[1, 2, 3, 4, 5, 6],
                index=1,  # Default to 2 times per day
                help="How many times per day should the medication be taken?"
            )
            duration_days = st.number_input("Duration (days) *", min_value=1, max_value=365, value=7)
        
        # Auto-generate times based on frequency
        st.subheader("Reminder Times")
        reminder_times = []
        
        # Auto-generate appropriate times based on frequency
        if frequency == 1:
            # Once daily - default to morning
            default_time = datetime(2024, 1, 1, 8, 0).time()
            time1 = st.time_input("Time *", value=default_time, key="time1")
            reminder_times.append(time1.strftime("%H:%M"))
            
        elif frequency == 2:
            # Twice daily - morning and evening
            col1, col2 = st.columns(2)
            with col1:
                time1 = st.time_input("Morning Time *", value=datetime(2024, 1, 1, 8, 0).time(), key="time1")
                reminder_times.append(time1.strftime("%H:%M"))
            with col2:
                time2 = st.time_input("Evening Time *", value=datetime(2024, 1, 1, 20, 0).time(), key="time2")
                reminder_times.append(time2.strftime("%H:%M"))
                
        elif frequency == 3:
            # Three times daily - morning, afternoon, evening
            col1, col2, col3 = st.columns(3)
            with col1:
                time1 = st.time_input("Morning Time *", value=datetime(2024, 1, 1, 8, 0).time(), key="time1")
                reminder_times.append(time1.strftime("%H:%M"))
            with col2:
                time2 = st.time_input("Afternoon Time *", value=datetime(2024, 1, 1, 14, 0).time(), key="time2")
                reminder_times.append(time2.strftime("%H:%M"))
            with col3:
                time3 = st.time_input("Evening Time *", value=datetime(2024, 1, 1, 20, 0).time(), key="time3")
                reminder_times.append(time3.strftime("%H:%M"))
                
        elif frequency == 4:
            # Four times daily - every 6 hours
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                time1 = st.time_input("Time 1 *", value=datetime(2024, 1, 1, 6, 0).time(), key="time1")
                reminder_times.append(time1.strftime("%H:%M"))
            with col2:
                time2 = st.time_input("Time 2 *", value=datetime(2024, 1, 1, 12, 0).time(), key="time2")
                reminder_times.append(time2.strftime("%H:%M"))
            with col3:
                time3 = st.time_input("Time 3 *", value=datetime(2024, 1, 1, 18, 0).time(), key="time3")
                reminder_times.append(time3.strftime("%H:%M"))
            with col4:
                time4 = st.time_input("Time 4 *", value=datetime(2024, 1, 1, 0, 0).time(), key="time4")
                reminder_times.append(time4.strftime("%H:%M"))
                
        elif frequency == 5:
            # Five times daily - every 4-5 hours
            col1, col2, col3, col4, col5 = st.columns(5)
            times = [6, 10, 14, 18, 22]  # Every 4 hours
            for i, hour in enumerate(times, 1):
                with eval(f"col{i}"):
                    time_val = st.time_input(f"Time {i} *", value=datetime(2024, 1, 1, hour, 0).time(), key=f"time{i}")
                    reminder_times.append(time_val.strftime("%H:%M"))
                    
        elif frequency == 6:
            # Six times daily - every 4 hours including night
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            times = [6, 10, 14, 18, 22, 2]  # Every 4 hours including night
            for i, hour in enumerate(times, 1):
                with eval(f"col{i}"):
                    time_val = st.time_input(f"Time {i} *", value=datetime(2024, 1, 1, hour, 0).time(), key=f"time{i}")
                    reminder_times.append(time_val.strftime("%H:%M"))
        
        # Show auto-generated times info
        if frequency > 1:
            st.info(f"💡 Auto-generated {frequency} reminder times. You can adjust these times as needed.")
        
        reminder_message = st.text_area(
            "Reminder Message",
            value="Time to take your medication!",
            height=80
        )
        
        add_reminder = st.form_submit_button("➕ Add Reminder", type="primary")
        
        if add_reminder:
            if medication_name and reminder_times and st.session_state.patient_data.get('telegram_chat_id'):
                # Add to session state
                reminder = {
                    'medication': medication_name,
                    'dosage': dosage,
                    'times': reminder_times,
                    'frequency': frequency,
                    'duration': duration_days,
                    'message': reminder_message,
                    'patient_name': st.session_state.patient_data['name'],
                    'chat_id': st.session_state.patient_data['telegram_chat_id']
                }
                
                st.session_state.medication_reminders.append(reminder)
                st.success(f"✅ Added reminder for {medication_name} ({frequency}x daily)")
                st.rerun()
            else:
                st.error("❌ Please fill in medication name, set reminder times, and ensure Telegram chat ID is available")
    
    # Display current reminders
    if st.session_state.medication_reminders:
        st.subheader("📋 Current Medication Reminders")
        
        for i, reminder in enumerate(st.session_state.medication_reminders):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**{reminder['medication']}**")
                if reminder.get('dosage'):
                    st.write(f"Dosage: {reminder['dosage']}")
                st.write(f"Frequency: {reminder['frequency']}x daily")
                st.write(f"Message: {reminder['message']}")
            
            with col2:
                st.write("**Times:**")
                for j, time in enumerate(reminder['times'], 1):
                    st.write(f"• {time}")
            
            with col3:
                st.write(f"Duration: {reminder['duration']} days")
            
            with col4:
                if st.button(f"❌ Remove", key=f"remove_{i}"):
                    st.session_state.medication_reminders.pop(i)
                    st.rerun()
    
    # Start reminders button
    if st.session_state.medication_reminders:
        if st.button("🚀 Start All Reminders", type="primary"):
            with st.spinner("Starting medication reminders..."):
                try:
                    scheduler = HealthcareScheduler()
                    
                    for reminder in st.session_state.medication_reminders:
                        # Add medication schedule
                        scheduler.add_medication_schedule(
                            medication_name=reminder['medication'],
                            dosage=reminder.get('dosage', ''),
                            times=reminder['times'],
                            duration_days=reminder['duration'],
                            additional_notes=reminder['message'],
                            chat_id=reminder['chat_id']
                        )
                    
                    # Start scheduler in background thread
                    def run_scheduler():
                        scheduler.start_scheduler()
                    
                    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
                    scheduler_thread.start()
                    
                    st.success("✅ Medication reminders started successfully!")
                    st.info("💡 Reminders will be sent via Telegram at the specified times.")
                    
                except Exception as e:
                    st.error(f"❌ Failed to start reminders: {str(e)}")
    
    # Final summary
    st.subheader("🎉 Discharge Process Complete!")
    st.success("""
    The discharge process has been completed successfully! Here's what was accomplished:
    
    ✅ Audio transcription completed
    ✅ Patient information collected
    ✅ Discharge summary generated
    ✅ PDF document created
    ✅ Notifications sent
    ✅ Medication reminders configured
    
    The patient is now ready for discharge with all necessary documentation and follow-up care arranged.
    """)

def sidebar_navigation():
    """Sidebar navigation."""
    st.sidebar.title("🏥 Navigation")
    
    # Progress indicator
    steps = [
        "Audio Upload",
        "Patient Form", 
        "Generate Summary",
        "Create PDF",
        "Send Notifications",
        "Medication Reminders"
    ]
    
    st.sidebar.subheader("Progress")
    for i, step in enumerate(steps, 1):
        if i < st.session_state.step:
            st.sidebar.success(f"✅ {step}")
        elif i == st.session_state.step:
            st.sidebar.info(f"🔄 {step}")
        else:
            st.sidebar.write(f"⏳ {step}")
    
    st.sidebar.markdown("---")
    
    # Manual navigation
    st.sidebar.subheader("Manual Navigation")
    for i, step in enumerate(steps, 1):
        if st.sidebar.button(f"Go to Step {i}: {step}", key=f"nav_{i}"):
            st.session_state.step = i
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Reset button
    if st.sidebar.button("🔄 Reset All"):
        for key in ['transcription', 'patient_data', 'summary', 'pdf_path', 'medication_reminders']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.step = 1
        st.rerun()
    
    # About section
    st.sidebar.markdown("---")
    st.sidebar.subheader("About")
    st.sidebar.info("""
    **Healthcare Discharge Assistant**
    
    This application helps healthcare providers create comprehensive discharge summaries and manage patient follow-up care.
    
    **Features:**
    - Audio transcription
    - AI-powered summaries
    - PDF generation
    - Automated notifications
    - Medication reminders
    - Calendar integration
    """)

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    main_header()
    
    # Sidebar navigation
    sidebar_navigation()
    
    # Main content based on current step
    if st.session_state.step == 1:
        step_1_audio_upload()
    elif st.session_state.step == 2:
        step_2_patient_form()
    elif st.session_state.step == 3:
        step_3_generate_summary()
    elif st.session_state.step == 4:
        step_4_pdf_generation()
    elif st.session_state.step == 5:
        step_5_notifications()
    elif st.session_state.step == 6:
        step_6_medication_reminders()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Healthcare Discharge Assistant | Built with Streamlit and AI"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 