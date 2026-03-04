import anthropic
import sendgrid
from sendgrid.helpers.mail import Mail
import os
import time
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SENDGRID_API_KEY  = os.environ["SENDGRID_API_KEY"]
SENDER_EMAIL      = "roelspee@protonmail.com"
RECIPIENT_EMAIL   = "roelleonard@gmail.com"

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a financial analyst assistant for a European investor based in Spain.

Investor profile:
- Age 40, works in tech (career income correlated with tech/NASDAQ)
- Platform: DEGIRO Spain (MiFID II applies — cannot buy US-domiciled ETFs)
- Currency: EUR income, mixed EUR/USD portfolio
- Tax: Spanish IRPF

Current portfolio:
- GOOGL 21.5% — largest holding, tech anchor
- IWDA 21.9% — iShares MSCI World UCITS (core global equity)
- VT 9.9% — Vanguard Total World (legacy hold, no new buys)
- MSFT 9.5% — Microsoft
- IEAC 9.8% — iShares Core Corp Bond UCITS
- AGGH 6.2% — iShares Global Aggregate Bond EUR Hedged
- VNGA80 5.2% — Vanguard LifeStrategy 80% Equity
- VWCE ~7.9% target — Vanguard FTSE All-World UCITS (being added)
- Cash ~3% target

The portfolio is tech-heavy so tech, AI, semiconductor and macro news is especially relevant.
The investor holds significant USD assets so EUR/USD moves matter.
Bond allocation is being built up so rate decisions (ECB, Fed) are important.

Always search the web for today's latest financial news before producing the report.
Format your entire response as a clean, well-styled HTML email (no markdown, pure HTML)."""

# ── USER PROMPT ───────────────────────────────────────────────────────────────
def build_user_prompt():
    today = datetime.now().strftime("%A %d %B %Y")
    return f"""Today is {today}.

Search for today's most important stock market and macroeconomic news globally.
Focus on: US markets, European markets, tech sector, AI, semiconductors, oil/energy, 
central banks (Fed + ECB), EUR/USD, and any geopolitical events moving markets.

Then produce a report titled 'Top 10 Market Facts You Need to Know Today'.

Format the report as a complete HTML email with this structure:

1. A styled header with the title and today's date
2. A short 1-sentence intro
3. Numbered list of 10 facts, each with:
   - A relevant emoji + bold headline
   - 2-3 sentences of clear explanation
   - One sentence in italic starting with '🇪🇺 European investor angle:' explaining the specific impact on a European tech investor with the portfolio described
4. A final section titled 'European Investor Summary' with a short paragraph tying it together
5. A small footer with a disclaimer that this is not financial advice

Use clean inline CSS styling. Make it readable and professional.
Use a white background, dark text, with subtle blue (#2E5090) accent colors for headings."""

# ── CALL ANTHROPIC WITH WEB SEARCH ───────────────────────────────────────────
def generate_report():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"[{datetime.now()}] Calling Anthropic API with web search...")

    messages = [{"role": "user", "content": build_user_prompt()}]
    full_response = ""

    # Agentic loop — handles tool use (web search) automatically
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        # Collect any text from this response
        for block in response.content:
            if hasattr(block, "text"):
                full_response += block.text

        # If Claude wants to use a tool, let it — add response + dummy tool result to messages
        if response.stop_reason == "tool_use":
            # Add assistant's response to history
            messages.append({"role": "assistant", "content": response.content})

            # Add tool results (the web search happens server-side, we just continue)
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed."
                    })

            messages.append({"role": "user", "content": tool_results})
            print(f"[{datetime.now()}] Web search performed, continuing...")
            time.sleep(1)

        else:
            # stop_reason == "end_turn" — we're done
            break

    print(f"[{datetime.now()}] Report generated ({len(full_response)} chars)")
    return full_response

# ── SEND EMAIL VIA SENDGRID ───────────────────────────────────────────────────
def send_email(html_content):
    today = datetime.now().strftime("%d %b %Y")
    subject = f"📈 Daily Market Report — {today}"

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=subject,
        html_content=html_content
    )

    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"[{datetime.now()}] Email sent — status {response.status_code}")

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting daily market report...")
    try:
        report_html = generate_report()
        send_email(report_html)
        print(f"[{datetime.now()}] Done!")
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        raise
