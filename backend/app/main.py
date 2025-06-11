import logging
import asyncio
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.scheduler import start_scheduler, shutdown_scheduler, schedule_initial_tasks
from app.api import tasks, logs, settings as api_settings
from app.api.tasks import router as tasks_router
from app.api.settings import router as settings_router
from app.utils.page_loader import PageLoader
from loguru import logger

# --- Logging Setup ---
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / "monitor.log"

# Define screenshots directory for static file serving
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"

# Configure file-based logging
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Get root logger and add our file handler
# Uvicorn will manage the console handler, so we don't set up our own.
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)


# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup...")
    
    # Initialize PageLoader
    await PageLoader.initialize()
    
    # Schedule initial tasks
    logger.info("Scheduling jobs...")
    schedule_initial_tasks(settings.tasks)
    
    # Start scheduler
    start_scheduler()
    logger.info("Scheduler started.")

    # Install playwright browsers
    logger.info("Installing Playwright browsers...")
    try:
        proc = await asyncio.create_subprocess_shell(
            'playwright install',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f"Playwright install failed: {stderr.decode()}")
        else:
            logger.info("Playwright browsers installed successfully.")
    except Exception as e:
        logger.error(f"Failed to run Playwright install: {e}")

    yield

    # Shutdown
    logger.info("Application shutdown...")
    await PageLoader.shutdown()
    shutdown_scheduler()
    logger.info("Scheduler shut down.")

app = FastAPI(
    title="Web Monitor",
    description="A general-purpose web content monitoring system.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, can be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Files ---
app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

# --- API Routers ---
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])

# --- Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Web Monitor is running."} 