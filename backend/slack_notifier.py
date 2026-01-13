import requests
import os

from dotenv import load_dotenv  # <--- THIS LINE IS MISSING

# Load .env variables
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_to_slack(ticket_text, recommendation):
    

    if not SLACK_WEBHOOK_URL:
        print("⚠️ Slack webhook not configured. Skipping notification.")
        return
    try:
        score = int(recommendation["score"] * 100)

        payload = {
            "text": "AI Content Gap Alert",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Ticket:* {ticket_text}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Article:* {recommendation['title']}"},
                        {"type": "mrkdwn", "text": f"*Confidence:* {score}%"}
                    ]
                }
            ]
        }

        r = requests.post(SLACK_WEBHOOK_URL, json=payload)

        if r.status_code != 200:
            print("⚠️ Slack error:", r.text)

    except Exception as e:
        print("⚠️ Slack notification failed:", e)
