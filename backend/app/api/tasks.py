import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from app.core.config import Task, settings, save_config, get_config_path
from app.core.scheduler import schedule_task, remove_job

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[Task])
async def get_all_tasks():
    """Retrieve all monitoring tasks."""
    return settings.tasks

@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(task: Task):
    """Create a new monitoring task."""
    if any(t.name == task.name for t in settings.tasks):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task with name '{task.name}' already exists."
        )
    
    settings.tasks.append(task)
    try:
        save_config(settings, get_config_path())
        schedule_task(task)
        logger.info(f"Successfully created and scheduled task: {task.name}")
    except Exception as e:
        logger.error(f"Failed to save config or reschedule after creating task '{task.name}': {e}")
        # Revert change in memory if save/schedule fails
        settings.tasks.pop()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration or update scheduler."
        )
        
    return task

@router.get("/{task_name}", response_model=Task)
def get_task_by_name(task_name: str):
    """Retrieve a specific task by its name."""
    task = next((t for t in settings.tasks if t.name == task_name), None)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with name '{task_name}' not found."
        )
    return task

@router.put("/{task_name}", response_model=Task)
async def update_task(task_name: str, updated_task: Task):
    """Update an existing monitoring task."""
    for i, task in enumerate(settings.tasks):
        if task.name == task_name:
            settings.tasks[i] = updated_task
            save_config(settings, get_config_path())
            schedule_task(updated_task)
            logger.info(f"Successfully updated and rescheduled task: {updated_task.name}")
            return updated_task
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

@router.delete("/{task_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_name: str):
    """Delete a monitoring task."""
    task_found = False
    for task in settings.tasks:
        if task.name == task_name:
            settings.tasks.remove(task)
            task_found = True
            break
    
    if not task_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with name '{task_name}' not found."
        )
        
    save_config(settings, get_config_path())
    remove_job(task_name)
    logger.info(f"Successfully deleted and rescheduled tasks. Removed: {task_name}")
    return 