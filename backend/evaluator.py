import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from enrichment import enrich_property

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def evaluate_asset(asset_data, image_insights: dict = {}) -> dict:
    """
    Produces a transparent, evidence-based investment scorecard for a property.

    Design note: enrichment is called here (not in api.py) so that the evaluator
    is self-contained. The caller (api.py) is responsible for only calling this
    function on non-duplicate assets — enrichment is intentionally not guarded
    here to keep the function's responsibility narrow.
    """
    city = asset_data.address.city or ""
    street = asset_data.address.street or ""

    enrichment = enrich_property(street, city, asset_data.asset_classification)
    asset_json = asset_data.model_dump_json(indent=2)
    enrichment_json = json.dumps(enrichment, indent=2, ensure_ascii=False)

    # Build optional image analysis section
    image_section = ""
    if image_insights and not image_insights.get("error"):
        image_section = f"""

VISUAL ANALYSIS FROM PDF IMAGES (Gemini Vision):
{json.dumps(image_insights, indent=2, ensure_ascii=False)}

Use visual observations about property condition and location when scoring.
"""

    prompt = f"""
You are a senior real estate investment analyst at Investa Real Estate GmbH in Germany.

You receive a structured property offer and real external market data.
Your job is to produce a transparent, evidence-based investment scorecard.

PROPERTY OFFER:
{asset_json}

EXTERNAL MARKET DATA (live API sources):
{enrichment_json}

SCORING INSTRUCTIONS:
- Score 0-10 overall. Be precise (e.g. 7.3, not just 7).
- For existing_investment assets: weight yield heavily (is it above 5%?),
  consider tenant quality, location, price per sqm vs market rent
- For land_development assets: weight permit status heavily (granted permit =
  low risk, new planning = high risk), consider location demand and unit count
- Base ALL reasoning on the actual data provided above, not on assumptions
- If data is missing, say so in the risks
{image_section}
Return ONLY valid JSON in this exact structure:
{{
  "overall_score": <float>,
  "score_breakdown": {{
    "location_score": <float 0-10>,
    "financial_score": <float 0-10>,
    "development_risk_score": <float 0-10>
  }},
  "top_drivers": [
    "<specific reason with numbers from the data>",
    "<specific reason with numbers from the data>",
    "<specific reason with numbers from the data>"
  ],
  "risks": [
    "<specific risk based on actual data>",
    "<specific risk based on actual data>"
  ],
  "score_reasoning": "<3 sentences in German summarizing the investment case>",
  "recommendation": "<one of: invest | review | pass>"
}}
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            result = json.loads(response.text)
            break
        except Exception as e:
            if attempt < 2:
                print(f"Gemini attempt {attempt + 1} failed: {e} — retrying in 5s...")
                time.sleep(5)
            else:
                raise

    result["enrichment_used"] = enrichment
    return result