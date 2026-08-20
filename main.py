import os
import subprocess
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from backend.database.sqlite import db
from backend.repositories.file_repository import file_repo
from backend.utils.logger import logger

# Import all route routers
from backend.routes.health import router as health_router
from backend.routes.stats import router as stats_router
from backend.routes.history import router as history_router
from backend.routes.settings import router as settings_router
from backend.routes.mining import router as mining_router
from backend.routes.validation import router as validation_router
from backend.routes.downloads import router as downloads_router
from backend.routes.logs import router as logs_router
from backend.routes.locations import router as locations_router
from backend.routes.keywords import router as keywords_router

app = FastAPI(
    title="Enterprise Google Maps Lead Harvester & Mining System",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup lifecycle initialization
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing folder structure and database schema...")
    file_repo.ensure_directories()
    db.initialize_db()
    
    # Check and install Playwright browser dependencies automatically
    try:
        logger.info("Verifying Playwright browser requirements...")
        # Run playwright install chromium in subprocess to avoid blocking event loop
        subprocess.Popen(
            ["playwright", "install", "chromium"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info("Playwright chromium browser install scheduled successfully.")
    except Exception as e:
        logger.warning(f"Failed to auto-install Playwright chromium: {e}. Ensure playwright is installed manually.")

# Serve static frontend folder assets
# Map standard static directories
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
if os.path.exists("frontend/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Route controllers registration
app.include_router(health_router)
app.include_router(stats_router)
app.include_router(history_router)
app.include_router(settings_router)
app.include_router(mining_router)
app.include_router(validation_router)
app.include_router(downloads_router)
app.include_router(logs_router)
app.include_router(locations_router)
app.include_router(keywords_router)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves primary SPA frontend index file."""
    index_path = os.path.join("frontend", "templates", "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse(
            content="<h1>Frontend file index.html is missing. Ensure the directory path frontend/templates/index.html is set up.</h1>",
            status_code=404
        )
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import os

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
