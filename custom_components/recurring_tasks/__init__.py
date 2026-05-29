"""Recurring Tasks integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    TASK_ICON,
    TASK_INTERVAL_DAYS,
    TASK_NAME,
    TASK_NOTES,
    TASK_NOTIFY,
    TASK_NOTIFY_SERVICE,
    TASK_NOTIFY_TIME,
    TASK_WARN_BEFORE_DAYS,
    DEFAULT_ICON,
    DEFAULT_NOTIFY_TIME,
    DEFAULT_WARN_BEFORE_DAYS,
)
from .coordinator import RecurringTasksCoordinator
from .storage import RecurringTasksStorage

_LOGGER = logging.getLogger(__name__)

SERVICE_MARK_DONE = "mark_done"
SERVICE_ADD_TASK = "add_task"
SERVICE_DELETE_TASK = "delete_task"

SERVICE_MARK_DONE_SCHEMA = vol.Schema({
    vol.Required("task_id"): cv.string,
})

SERVICE_ADD_TASK_SCHEMA = vol.Schema({
    vol.Required(TASK_NAME): cv.string,
    vol.Required(TASK_INTERVAL_DAYS): vol.Coerce(int),
    vol.Optional(TASK_WARN_BEFORE_DAYS, default=DEFAULT_WARN_BEFORE_DAYS): vol.Coerce(int),
    vol.Optional(TASK_ICON, default=DEFAULT_ICON): cv.string,
    vol.Optional(TASK_NOTES, default=""): cv.string,
    vol.Optional(TASK_NOTIFY, default=False): cv.boolean,
    vol.Optional(TASK_NOTIFY_SERVICE, default=""): cv.string,
    vol.Optional(TASK_NOTIFY_TIME, default=DEFAULT_NOTIFY_TIME): cv.string,
})

SERVICE_DELETE_TASK_SCHEMA = vol.Schema({
    vol.Required("task_id"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Recurring Tasks from a config entry."""
    storage = RecurringTasksStorage(hass)
    await storage.async_load()

    coordinator = RecurringTasksCoordinator(hass, storage)
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_setup_notifications()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN]["entry"] = entry

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_mark_done(call: ServiceCall) -> None:
        task_id = call.data["task_id"]
        if not coordinator.storage.get_task(task_id):
            raise ServiceValidationError(f"Task '{task_id}' not found")
        await coordinator.async_mark_done(task_id)

    async def handle_add_task(call: ServiceCall) -> None:
        task_data = {
            TASK_NAME: call.data[TASK_NAME],
            TASK_INTERVAL_DAYS: call.data[TASK_INTERVAL_DAYS],
            TASK_WARN_BEFORE_DAYS: call.data.get(TASK_WARN_BEFORE_DAYS, DEFAULT_WARN_BEFORE_DAYS),
            TASK_ICON: call.data.get(TASK_ICON, DEFAULT_ICON),
            TASK_NOTES: call.data.get(TASK_NOTES, ""),
            TASK_NOTIFY: call.data.get(TASK_NOTIFY, False),
            TASK_NOTIFY_SERVICE: call.data.get(TASK_NOTIFY_SERVICE, ""),
            TASK_NOTIFY_TIME: call.data.get(TASK_NOTIFY_TIME, DEFAULT_NOTIFY_TIME),
        }
        await coordinator.async_create_task(task_data)

    async def handle_delete_task(call: ServiceCall) -> None:
        task_id = call.data["task_id"]
        if not coordinator.storage.get_task(task_id):
            raise ServiceValidationError(f"Task '{task_id}' not found")
        await coordinator.async_delete_task(task_id)

    hass.services.async_register(DOMAIN, SERVICE_MARK_DONE, handle_mark_done, SERVICE_MARK_DONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_TASK, handle_add_task, SERVICE_ADD_TASK_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_TASK, handle_delete_task, SERVICE_DELETE_TASK_SCHEMA)

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.services.async_remove(DOMAIN, SERVICE_MARK_DONE)
        hass.services.async_remove(DOMAIN, SERVICE_ADD_TASK)
        hass.services.async_remove(DOMAIN, SERVICE_DELETE_TASK)
        hass.data.pop(DOMAIN, None)

    return unload_ok
