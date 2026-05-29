"""Storage management for Recurring Tasks."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    STORAGE_KEY,
    STORAGE_VERSION,
    TASK_ID,
    TASK_LAST_DONE,
    TASK_NAME,
)

_LOGGER = logging.getLogger(__name__)


class RecurringTasksStorage:
    """Manages persistent storage for recurring tasks."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        if stored:
            self._data = stored
        else:
            self._data = {"tasks": {}}
        _LOGGER.debug("Loaded %d tasks from storage", len(self._data.get("tasks", {})))

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    def get_tasks(self) -> dict[str, Any]:
        """Return all tasks."""
        return self._data.get("tasks", {})

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Return a specific task."""
        return self._data.get("tasks", {}).get(task_id)

    async def async_create_task(self, task_data: dict[str, Any]) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4()).replace("-", "")[:12]
        if "tasks" not in self._data:
            self._data["tasks"] = {}
        self._data["tasks"][task_id] = {
            TASK_ID: task_id,
            TASK_LAST_DONE: None,
            **task_data,
        }
        await self.async_save()
        _LOGGER.debug("Created task %s: %s", task_id, task_data.get(TASK_NAME))
        return task_id

    async def async_update_task(self, task_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing task."""
        if task_id not in self._data.get("tasks", {}):
            return False
        self._data["tasks"][task_id].update(updates)
        await self.async_save()
        return True

    async def async_delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self._data.get("tasks", {}):
            return False
        del self._data["tasks"][task_id]
        await self.async_save()
        _LOGGER.debug("Deleted task %s", task_id)
        return True

    async def async_mark_done(self, task_id: str) -> bool:
        """Mark a task as done (sets last_done to now)."""
        if task_id not in self._data.get("tasks", {}):
            return False
        self._data["tasks"][task_id][TASK_LAST_DONE] = datetime.now().isoformat()
        await self.async_save()
        _LOGGER.debug("Marked task %s as done", task_id)
        return True
