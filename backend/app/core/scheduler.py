import logging
import re
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.core.config import Task
from app.services.monitor import run_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def _parse_frequency_to_seconds(freq: str) -> int:
    """
    Parses a frequency string (e.g., '10m', '1h', '30s') into seconds.
    """
    match = re.match(r"(\d+)([smhd])", freq.lower())
    if not match:
        raise ValueError(f"Invalid frequency format: {freq}")

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return value
    if unit == 'm':
        return value * 60
    if unit == 'h':
        return value * 3600
    if unit == 'd':
        return value * 86400
    
    raise ValueError(f"Unknown frequency unit: {unit}")

def schedule_initial_tasks(tasks: list[Task]):
    logger.info("Scheduling initial tasks...")
    for task in tasks:
        schedule_task(task)
    logger.info("Initial tasks scheduled.")

def schedule_task(task: Task):
    if not task.enabled:
        logger.info(f"Task '{task.name}' is disabled, skipping.")
        if scheduler.get_job(task.name):
            scheduler.remove_job(task.name)
        return

    try:
        if scheduler.get_job(task.name):
            scheduler.remove_job(task.name)

        seconds = _parse_frequency_to_seconds(task.frequency)
        scheduler.add_job(
            run_task,
            trigger=IntervalTrigger(seconds=seconds),
            args=[task],
            id=task.name,
            name=task.name,
            misfire_grace_time=60,
            coalesce=True,
            max_instances=3,
        )
        logger.info(f"Scheduled task '{task.name}' to run every {task.frequency}.")
    except Exception as e:
        logger.error(f"Error scheduling task '{task.name}': {e}")

def remove_job(task_name: str):
    if scheduler.get_job(task_name):
        scheduler.remove_job(task_name)
        logger.info(f"Removed job '{task_name}' from scheduler.")

def start_scheduler():
    scheduler.start()
    logger.info("Scheduler started.")

def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down.") 