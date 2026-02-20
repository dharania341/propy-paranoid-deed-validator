import json
import re
from datetime import datetime
from dateutil import parser as date_parser
from rapidfuzz import process
from openai import OpenAI

# -------------------------
# RAW INPUT (Exact string provided)
# -------------------------
RAW_DEED_TEXT = """
*** RECORDING REQ ***
Doc: DEED-TRUST-0042
County: S. Clara  |  State: CA
Date Signed: 2024-01-15
Date Recorded: 2024-01-10
Grantor:  T.E.S.L.A. Holdings LLC
Grantee:  John  &  Sarah  Connor
Amount: $1,250,000.00 (One Million Two Hundred Thousand Dollars)
APN: 992-001-XA
Status: PRELIMINARY
*** END ***
"""


# -------------------------
# LLM Extraction
# -------------------------
def extract_with_llm(raw_text: str) -> dict:
    """
    LLM is used ONLY for structured extraction.
    Not trusted for validation or financial logic.
    """

    client = OpenAI()

    prompt = f"""
Extract the following fields from the deed text.
Return JSON only.

Fields:
- doc_id
- county
- state
- date_signed
- date_recorded
- grantor
- grantee
- amount_numeric
- amount_text
- apn
- status

Text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    parsed = response.choices[0].message.content
    return json.loads(parsed)


# -------------------------
# County Normalization
# -------------------------
def load_counties():
    with open("counties.json") as f:
        return json.load(f)


def normalize_county(input_county: str, counties):
    names = [c["name"] for c in counties]
    best_match, score, _ = process.extractOne(input_county, names)

    if score < 70:
        raise ValueError(f"Unknown county: {input_county}")

    return best_match


# -------------------------
# Money Validation
# -------------------------
def text_amount_to_number(text_amount: str) -> int:
    """
    Minimal controlled conversion for demo.
    In production: use hardened number-word parser.
    """

    text_amount = text_amount.lower()

    total = 0

    if "one million" in text_amount:
        total += 1_000_000

    if "two hundred thousand" in text_amount:
        total += 200_000

    return total


# -------------------------
# Sanity Checks
# -------------------------
def validate_dates(date_signed: str, date_recorded: str):
    signed = date_parser.parse(date_signed)
    recorded = date_parser.parse(date_recorded)

    if recorded < signed:
        raise ValueError(
            f"INVALID DATE ORDER: Recorded {recorded.date()} "
            f"before Signed {signed.date()}"
        )


def validate_money(amount_numeric: str, amount_text: str):
    numeric_value = float(re.sub(r"[^\d.]", "", amount_numeric))
    text_value = text_amount_to_number(amount_text)

    if abs(numeric_value - text_value) > 1:
        raise ValueError(
            f"MONEY MISMATCH: Numeric={numeric_value} vs Text={text_value}"
        )


# -------------------------
# Closing Cost Calculation
# -------------------------
def calculate_tax(amount_numeric: str, tax_rate: float):
    numeric_value = float(re.sub(r"[^\d.]", "", amount_numeric))
    return numeric_value * tax_rate


# -------------------------
# Orchestration
# -------------------------
def process_deed():
    print("Extracting with LLM...")
    data = extract_with_llm(RAW_DEED_TEXT)

    print("Loading counties...")
    counties = load_counties()

    print("Normalizing county...")
    normalized_county = normalize_county(data["county"], counties)

    tax_rate = next(
        c["tax_rate"] for c in counties if c["name"] == normalized_county
    )

    print("Running sanity checks...")
    validate_dates(data["date_signed"], data["date_recorded"])
    validate_money(data["amount_numeric"], data["amount_text"])

    tax_due = calculate_tax(data["amount_numeric"], tax_rate)

    print("SUCCESS ✅")
    print(f"Normalized County: {normalized_county}")
    print(f"Tax Rate: {tax_rate}")
    print(f"Closing Tax Due: ${tax_due:,.2f}")


if __name__ == "__main__":
    process_deed()
