import io
import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import extract_msg
import pdfplumber
from dotenv import load_dotenv

from database import init_db, save_offer, get_all_offers, save_known_property
from schema import RealEstateOffer
from analysis import analyze_property_payload
from matcher import check_for_duplicate, generate_rejection_email
from evaluator import evaluate_asset
from image_analyzer import analyze_property_images

load_dotenv()
app = FastAPI(title="Investa Pipeline API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/offers")
def list_offers():
    return get_all_offers()

@app.post("/upload")
async def upload_offer(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "upload"
    
    # Extract text from .msg or .pdf
    raw_text = ""
    pdf_bytes_for_vision = None
    try:
        if filename.lower().endswith(".msg"):
            msg = extract_msg.openMsg(io.BytesIO(content))
            raw_text = f"EMAIL SUBJECT: {msg.subject}\nFROM: {msg.sender}\nBODY:\n{msg.body or ''}\n"
            for att in msg.attachments:
                if att.longFilename and att.longFilename.lower().endswith(".pdf"):
                    pdf_bytes_for_vision = att.data  # save raw bytes for vision
                    pdf_bytes = io.BytesIO(att.data)
                    with pdfplumber.open(pdf_bytes) as pdf:
                        for page in pdf.pages:
                            t = page.extract_text()
                            if t:
                                raw_text += f"\n--- ATTACHMENT: {att.longFilename} ---\n{t}"
        elif filename.lower().endswith(".pdf"):
            pdf_bytes_for_vision = content  # save for vision
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        raw_text += t + "\n"
        else:
            raw_text = content.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    # LLM extraction
    structured: RealEstateOffer = analyze_property_payload(raw_text)
    extracted = structured.model_dump()

    # Duplicate check
    is_dup, matched = check_for_duplicate(structured.address.street, structured.address.city)
    rejection_email = None

    if is_dup:
        broker = structured.contact.company if structured.contact else "Makler"
        rejection_email = generate_rejection_email(broker, structured.subject_title, matched)
        save_offer(filename, structured.subject_title, extracted, {}, None, {}, "", True, rejection_email)
        return {"status": "duplicate", "matched": matched, "rejection_email": rejection_email, "extracted": extracted}

    # Enrich + score
    # Enrich + score
    # Image analysis (4.4c optional but implemented)
    image_insights = {}
    if pdf_bytes_for_vision:
        try:
            image_insights = analyze_property_images(pdf_bytes_for_vision)
        except Exception as e:
            image_insights = {"error": str(e)}

    # Enrich + score
    eval_result = evaluate_asset(structured, image_insights)
    
    # Store drivers/risks inside score_breakdown for easy retrieval
    full_breakdown = {
        **(eval_result.get("score_breakdown") or {}),
        "top_drivers": eval_result.get("top_drivers", []),
        "risks": eval_result.get("risks", []),
        "recommendation": eval_result.get("recommendation", "review"),
    }

    save_offer(
        filename,
        structured.subject_title,
        extracted,
        eval_result.get("enrichment_used", {}),
        eval_result["overall_score"],
        full_breakdown,
        eval_result.get("score_reasoning", ""),
        False
    )
    save_known_property(structured.address.street or "unknown", structured.address.city)

    return {
        "status": "analyzed",
        "extracted": extracted,
        "score": eval_result["overall_score"],
        "score_breakdown": full_breakdown,
        "top_drivers": eval_result.get("top_drivers", []),
        "risks": eval_result.get("risks", []),
        "score_reasoning": eval_result.get("score_reasoning", ""),
    }