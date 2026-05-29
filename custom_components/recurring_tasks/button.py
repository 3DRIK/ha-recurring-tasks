"""Button platform for Recurring Tasks – 'Mark as done'."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_ICON, DOMAIN, TASK_ICON, TASK_NAME
from .coordinator import RecurringTasksCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator: RecurringTasksCoordinator = hass.data[DOMAIN]["coordinator"]
    entities: list[RecurringTaskButton] = []

    for task_id in coordinator.data:
        entities.append(RecurringTaskButton(coordinator, task_id))

    async_add_entities(entities)

    @callback
    def _async_add_new_buttons() -> None:
        existing_ids = {e.task_id for e in entities}
        new_entities = []
        for task_id in coordinator.data:
            if task_id not in existing_ids:
                btn = RecurringTaskButton(coordinator, task_id)
                new_entities.append(btn)
                entities.append(btn)
        if new_entities:
            async_add_entities(new_entities)

    coordinator.async_add_listener(_async_add_new_buttons)


class RecurringTaskButton(CoordinatorEntity, ButtonEntity):
    """Button to mark a task as done."""

    def __init__(self, coordinator: RecurringTasksCoordinator, task_id: str) -> None:
        super().__init__(coordinator)
        self.task_id = task_id
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{DOMAIN}_{task_id}_button"

    @property
    def _task(self) -> dict[str, Any] | None:
        return (self.coordinator.data or {}).get(self.task_id)

    @property
    def name(self) -> str:
        task_name = (self._task or {}).get(TASK_NAME, "Unknown Task")
        return f"{task_name} – Označiť hotové"

    @property
    def icon(self) -> str:
        return "mdi:check-circle"

    async def async_press(self) -> None:
        """Handle button press – mark task done."""
        await self.coordinator.async_mark_done(self.task_id)
        _LOGGER.debug("Task %s marked as done via button", self.task_id)

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.task_id)},
            "name": (self._task or {}).get(TASK_NAME, "Recurring Task"),
            "manufacturer": "Recurring Tasks",
            "model": "Task",
        }
