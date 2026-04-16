import anthropic
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDS_JSON    = os.environ["GOOGLE_CREDS_JSON"]
SHEET_ID             = "1cP2yKPwE059s8j2KdFY__zc_qxc3Gilh3vL1y-Haza8"

# ── READ PORTFOLIO FROM GOOGLE SHEETS ────────────────────────────────────────
def get_portfolio():
    print(f"[{datetime.now()}] Reading portfolio from Google Sheets...")

    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.get_worksheet(0)
    rows = worksheet.get_all_records()

    # Parse DEGIRO CSV format
    portfolio = []
    total_value = 0.0

    for row in rows:
        # Get value in EUR -- try different possible column names
        eur_value = 0.0
        for col in ["Value in EUR", "Waarde in EUR", "Valor en EUR"]:
            if col in row and row[col]:
                val = str(row[col]).replace(",", ".").replace("\"", "").strip()
                try:
                    eur_value = float(val)
                    break
                except:
                    pass

        name = str(row.get("Product", "")).strip()
        isin = str(row.get("Symbol/ISIN", "")).strip()

        if eur_value > 0 and name:
            portfolio.append({
                "name": name,
                "isin": isin,
                "value_eur": eur_value
            })
            total_value += eur_value

    # Build portfolio text with weights
    portfolio_text = ""
    for p in sorted(portfolio, key=lambda x: x["value_eur"], reverse=True):
        weight = (p["value_eur"] / total_value * 100) if total_value > 0 else 0
        portfolio_text += f"- {p['name']} ({p['isin']}): EUR {p['value_eur']:,.2f} ({weight:.1f}%)\n"

    portfolio_text += f"\nTotal portfolio value: EUR {total_value:,.2f}"

    print(f"[{datetime.now()}] Portfolio loaded -- {len(portfolio)} positions, total EUR {total_value:,.2f}")
    return portfolio_text

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a financial analyst assistant for a European investor based in Spain.

Investor profile:
- Age 40, works in tech (career income correlated with tech/NASDAQ)
- Platform: DEGIRO Spain (MiFID II applies -- cannot buy US-domiciled ETFs)
- Currency: EUR income, mixed EUR/USD portfolio
- Tax: Spanish IRPF

The portfolio is tech-heavy so tech, AI, semiconductor and macro news is especially relevant.
The investor holds significant USD assets so EUR/USD moves matter.
Bond allocation is being built up so rate decisions (ECB, Fed) are important.
Format your entire response as a clean, well-styled HTML email (no markdown, pure HTML)."""

# ── USER PROMPT ───────────────────────────────────────────────────────────────
def build_user_prompt(portfolio_text):
    today = datetime.now().strftime("%A %d %B %Y")
    return f"""Today is {today}.

My current DEGIRO portfolio is:
{portfolio_text}

Search for today's most important stock market and macroeconomic news globally.
Focus on: US markets, European markets, tech sector, AI, semiconductors, oil/energy,
central banks (Fed + ECB), EUR/USD, and any geopolitical events moving markets.

Then produce a report titled Top 5 Market Facts You Need to Know Today.

Format as a complete HTML email:
1. Styled header with title and today's date
2. Short 1-sentence intro
3. Numbered list of 5 facts, each with emoji + bold headline, 2-3 sentences explanation,
   and one italic sentence starting with European investor angle: explaining the specific
   impact on my portfolio holdings listed above
4. Section titled European Investor Summary referencing my actual holdings
5. Small disclaimer footer

Use clean inline CSS. White background, dark text, blue (#2E5090) headings."""

# ── SUBMIT BATCH ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting daily market report submission...")

    portfolio_text = get_portfolio()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"[{datetime.now()}] Submitting batch request to Anthropic...")

    batch = client.messages.batches.create(
        requests=[
            {
                "custom_id": "daily-market-report",
                "params": {
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 4000,
                    "system": SYSTEM_PROMPT,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": build_user_prompt(portfolio_text)}]
                }
            }
        ]
    )

    print(f"[{datetime.now()}] Batch submitted -- ID: {batch.id}")
    print(f"[{datetime.now()}] Step 1 done. Step 2 will run in 15 minutes.")
