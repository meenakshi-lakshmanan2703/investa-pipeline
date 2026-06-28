````markdown
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
  - OpenStreetMap
  - Wikidata
  - Mietspiegel
  - Google Search
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
(OSM + Wikidata + Mietspiegel + Search)
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
````

---

## Tech Stack

### Backend

* Python
* FastAPI
* Gemini 2.5 Flash
* SQLite

### Frontend

* HTML / CSS / Vanilla JavaScript
* Chart.js
* nginx

### Infrastructure

* Docker
* Docker Compose

---

## Project Structure

```bash
investa-real-estate/
│
├── backend/
│   ├── api.py
│   ├── services/
│   ├── models/
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── data/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start (Docker)

### 1. Clone Repository

```bash
git clone <repository-url>
cd investa-real-estate
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Add your API key:

```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Start Application

```bash
docker compose up --build
```

---

Access the application:

* Frontend: http://localhost:3000
* Backend API: http://localhost:8000
* API Docs: http://localhost:8000/docs

---

## Quick Start (Without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### Frontend

Open:

```bash
frontend/index.html
```

in your browser.

---

## API Endpoints

| Method | Endpoint  | Description                       |
| ------ | --------- | --------------------------------- |
| POST   | `/upload` | Upload `.msg` or `.pdf` files     |
| GET    | `/offers` | Retrieve processed offers         |
| GET    | `/docs`   | Interactive Swagger documentation |

---

## Scoring Logic

Each offer is evaluated across multiple investment dimensions:

* Location attractiveness
* Rental potential
* Market valuation
* Population growth
* Property condition
* Yield potential

Final score:

```text
0 = Very Poor Investment Opportunity
10 = Excellent Investment Opportunity
```

Each score includes AI-generated reasoning in German for explainability and auditability.

---

## Data Sources

The enrichment pipeline uses:

* **OpenStreetMap Nominatim** — Geocoding & address normalization
* **Wikidata SPARQL** — Population and regional metadata
* **Mietspiegel 2024** — Public rent benchmarks
* **Gemini Search Grounding** — Live market information

---

## Environment Variables

Required configuration:

```env
GEMINI_API_KEY=
DATABASE_PATH=
```

See `.env.example` for the complete configuration.

---

## Future Improvements

* Broker email inbox integration
* Vector search for similar offers
* Historical investment analytics
* Advanced portfolio recommendations
* Multi-user authentication

---

## License

This project is intended for educational and demonstration purposes.

```
```
