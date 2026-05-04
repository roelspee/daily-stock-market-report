import anthropic
import resend
import os
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY    = os.environ["RESEND_API_KEY"]

EMAIL_SENDER      = "onboarding@resend.dev"
EMAIL_RECEIVER    = "roelspee@protonmail.com"

MAX_WAIT_SECONDS  = 600

resend.api_key = RESEND_API_KEY


def send_email(html_content):
    today = datetime.now().strftime("%d %b %Y")
    subject = f"Daily Market Report -- {today}"

    r = resend.Emails.send({
        "from": EMAIL_SENDER,
        "to": EMAIL_RECEIVER,
        "subject": subject,
        "html": html_content,
    })
    print(f"[{datetime.now()}] Email sent (id: {r['id']})")


if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting step 2 -- finding latest batch...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Get the most recent batch -- no need to pass batch ID between containers
    batches = client.messages.batches.list(limit=1)
    if not batches.data:
        raise ValueError("No batches found in Anthropic account")

    batch = batches.data[0]
    batch_id = batch.id
    print(f"[{datetime.now()}] Found latest batch -- ID: {batch_id} -- status: {batch.processing_status}")

    # Poll until complete
    waited = 0
    poll_interval = 15

    while waited < MAX_WAIT_SECONDS:
        if batch.processing_status == "ended":
            break
        print(f"[{datetime.now()}] Not ready yet -- waiting {poll_interval}s...")
        time.sleep(poll_interval)
        waited += poll_interval
        batch = client.messages.batches.retrieve(batch_id)
        print(f"[{datetime.now()}] Batch status: {batch.processing_status}")

    if batch.processing_status != "ended":
        raise TimeoutError(f"Batch did not complete within {MAX_WAIT_SECONDS} seconds")

    # Retrieve results
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
    print(f"[{datetime.now()}] Done!")
