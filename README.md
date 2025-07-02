# Healthcare Discharge Assistant

A comprehensive AI-powered healthcare discharge management system built with Python and Streamlit. This application assists healthcare providers in creating discharge summaries, managing patient data, and setting up automated medication reminders.

## 🏥 Features

### Core Functionality
- **Audio Transcription**: Convert medical audio recordings to text using OpenAI Whisper
- **AI-Powered Summarization**: Generate discharge summaries using LangChain and HuggingFace models
- **PDF Generation**: Create professional discharge summary documents
- **Patient Memory**: Store and retrieve patient profiles using ChromaDB semantic search
- **Multi-language Support**: Translate content using Google Translate API

### Communication & Notifications
- **Telegram Integration**: Send discharge summaries and medication reminders via Telegram bot
- **Email Notifications**: Send discharge summaries via email
- **Google Calendar Integration**: Automatically create follow-up appointments
- **Medication Reminders**: Set up automated medication schedules with customizable frequencies

### Security & Data Management
- **Data Encryption**: Secure sensitive patient information
- **Semantic Search**: Intelligent patient profile retrieval
- **Persistent Storage**: Save schedules and patient data locally

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Telegram Bot Token
- Google Cloud credentials (for Calendar integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ManikantaTalluriGenAi/healthcare_discharge_ai.git
   cd healthcare_discharge_ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with your API keys:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📋 Usage Guide

### Step 1: Audio Upload
- Upload medical audio recordings (MP3, WAV, M4A)
- Audio is automatically transcribed using Whisper
- Review and edit transcription if needed

### Step 2: Patient Information
- Fill in patient details (name, age, diagnosis, etc.)
- Add medications and dosages
- Include follow-up instructions

### Step 3: Generate Summary
- AI generates comprehensive discharge summary
- Review and edit the generated content
- Customize based on specific patient needs

### Step 4: Create PDF
- Generate professional PDF document
- Download for patient records
- Include all relevant medical information

### Step 5: Send Notifications
- Send discharge summary via Telegram
- Email summary to patient/family
- Create Google Calendar follow-up events
- Store patient profile for future reference

### Step 6: Medication Reminders
- Set up medication schedules with custom frequencies
- Configure reminder times (1-6 times per day)
- Start automated Telegram reminders
- Monitor active medication schedules

## 🛠️ Technical Architecture

### Core Modules
- **`app.py`**: Main Streamlit application
- **`utils/transcriber.py`**: Audio transcription using Whisper
- **`utils/summarizer.py`**: AI-powered text summarization
- **`utils/pdf_generator.py`**: PDF document creation
- **`utils/telegram_sender.py`**: Telegram bot integration
- **`utils/email_sender.py`**: Email notification system
- **`utils/calendar.py`**: Google Calendar integration
- **`utils/scheduler.py`**: Medication reminder scheduling
- **`utils/memory.py`**: Patient profile storage with ChromaDB
- **`utils/encryption.py`**: Data encryption utilities

### AI Models Used
- **Whisper**: Audio transcription
- **flan-t5-small**: Text summarization
- **all-MiniLM-L6-v2**: Semantic embeddings for patient search

## 🔧 Configuration

### Telegram Bot Setup
1. Create a bot via @BotFather on Telegram
2. Get your bot token
3. Add bot token to `.env` file
4. Start a chat with your bot to get chat ID

### Google Calendar Integration
1. Create a Google Cloud project
2. Enable Google Calendar API
3. Create service account credentials
4. Download `service_account.json` to project root

### Email Configuration
1. Enable 2-factor authentication on Gmail
2. Generate app password
3. Add email and app password to `.env` file

## 📁 Project Structure
```
healthcare_discharge_ai/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
├── utils/               # Utility modules
│   ├── transcriber.py   # Audio transcription
│   ├── summarizer.py    # AI summarization
│   ├── pdf_generator.py # PDF generation
│   ├── telegram_sender.py # Telegram integration
│   ├── email_sender.py  # Email notifications
│   ├── calendar.py      # Google Calendar
│   ├── scheduler.py     # Medication reminders
│   ├── memory.py        # Patient storage
│   ├── encryption.py    # Data encryption
│   ├── translator.py    # Translation services
│   └── instruction_simplifier.py # Text simplification
└── chroma_db/          # Patient database (auto-created)
```

## 🚨 Important Notes

### Security
- Never commit sensitive credentials to version control
- Use environment variables for API keys
- Encrypt sensitive patient data
- Follow HIPAA guidelines for patient information

### Performance
- Application runs on CPU to avoid GPU memory issues
- Uses smaller AI models for better compatibility
- Optimized for macOS and Linux systems

### Limitations
- Requires internet connection for AI services
- Telegram bot must be active for reminders
- Google Calendar requires valid credentials

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

## 🔄 Updates

### Latest Features
- Auto-generated medication reminder times
- Enhanced patient profile search
- Improved PDF formatting
- Better error handling
- Streamlined user interface

### Planned Features
- Mobile app version
- Integration with hospital systems
- Advanced analytics dashboard
- Multi-language interface
- Voice command support

---

**Built with ❤️ for better healthcare management** 