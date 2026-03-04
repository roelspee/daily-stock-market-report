import anthropic
import os
import json
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BATCH_ID_FILE     = "/tmp/batch_id.txt"

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a financial analyst assistant for a European investor based in Spain.

Investor profile:
- Age 40, works in tech (career income correlated with tech/NASDAQ)
- Platform: DEGIRO Spain (MiFID II applies -- cannot buy US-domiciled ETFs)
- Currency: EUR income, mixed EUR/USD portfolio
- Tax: Spanish IRPF

Current portfolio:
- GOOGL 21.5% -- largest holding, tech anchor
- IWDA 21.9% -- iShares MSCI World UCITS (core global equity)
- VT 9.9% -- Vanguard Total World (legacy hold, no new buys)
- MSFT 9.5% -- Microsoft
- IEAC 9.8% -- iShares Core Corp Bond UCITS
- AGGH 6.2% -- iShares Global Aggregate Bond EUR Hedged
- VNGA80 5.2% -- Vanguard LifeStrategy 80% Equity
- VWCE 7.9% target -- Vanguard FTSE All-World UCITS (being added)
- Cash 3% target

The portfolio is tech-heavy so tech, AI, semiconductor and macro news is especially relevant.
The investor holds significant USD assets so EUR/USD moves matter.
Bond allocation is being built up so rate decisions (ECB, Fed) are important.
Format your entire response as a clean, well-styled HTML email (no markdown, pure HTML)."""

def build_user_prompt():
    today = datetime.now().strftime("%A %d %B %Y")
    return f"""Today is {today}.

Search for today's most important stock market and macroeconomic news globally.
Focus on: US markets, European markets, tech sector, AI, semiconductors, oil/energy,
central banks (Fed + ECB), EUR/USD, and any geopolitical events moving markets.

Then produce a report titled Top 10 Market Facts You Need to Know Today.

Format as a complete HTML email:
1. Styled header with title and today's date
2. Short 1-sentence intro
3. Numbered list of 10 facts, each with emoji + bold headline, 2-3 sentences explanation,
   and one italic sentence starting with European investor angle:
4. Section titled European Investor Summary
5. Small disclaimer footer

Use clean inline CSS. White background, dark text, blue (#2E5090) headings."""

if __name__ == "__main__":
    print(f"[{datetime.now()}] Submitting batch request to Anthropic...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    batch = client.messages.batches.create(
        requests=[
            {
                "custom_id": "daily-market-report",
                "params": {
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "system": SYSTEM_PROMPT,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": build_user_prompt()}]
                }
            }
        ]
    )

    # Save batch ID so step 2 can retrieve it
    with open(BATCH_ID_FILE, "w") as f:
        f.write(batch.id)

    print(f"[{datetime.now()}] Batch submitted -- ID: {batch.id}")
    print(f"[{datetime.now()}] Step 1 done. Step 2 will run in 15 minutes.")
