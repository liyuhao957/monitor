import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

LOG_FILE_PATH = Path(__file__).parent.parent.parent.parent / "logs" / "monitor.log"

MAX_LOG_LINES = 500

@router.get("/", response_class=PlainTextResponse)
async def get_logs():
    """
    Retrieves the last N lines of the log file.
    """
    if not LOG_FILE_PATH.is_file():
        # To avoid showing an error on a fresh start, return a friendly message.
        return "Log file not yet created. Please wait for some activity."

    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            # Read all lines and return the last MAX_LOG_LINES in reverse order
            lines = f.readlines()
            last_lines = lines[-MAX_LOG_LINES:]
            last_lines.reverse()
            return "".join(last_lines)
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {e}") 