# Google Calendar Setup Guide

To enable Google Calendar integration for follow-up appointments, follow these steps:

## 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API for your project

## 2. Create a Service Account

1. In your Google Cloud project, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Give it a name (e.g., "discharge-assistant")
4. Grant it the "Calendar API Admin" role
5. Create and download the JSON key file

## 3. Set Up the Credentials File

1. Rename the downloaded JSON file to `credentials.json`
2. Place it in the root directory of this project
3. The file should look like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
}
```

## 4. Share Calendar (Optional)

If you want to create events in a specific calendar:
1. Go to Google Calendar
2. Find the calendar you want to use
3. Click the three dots next to the calendar name
4. Select "Settings and sharing"
5. Add your service account email as a user with "Make changes to events" permission

## 5. Test the Integration

Once you have the credentials.json file in place, the Google Calendar integration should work automatically when you use the app.

## Security Note

- Keep your credentials.json file secure and never commit it to version control
- The file is already in .gitignore to prevent accidental commits
- Consider using environment variables for production deployments 