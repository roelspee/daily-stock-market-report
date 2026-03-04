# Daily Market Report — Railway Deployment

Runs every morning at 7:00 AM (UTC). Searches live financial news via Anthropic's
web search tool and emails a personalised Top 10 market report via SendGrid.

## Files
- `market_report.py` — main script
- `requirements.txt` — Python dependencies
- `railway.toml` — Railway config + cron schedule

## Deploy to Railway

### 1. Create a GitHub repo
Upload these 3 files to a new GitHub repository (e.g. `daily-market-report`).

### 2. Create a Railway project
1. Go to railway.app and log in
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Railway will auto-detect Python and install dependencies

### 3. Add environment variables
In Railway → your project → **Variables**, add:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your Anthropic API key (starts with sk-ant-) |
| `SENDGRID_API_KEY` | your SendGrid API key |

### 4. Set the timezone (optional)
The cron runs at 07:00 UTC by default. To get 7:00 AM Madrid time (UTC+1 in winter, UTC+2 in summer):
- Winter: set cronSchedule to `0 6 * * *`
- Summer: set cronSchedule to `0 5 * * *`

Or just leave it at UTC and receive it at 8:00 AM Madrid time (close enough).

### 5. Test it manually
In Railway → your project → **Deployments** → click **Deploy** to trigger a one-off run.
Check the logs to confirm it ran successfully, then check your inbox.

### 6. It runs automatically from here
Railway will execute the script every morning per the cron schedule.
No Make.com needed.

## Costs
- Railway free tier: $5 free credit/month — this script uses ~$0.01/month of compute
- Anthropic API: ~$0.03-0.05 per run with web search → ~$1.50/month
- SendGrid free tier: 100 emails/day — more than enough

## Updating your portfolio
When your portfolio changes, edit the SYSTEM_PROMPT in market_report.py and push to GitHub.
Railway will automatically redeploy.
