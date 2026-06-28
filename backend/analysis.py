import os
import json
import re
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schema import RealEstateOffer
from matcher import check_for_duplicate, generate_rejection_email
from evaluator import evaluate_asset


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_property_payload(raw_text: str) -> RealEstateOffer:
    """
    Sends raw email/PDF text to Gemini and returns a validated Pydantic object.
    Uses manual JSON parsing instead of response_schema to avoid Gemini SDK
    compatibility issues with Optional fields.
    """
    prompt = f"""
You are an elite real estate investment analyst working for Investa Real Estate GmbH.
Analyze the following raw text from an inbound property offer email and its attachments.

Extract all relevant information and return ONLY a valid JSON object.
No explanation, no markdown, no code blocks — raw JSON only.

Required JSON structure:
{{
  "offer_date": "YYYY-MM-DD or null",
  "subject_title": "main subject/headline of the offer",
  "asset_classification": "land_development or existing_investment",
  "address": {{
    "street": "street and number or null",
    "postal_code": "German PLZ or null",
    "city": "city name",
    "district": "district/neighborhood or null"
  }},
  "contact": {{
    "company": "broker company name or null",
    "email": "email or null",
    "phone": "phone or null"
  }},
  "plot_size_sqm": null,
  "planned_units": null,
  "building_permit_status": "description of permit status or null",
  "current_annual_net_rent_eur": null,
  "target_yield_percent": null,
  "total_existing_units": null,
  "key_tenants": [],
  "purchase_price_eur": null,
  "total_living_area_sqm": null
}}

Rules:
- asset_classification MUST be exactly "land_development" or "existing_investment"
- city is always required, never null
- All monetary values in EUR as plain numbers, no currency symbols
- plot_size_sqm, planned_units, purchase_price_eur etc. are numbers or null
- If a field is not mentioned in the text, use null

RAW PROPERTY TEXT:
{raw_text}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            text = response.text.strip()

            # Belt-and-suspenders: strip markdown fences if Gemini adds them
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            else:
                raise ValueError(f"No JSON found in LLM response: {text[:200]}")

            data = json.loads(text)
            return RealEstateOffer.model_validate(data)
        
        except Exception as e:
            if attempt < 2:
                print(f"Gemini attempt {attempt+1} failed: {e} — retrying in 5s...")
                time.sleep(5)
            else:
                raise
            
   
    
if __name__ == "__main__":
    import glob

    payload_files = glob.glob("*_raw_payload.txt")

    if not payload_files:
        print("No raw payload files found. Run pipeline.py first.")
        exit()

    print(f"Found {len(payload_files)} payload(s) to analyze.\n")

    for sample_file in payload_files:
        print("=" * 70)
        print(f"PROCESSING: {sample_file}")
        print("=" * 70)

        with open(sample_file, "r", encoding="utf-8") as f:
            raw_payload = f.read()

        try:
            structured_data = analyze_property_payload(raw_payload)
            print("\nEXTRACTED DATA:")
            print(structured_data.model_dump_json(indent=2))

            is_duplicate, matched_street = check_for_duplicate(
                incoming_street=structured_data.address.street,
                incoming_city=structured_data.address.city
            )

            if is_duplicate:
                print(f"\nDUPLICATE FOUND: {matched_street}")
                broker = structured_data.contact.company if structured_data.contact else "Makler"
                print(generate_rejection_email(broker, structured_data.subject_title, matched_street))
            else:
                print("\nClean asset — running evaluation...")
                report = evaluate_asset(structured_data)
                print(json.dumps(report, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"ERROR: {e}")

        print("\n" + "-" * 70 + "\n")