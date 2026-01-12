import requests

# Replace with your actual webhook URL
import os

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Simple test message
payload = {
    "text": "✅ Hello Slack! This is a test message from your AI Support Engine."
}

response = requests.post(SLACK_WEBHOOK_URL, json=payload)

print("Status Code:", response.status_code)
print("Response:", response.text)
