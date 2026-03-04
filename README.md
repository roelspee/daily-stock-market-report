# Daily Market Report — Two-Step Batch Architecture

Solves the Railway timeout problem by splitting into two fast cron jobs:
- Step 1 (7:00 AM): Submits request to Anthropic Batch API — completes in ~2 seconds
- Step 2 (7:15 AM): Retrieves result and sends email — completes in ~5 seconds

No timeout issues. Live web search included.

## Files
- `step1_submit.py`   — submits batch request, saves batch ID to /tmp
- `step2_retrieve.py` — retrieves result, sends email via SendGrid
- `requirements.txt`  — Python dependencies
- `railway.toml`      — Railway build config

## Deploy to Railway

### 1. Push all files to your GitHub repo
Replace the old market_report.py with these new files.
Delete market_report.py and Procfile from the repo.

### 2. In Railway — create TWO cron services from the same repo

You need two separate services pointing at the same GitHub repo,
each with a different start command.

**Service 1 — "submit"**
- Source: same GitHub repo
- Start command: `python step1_submit.py`
- Cron schedule: `0 7 * * *`  (7:00 AM UTC = 8:00 AM Madrid winter)

**Service 2 — "retrieve"**
- Source: same GitHub repo
- Start command: `python step2_retrieve.py`
- Cron schedule: `15 7 * * *` (7:15 AM UTC = 8:15 AM Madrid winter)

### 3. Add environment variables to BOTH services

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | sk-ant-... |
| `SENDGRID_API_KEY`  | SG....     |

Note: step1 only needs ANTHROPIC_API_KEY.
      step2 needs both.

### 4. Important: shared /tmp storage
Both services must run in the same Railway region (us-west2) so they
share the same /tmp filesystem where the batch ID is stored.
Check Settings on both services and confirm region matches.

### 5. Test
Trigger step1 manually first, check logs for "Batch submitted -- ID: msgbatch_..."
Then trigger step2 manually, check logs for "Email sent -- status 202"
Check roelleonard@gmail.com for the report.

## Costs
- Anthropic Batch API: 50% cheaper than regular API (~$0.015/day)
- Railway: both cron services fit in free tier
- SendGrid: free tier (100 emails/day)
