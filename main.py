import json
import os
from urllib import request as urllib_request


def build_slack_payload():
    return {
        "text": " *데일리 스크럼 시간입니다!* (오전 10시)",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "데일리 스크럼",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "안녕하세요! 오늘의 데일리 스크럼을 작성해주세요 :wave:\n아래 양식을 복사해서 사용하세요.",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "```데일리 스크럼 양식\n\n 이름:\n\n 어제 한 일:\n-\n\n 오늘 할 일:\n-\n\n 블로커 / 이슈:\n-\n\n 공유 사항:\n-```",
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "매일 오전 10시 10분 자동 발송",
                    }
                ],
            },
        ],
    }


def send_slack_message(webhook_url, payload):
    request = urllib_request.Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib_request.urlopen(request, timeout=5) as response:
        status_code = getattr(response, "status", 200)
        if status_code >= 400:
            raise RuntimeError(f"Slack webhook request failed with status {status_code}")


def lambda_handler(event, context):
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    payload = build_slack_payload()
    send_slack_message(webhook_url, payload)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Daily scrum reminder sent"}),
    }
