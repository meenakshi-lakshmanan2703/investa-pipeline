import os
import requests
import time
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_nominatim_location(address: str, city: str) -> Dict:
    """Free OSM geocoding — no API key needed."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{address}, {city}, Germany", "format": "json", "limit": 1}
        headers = {"User-Agent": "InvestaRealEstatePipeline/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        data = r.json()
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "display_name": data[0]["display_name"],
            }
    except Exception:
        pass
    return {}


# Static fallback populations for common German cities and municipalities.
# Used when Wikidata SPARQL returns no result (e.g. smaller towns, municipalities
# that are not classified as Q515/city in Wikidata).
# Source: Destatis / Statistisches Bundesamt 2023.
POPULATION_FALLBACK = {
    "berlin": 3_677_000,
    "hamburg": 1_853_000,
    "münchen": 1_488_000,
    "frankfurt": 773_000,
    "köln": 1_084_000,
    "düsseldorf": 648_000,
    "stuttgart": 634_000,
    "leipzig": 628_000,
    "dortmund": 588_000,
    "essen": 582_000,
    "bremen": 577_000,
    "dresden": 563_000,
    "hannover": 535_000,
    "nürnberg": 523_000,
    "bernau": 41_000,
}


def _try_wikidata(city: str) -> Dict:
    """
    Attempts to fetch population from Wikidata SPARQL.
    Uses VALUES to match multiple entity types (Q515=city, Q262166=Kreisstadt,
    Q253019=Gemeinde, Q42744322=Großstadt) so smaller municipalities are found.
    Returns empty dict on any failure — caller handles fallback.
    """
    try:
        query = f"""
        SELECT ?pop WHERE {{
          VALUES ?type {{ wd:Q515 wd:Q262166 wd:Q253019 wd:Q42744322 }}
          ?city wdt:P31 ?type ;
                rdfs:label "{city}"@de ;
                wdt:P1082 ?pop .
        }} LIMIT 1
        """
        r = requests.get(
            "https://query.wikidata.org/sparql",
            params={"query": query, "format": "json"},
            headers={"User-Agent": "InvestaRealEstatePipeline/1.0"},
            timeout=10,
        )
        bindings = r.json().get("results", {}).get("bindings", [])
        if bindings:
            return {
                "population": int(bindings[0]["pop"]["value"]),
                "source": "wikidata",
            }
    except Exception:
        pass
    return {}


def get_population_data(city: str) -> Dict:
    """
    Returns population data for a city.
    Priority: Wikidata live → static fallback → unavailable.
    """
    result = _try_wikidata(city)
    if result:
        return result

    # Static fallback — covers cities where Wikidata SPARQL returns nothing
    key = city.lower().strip()
    for k, v in POPULATION_FALLBACK.items():
        if k in key or key in k:
            return {"population": v, "source": "static_fallback"}

    return {"population": None, "source": "unavailable"}


# Static rent index — sourced from German Mietspiegel 2024 public data.
# Deliberate design choice: a static dict avoids rate limits and API costs
# for a baseline that changes only annually. Live data supplements this
# via Gemini Search grounding below.
MIETSPIEGEL_2024 = {
    "berlin":    {"avg_rent_sqm": 13.80, "rent_trend": "+4.2% YoY", "source": "Berliner Mietspiegel 2024"},
    "hamburg":   {"avg_rent_sqm": 13.20, "rent_trend": "+3.8% YoY", "source": "Hamburger Mietspiegel 2023"},
    "münchen":   {"avg_rent_sqm": 18.50, "rent_trend": "+2.9% YoY", "source": "Münchner Mietspiegel 2024"},
    "frankfurt": {"avg_rent_sqm": 14.10, "rent_trend": "+3.1% YoY", "source": "Frankfurter Mietspiegel 2024"},
    "köln":      {"avg_rent_sqm": 11.90, "rent_trend": "+3.5% YoY", "source": "Kölner Mietspiegel 2023"},
    "default":   {"avg_rent_sqm": 10.50, "rent_trend": "unknown",   "source": "German national average 2024"},
}


def get_rent_data(city: str) -> Dict:
    key = city.lower().strip()
    for k, v in MIETSPIEGEL_2024.items():
        if k in key or key in k:
            return v
    return MIETSPIEGEL_2024["default"]


def web_search_enrichment(city: str, asset_type: str) -> dict:
    """
    Uses Gemini with Google Search grounding to fetch LIVE market data.
    Gives the LLM real internet access at evaluation time — this is the
    primary source of up-to-date infrastructure, economic, and market data.
    """
    try:
        search_prompt = f"""
Search for current real estate market information about {city}, Germany.
Find and summarize:
1. Current average rent per sqm (Mietspiegel) in {city}
2. Population trend (growing or shrinking?)
3. Any major infrastructure projects planned (new transit, development zones)
4. Regional economic outlook (unemployment, GDP trend)
5. Real estate market trend (prices rising or falling in 2024-2025?)

For asset type: {asset_type}

Return a concise factual summary with numbers where available.
"""
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=search_prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1,
                    ),
                )
                return {
                    "web_search_summary": response.text,
                    "source": "Gemini Google Search grounding (live)",
                }
            except Exception as e:
                if attempt < 2:
                    print(f"Web search attempt {attempt + 1} failed: {e} — retrying in 5s...")
                    time.sleep(5)
                else:
                    return {
                        "web_search_summary": f"Unavailable after retries: {e}",
                        "source": "fallback",
                    }
    except Exception as e:
        return {"web_search_summary": f"Web search unavailable: {e}", "source": "fallback"}


ENRICHMENT_DEFAULTS = {
    "geocoding": {"lat": None, "lon": None, "display_name": None},
    "population": {"population": None, "source": "unavailable"},
    "rent_market": {"avg_rent_sqm": None, "rent_trend": None, "source": "unavailable"},
    "live_market_research": {"web_search_summary": None, "source": "unavailable"},
}

def enrich_property(address: str, city: str, asset_type: str = "unknown") -> Dict[str, Any]:
    result = {}
    result["geocoding"] = get_nominatim_location(address or "", city) or ENRICHMENT_DEFAULTS["geocoding"]
    result["population"] = get_population_data(city) or ENRICHMENT_DEFAULTS["population"]
    result["rent_market"] = get_rent_data(city) or ENRICHMENT_DEFAULTS["rent_market"]
    result["live_market_research"] = web_search_enrichment(city, asset_type) or ENRICHMENT_DEFAULTS["live_market_research"]
    result["macro_indicators"] = {
        "city": city,
        "data_sources": [
            "OpenStreetMap Nominatim (geocoding)",
            "Wikidata SPARQL (demographics)",
            "Mietspiegel 2024 public data",
            "Gemini Google Search grounding (live market data)"
        ]
    }
    return result