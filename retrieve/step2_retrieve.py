import anthropic
import sendgrid
from sendgrid.helpers.mail import Mail
import os
import time
import traceback
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SENDGRID_API_KEY  = os.environ["SENDGRID_API_KEY"]
SENDER_EMAIL      = "roelspee@protonmail.com"
RECIPIENT_EMAIL   = "roelleonard@gmail.com"
BATCH_ID_FILE     = "/tmp/batch_id.txt"
MAX_WAIT_SECONDS  = 600  # wait up to 10 minutes before giving up

def send_email(html_content):
    today = datetime.now().strftime("%d %b %Y")
    subject = f"Daily Market Report -- {today}"
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=subject,
        html_content=html_content
    )
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"[{datetime.now()}] Email sent -- status {response.status_code}")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting step 2 -- retrieving batch result...")

    if not os.path.exists(BATCH_ID_FILE):
        raise FileNotFoundError(f"Batch ID file not found at {BATCH_ID_FILE}. Did step 1 run?")

    with open(BATCH_ID_FILE, "r") as f:
        batch_id = f.read().strip()

    print(f"[{datetime.now()}] Batch ID: {batch_id}")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    waited = 0
    poll_interval = 15

    while waited < MAX_WAIT_SECONDS:
        batch = client.messages.batches.retrieve(batch_id)
        print(f"[{datetime.now()}] Batch status: {batch.processing_status}")

        if batch.processing_status == "ended":
            break

        print(f"[{datetime.now()}] Not ready yet -- waiting {poll_interval}s...")
        time.sleep(poll_interval)
        waited += poll_interval

    if batch.processing_status != "ended":
        raise TimeoutError(f"Batch did not complete within {MAX_WAIT_SECONDS} seconds")

    print(f"[{datetime.now()}] Batch complete -- retrieving results...")

    full_response = ""
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            for block in result.result.message.content:
                if hasattr(block, "text") and block.text:
                    full_response += block.text
        else:
            raise ValueError(f"Batch request failed: {result.result}")

    if not full_response:
        raise ValueError("Empty response from batch API")

    print(f"[{datetime.now()}] Report retrieved ({len(full_response)} chars)")

    send_email(full_response)
    os.remove(BATCH_ID_FILE)

    print(f"[{datetime.now()}] Done!")
```

---

### `retrieve/requirements.txt`
```
anthropic==0.49.0
sendgrid==6.11.0
