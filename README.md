# 🏢 Investa Real Estate — KI-Angebotspipeline

AI-powered pipeline for automatically processing, analyzing, and scoring inbound real estate offers from brokers.

---

## Overview

Investa Real Estate helps automate the evaluation of incoming property offers by converting unstructured broker emails and documents into structured, enriched, and scored investment opportunities.

The system reduces manual screening effort by combining **LLM-based extraction**, **data enrichment**, **duplicate detection**, and **transparent AI scoring**.

---

## Features

- 📩 Upload `.msg` email files and `.pdf` attachments via web interface
- 🤖 Extract structured offer data using **Gemini 2.5 Flash**
- 🔍 Detect duplicate properties using fuzzy address matching
- 🌍 Enrich offers with external market and location data:
  - OpenStreetMap Nominatim
  - Wikidata SPARQL
  - Mietspiegel 2024
  - Gemini Google Search grounding (live)
- 📊 Score each offer from **0–10**
- 📝 Generate explainable scoring with transparent German reasoning
- 📈 Visual dashboard with charts and offer cards

---

## System Architecture

```text
.msg / .pdf Upload
       │
       ▼
    FastAPI API
       │
       ▼
Gemini 2.5 Flash
(Data Extraction)
       │
       ▼
Duplicate Detection
    (SQLite)
       │
       ▼
Data Enrichment
(OSM + Wikidata + Mietspiegel + Gemini Search)
       │
       ▼
Gemini Scoring
(Score + Reasoning)
       │
       ▼
 SQLite Storage
       │
       ▼
 Dashboard UI
```

---

## Tech Stack

### Backend
- Python / FastAPI
- Gemini 2.5 Flash (extraction + scoring + live search grounding)
- SQLite

### Frontend
- HTML / CSS / Vanilla JavaScript
- Chart.js
- nginx

### Infrastructure
- Docker / Docker Compose

---

## Project Structure

```
investa-pipeline/
│
├── backend/
│   ├── api.py              # FastAPI app, upload endpoint
│   ├── analysis.py         # LLM extraction via Gemini
│   ├── evaluator.py        # Scoring logic
│   ├── enrichment.py       # OSM, Wikidata, Mietspiegel, Search
│   ├── matcher.py          # Fuzzy duplicate detection
│   ├── image_analyzer.py   # PDF image analysis via Gemini Vision
│   ├── database.py         # SQLite persistence
│   ├── schema.py           # Pydantic data models
│   ├── pipeline.py         # Standalone .msg batch processor
│   └── requirements.txt
│
├── frontend/
│   └── index.html          # Single-page dashboard
│
├── data/                   # SQLite DB (mounted as Docker volume)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start (Docker)

### 1. Clone Repository

```bash
git clone <repository-url>
cd investa-pipeline
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your key:

```env
GEMINI_API_KEY=your_api_key_here
DB_PATH=/app/data/investa.db
```

### 3. Start Application

```bash
docker compose up --build
```

Access the application:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Quick Start (Without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### Frontend

Open `frontend/index.html` directly in your browser.

> **Note:** The frontend calls `http://127.0.0.1:8000` directly from the browser.
> This is correct for local development — the API URL is not proxied through nginx.

---

## API Endpoints

| Method | Endpoint  | Description                       |
|--------|-----------|-----------------------------------|
| POST   | `/upload` | Upload `.msg` or `.pdf` files     |
| GET    | `/offers` | Retrieve all processed offers     |
| GET    | `/docs`   | Interactive Swagger documentation |

> **Performance note:** The `/upload` endpoint triggers Gemini extraction,
> external API enrichment, and scoring — expect ~30–60s per upload.
> This is a known prototype trade-off; production would use a background task queue.

---

## Scoring Logic

Each offer is evaluated across three dimensions:

| Dimension | Description |
|---|---|
| **Location Score** | Geocoding, demographics, infrastructure, macro/micro factors |
| **Financial Score** | Yield, price per sqm vs market rent, purchase price |
| **Development Risk Score** | Permit status, planning risk, unit count feasibility |

Final score: `0 = Very Poor` → `10 = Excellent Investment Opportunity`

Each score includes AI-generated reasoning in German for explainability and auditability.

---

## Data Sources

| Source | What it provides |
|---|---|
| OpenStreetMap Nominatim | Geocoding & address normalization |
| Wikidata SPARQL | Population and regional metadata |
| Mietspiegel 2024 | Public rent benchmarks (static, updated annually) |
| Gemini Search Grounding | Live market data, infrastructure news, economic trends |

---

## Environment Variables

```env
GEMINI_API_KEY=      # Required — Gemini API key from Google AI Studio
DB_PATH=             # SQLite path inside container: /app/data/investa.db
```

See `.env.example` for the template.

---

## Design Decisions & Trade-offs

- **SQLite over PostgreSQL:** Right-sized for a prototype. Docker volume ensures persistence. Would migrate to Postgres for multi-user production.
- **Static Mietspiegel dict:** Avoids rate limits and API costs for data that changes once per year. Gemini Search grounding provides live supplement.
- **Synchronous upload processing:** All enrichment happens in one request. Trade-off: simpler stack vs. ~30–60s response time. Production would use Celery/background tasks.
- **Single HTML file frontend:** Zero build tooling, instant iteration. Would move to React for production.
- **Seed data in `init_db()`:** Pre-populates known properties for demo purposes. Clearly separated from user-submitted data via `source='manual'` vs `source='auto'`.

---

## Future Improvements

- Background task queue (Celery / FastAPI BackgroundTasks) for async processing
- Broker email inbox integration (IMAP polling)
- Vector similarity search for semantically similar offers
- Historical investment analytics and portfolio view
- Multi-user authentication

---

## License

This project is intended for educational and demonstration purposes.
