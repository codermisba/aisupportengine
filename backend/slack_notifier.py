import requests
import os

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_to_slack(ticket_text, recommendation):
    try:
        score = int(recommendation["score"] * 100)

        payload = {
            "text": "🤖 AI Content Gap Alert",
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

        r = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=3)

        if r.status_code != 200:
            print("⚠️ Slack error:", r.text)

    except Exception as e:
        print("⚠️ Slack notification failed:", e)
