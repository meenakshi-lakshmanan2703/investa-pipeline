import io
import base64
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_images_from_pdf_bytes(pdf_bytes: bytes) -> list:
    """Extract images from PDF as base64 strings using PyMuPDF."""
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(min(3, len(doc))):  # first 3 pages only
            page = doc[page_num]
            # Render page as image (captures maps, floor plans, visual layouts)
            mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom for quality
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            images.append(b64)
        doc.close()
    except Exception as e:
        print(f"Image extraction error: {e}")
    return images

def analyze_property_images(pdf_bytes: bytes) -> dict:
    """
    Sends PDF page renders to Gemini Vision to extract
    visual information not captured by text extraction.
    """
    images = extract_images_from_pdf_bytes(pdf_bytes)
    if not images:
        return {"image_analysis": "No images extracted", "visual_insights": []}

    # Send first 2 pages to Gemini Vision
    contents = []
    for b64 in images[:2]:
        contents.append(
            types.Part.from_bytes(
                data=base64.b64decode(b64),
                mime_type="image/png"
            )
        )
    contents.append("""
Analyze these property exposé pages and extract:
1. Property condition visible in photos (new build, renovated, needs work?)
2. Location indicators visible (urban density, green spaces, transport nearby?)
3. Floor plan observations if visible (layout quality, unit sizes)
4. Any maps showing the property location or surroundings
5. Key visual selling points or red flags

Return a structured JSON with:
{
  "property_condition": "description",
  "location_visual_assessment": "description", 
  "floor_plan_notes": "description or null",
  "visual_highlights": ["point1", "point2"],
  "visual_risks": ["risk1"] or [],
  "image_quality_note": "what was visible vs not"
}
""")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        import json
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        result = json.loads(text)
        result["pages_analyzed"] = len(images)
        return result
    except Exception as e:
        return {
            "image_analysis_error": str(e),
            "visual_insights": [],
            "pages_analyzed": len(images)
        }