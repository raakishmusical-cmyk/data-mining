# Enterprise Google Maps Lead Harvester & Mining System

A production-ready, highly concurrent, and modular Lead Harvester application built from scratch to mine and validate corporate business information from Google Maps and official websites with extreme accuracy.

---

## 📌 Architecture & Design

The application follows a layered clean architecture:
- **Presentation Layer**: Pure Vanilla HTML5, CSS3, and JavaScript SPA (no framework overhead). High visual quality with responsive layouts, dark mode aesthetics, glassmorphism, and live logs terminal.
- **API Layer (FastAPI)**: Lightweight asynchronous REST API controllers and WebSocket adapters.
- **Service Layer**: Decoupled modules managing business logic for mining, validation, cache, and history cataloging.
- **Worker Layer**: Independent queue-driven workers managing scraper concurrency (Playwright browsers) and background website scraping pools (`aiohttp`).
- **Database Layer (SQLite)**: Persists session settings, file paths history, cache, checkpoints, and jobs.

---

## 🛠️ Features

- **Multi-District & Keyword Queues**: Complete sequentially district by district, keyword by keyword.
- **Concurrent Web Crawler**: Scrapes official sites (Home, Contact, About pages) to parse emails and social media handles.
- **Duplicate Prevention Engine**: Real-time filtering based on Place ID, Phone, Domain, or Name + City.
- **Automatic Industry/Tag Classifier**: Local fuzzy-matching classification using `RapidFuzz` and custom mappings, falling back to AI only when required.
- **Validation Board**: Upload Excel/CSV, scan duplicate groups, highlight (`marked.xlsx`), prune duplicate records (`clean.xlsx`), update classification fields, and download the active working package.
- **Recent Files Catalog**: Survival history logs across application and browser reloads.
- **Periodic Checkpoint System**: Auto-saves queue state and statistics for resume recovery on crash.

---

## 📂 Project Structure

```text
Data-Mining/
├── backend/
│   ├── database/        # SQLite connection pooling & schemas
│   ├── models/          # Pydantic data schemas
│   ├── repositories/    # File and DB repository logic
│   ├── routes/          # FastAPI REST and WebSocket controllers
│   ├── services/        # Service abstractions
│   ├── utils/           # Normalizers, validators, parsers
│   └── workers/         # Playwright & site crawling workers
├── frontend/
│   ├── css/             # Styled premium stylesheet
│   ├── js/              # SPA controllers, WS, mining, validation
│   └── templates/       # HTML markup templates
├── Output/              # Production output package store
├── main.py              # Server bootstrap and startup hook
├── requirements.txt     # Locked dependencies
└── README.md            # System documentation
```

---

## ⚙️ Installation & Usage

### 1. Set Up Environment
Ensure you have Python 3.12+ installed.
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 2. Start Application
```bash
python main.py
```
Open your web browser and navigate to `http://127.0.0.1:8000`.

---

## 📡 REST API Documentation

- `GET /health`: Server status readiness.
- `GET /statistics`: Current active mining statistics.
- `GET /history`: Registered file history packages list.
- `GET /settings` / `POST /settings`: Load and save settings values.
- `POST /mining/start` / `pause` / `resume` / `stop`: Control scraper task states.
- `POST /validation/upload`: Upload spreadsheet for validation.
- `POST /validation/find-duplicates`: Perform duplicate clusters checks.
- `POST /validation/mark`: Generate yellow marked spreadsheet.
- `POST /validation/delete`: Prune duplicates and create `clean.xlsx`.
- `POST /validation/fix-classification`: Fix industry classifications in-place.
- `GET /download/{download_id}`: Stream secure file package downloads.
- `DELETE /history/{file_id}`: Secure deletion from database and filesystem.
