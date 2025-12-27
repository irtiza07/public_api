"""Search recent credit-card and award-travel articles using OpenAI's web_search.

Summary:
- Uses the OpenAI Responses API with the built-in `web_search` tool to locate
    and summarize articles from a small allow-list of sites.
- Searches are restricted to these domains: frequentmiler.com, dannydealguru.com.
- The script requires the user to provide a lookback (number of days);
    it computes an earliest date and only considers articles published on or
    after that date.
- Topics covered include NLL (No Lifetime Language) offers, all-time-high
    sign-up bonuses, new credit-card rumors, transfer bonuses, airline news
    (Delta, Qatar, Turkish), and awards/promo flights.
- After the Responses API call the script prints a short estimated USD cost
    (derived from `resp.usage` token counts) to help track approximate spend.

Requirements:
- An up-to-date OpenAI Python SDK that provides `OpenAI()` and a `responses`
    client method.
- Set `OPENAI_API_KEY` in the environment before running.

Usage:
        export OPENAI_API_KEY="sk-..."
        python projects/openai-rewards-news-web-search/logic.py
"""
from __future__ import annotations

from openai import OpenAI

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv


load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)

ALLOWED_DOMAINS = [
    "frequentmiler.com",
    "dannydealguru.com",
]


def search_credit_card_articles(earliest_date: str) -> str:
    topics = [
        "No Lifetime Language (NLL) offers",
        "All Time High sign up bonuses",
        "New Credit Card Rumors",
        "Transfer Bonuses",
        "Delta Airlines",
        "Qatar Airways",
        "Turkish Airlines",
        "Awards and Promo Flights",
        "Delta SkyMiles",
        "Avianca LifeMiles",
        "Rakuten",
        "Alaska"
    ]

    prompt = (
        "Find recent articles on these topics limited to the domains: "
        + ", ".join(ALLOWED_DOMAINS)
        + ". Topics: "
        + ", ".join(topics)
        + ". Please summarize key points and include source URLs for notable claims."
    )
    
    prompt += f" Only consider articles published on or after {earliest_date}."

    print("Running Responses API web search for credit-card articles...")
    print(f"Lookback (earliest date): {earliest_date}")
    resp = client.responses.create(
        model="gpt-5",
        reasoning={"effort": "low"},
        tools=[
            {
                "type": "web_search",
                "filters": {"allowed_domains": ALLOWED_DOMAINS},
                "external_web_access": True,
            }
        ],
        input=prompt,
        include=["web_search_call.action.sources"],
        tool_choice="auto",
    )
    print("Responses API web search completed.")
    return getattr(resp, "output_text", "")


def main() -> None:
    while True:
        days = input("Enter how many days back to search (positive integer, e.g. 14): ").strip()
        if not (days.isdigit() and int(days) > 0):
            print("Invalid input. Enter a positive integer greater than zero (e.g. 14).")
            continue
        dnum = int(days)
        break

    earliest_date = (datetime.now(timezone.utc) - timedelta(days=dnum)).date().isoformat()
    earliest = earliest_date

    summary = search_credit_card_articles(earliest)
    print("--- Summary (Responses API) ---")
    print(summary)


if __name__ == "__main__":
    main()
