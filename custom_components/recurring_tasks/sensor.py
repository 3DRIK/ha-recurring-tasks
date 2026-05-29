"""Sensor platform for Recurring Tasks."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_ICON,
    DOMAIN,
    STATE_OK,
    STATE_OVERDUE,
    STATE_SOON,
    STATE_UNKNOWN,
    TASK_ICON,
    TASK_ID,
    TASK_INTERVAL_DAYS,
    TASK_NAME,
    TASK_NOTES,
    TASK_WARN_BEFORE_DAYS,
)
from .coordinator import RecurringTasksCoordinator

_LOGGER = logging.getLogger(__name__)

STATE_COLORS = {
    STATE_OK: "green",
    STATE_SOON: "yellow",
    STATE_OVERDUE: "red",
    STATE_UNKNOWN: "grey",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: RecurringTasksCoordinator = hass.data[DOMAIN]["coordinator"]
    entities = []

    for task_id, task_data in coordinator.data.items():
        entities.append(RecurringTaskSensor(coordinator, task_id))

    async_add_entities(entities)

    # Listen for new tasks
    @callback
    def _async_add_new_sensors() -> None:
        existing_ids = {e.task_id for e in entities}
        new_entities = []
        for task_id in coordinator.data:
            if task_id not in existing_ids:
                sensor = RecurringTaskSensor(coordinator, task_id)
                new_entities.append(sensor)
                entities.append(sensor)
        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(_async_add_new_sensors)


class RecurringTaskSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity representing one recurring task."""

    def __init__(self, coordinator: RecurringTasksCoordinator, task_id: str) -> None:
        super().__init__(coordinator)
        self.task_id = task_id
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{DOMAIN}_{task_id}_sensor"

    @property
    def _task(self) -> dict[str, Any] | None:
        return (self.coordinator.data or {}).get(self.task_id)

    @property
    def name(self) -> str:
        return self._task.get(TASK_NAME, "Unknown Task") if self._task else "Unknown Task"

    @property
    def icon(self) -> str:
        return (self._task or {}).get(TASK_ICON, DEFAULT_ICON)

    @property
    def native_value(self) -> str:
        task = self._task
        if not task:
            return STATE_UNKNOWN
        return task.get("state", STATE_UNKNOWN)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        task = self._task
        if not task:
            return {}

        due_date: datetime | None = task.get("due_date")
        last_done_dt: datetime | None = task.get("last_done_dt")

        attrs: dict[str, Any] = {
            "task_id": self.task_id,
            "interval_days": task.get(TASK_INTERVAL_DAYS),
            "warn_before_days": task.get(TASK_WARN_BEFORE_DAYS),
            "days_remaining": task.get("days_remaining"),
            "days_overdue": task.get("days_overdue"),
            "notes": task.get(TASK_NOTES, ""),
            "color": STATE_COLORS.get(task.get("state", STATE_UNKNOWN), "grey"),
        }

        if due_date:
            attrs["due_date"] = due_date.strftime("%Y-%m-%d")
            attrs["due_date_formatted"] = due_date.strftime("%d.%m.%Y")

        if last_done_dt:
            attrs["last_done"] = last_done_dt.strftime("%Y-%m-%d")
            attrs["last_done_formatted"] = last_done_dt.strftime("%d.%m.%Y %H:%M")

        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.task_id)},
            "name": (self._task or {}).get(TASK_NAME, "Recurring Task"),
            "manufacturer": "Recurring Tasks",
            "model": "Task",
        }
