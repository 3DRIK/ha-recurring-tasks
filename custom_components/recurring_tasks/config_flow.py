"""Config flow for Recurring Tasks integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DEFAULT_ICON,
    DEFAULT_NOTIFY_TIME,
    DEFAULT_WARN_BEFORE_DAYS,
    DOMAIN,
    TASK_ICON,
    TASK_INTERVAL_DAYS,
    TASK_NAME,
    TASK_NOTES,
    TASK_NOTIFY,
    TASK_NOTIFY_SERVICE,
    TASK_NOTIFY_TIME,
    TASK_WARN_BEFORE_DAYS,
)

_LOGGER = logging.getLogger(__name__)

TASK_SCHEMA = vol.Schema(
    {
        vol.Required(TASK_NAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(TASK_INTERVAL_DAYS, default=7): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=3650, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(TASK_WARN_BEFORE_DAYS, default=DEFAULT_WARN_BEFORE_DAYS): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(TASK_ICON, default=DEFAULT_ICON): selector.IconSelector(),
        vol.Optional(TASK_NOTES, default=""): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT, multiline=True)
        ),
        vol.Optional(TASK_NOTIFY, default=False): selector.BooleanSelector(),
        vol.Optional(TASK_NOTIFY_SERVICE, default="notify.mobile_app"): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Optional(TASK_NOTIFY_TIME, default=DEFAULT_NOTIFY_TIME): selector.TimeSelector(),
    }
)


class RecurringTasksConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Recurring Tasks."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle initial setup step."""
        # Only allow one config entry
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Recurring Tasks", data={})

        return self.async_show_form(
            step_id="user",
            description_placeholders={"description": "Integrácia pre správu pravidelných domácich úloh."},
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> RecurringTasksOptionsFlow:
    return RecurringTasksOptionsFlow()


class RecurringTasksOptionsFlow(config_entries.OptionsFlow):
    """Options flow – manage tasks."""

    def __init__(self) -> None:
    self._task_action: str | None = None
    self._selected_task_id: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Main menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_task", "edit_task", "delete_task"],
        )

    # ── ADD ──────────────────────────────────────────────────────────────────

    async def async_step_add_task(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Add a new task."""
        errors: dict[str, str] = {}

        if user_input is not None:
            coordinator = self.hass.data[DOMAIN]["coordinator"]
            task_data = {
                TASK_NAME: user_input[TASK_NAME],
                TASK_INTERVAL_DAYS: int(user_input[TASK_INTERVAL_DAYS]),
                TASK_WARN_BEFORE_DAYS: int(user_input.get(TASK_WARN_BEFORE_DAYS, DEFAULT_WARN_BEFORE_DAYS)),
                TASK_ICON: user_input.get(TASK_ICON, DEFAULT_ICON),
                TASK_NOTES: user_input.get(TASK_NOTES, ""),
                TASK_NOTIFY: user_input.get(TASK_NOTIFY, False),
                TASK_NOTIFY_SERVICE: user_input.get(TASK_NOTIFY_SERVICE, ""),
                TASK_NOTIFY_TIME: user_input.get(TASK_NOTIFY_TIME, DEFAULT_NOTIFY_TIME),
            }
            await coordinator.async_create_task(task_data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_task",
            data_schema=TASK_SCHEMA,
            errors=errors,
        )

    # ── EDIT ─────────────────────────────────────────────────────────────────

    async def async_step_edit_task(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select task to edit."""
        coordinator = self.hass.data[DOMAIN]["coordinator"]
        tasks = coordinator.storage.get_tasks()

        if not tasks:
            return self.async_abort(reason="no_tasks")

        if user_input is not None:
            self._selected_task_id = user_input["task_id"]
            return await self.async_step_edit_task_form()

        task_options = {tid: t[TASK_NAME] for tid, t in tasks.items()}
        return self.async_show_form(
            step_id="edit_task",
            data_schema=vol.Schema({
                vol.Required("task_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in task_options.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }),
        )

    async def async_step_edit_task_form(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Edit form for selected task."""
        coordinator = self.hass.data[DOMAIN]["coordinator"]
        task = coordinator.storage.get_task(self._selected_task_id)

        if user_input is not None:
            updates = {
                TASK_NAME: user_input[TASK_NAME],
                TASK_INTERVAL_DAYS: int(user_input[TASK_INTERVAL_DAYS]),
                TASK_WARN_BEFORE_DAYS: int(user_input.get(TASK_WARN_BEFORE_DAYS, DEFAULT_WARN_BEFORE_DAYS)),
                TASK_ICON: user_input.get(TASK_ICON, DEFAULT_ICON),
                TASK_NOTES: user_input.get(TASK_NOTES, ""),
                TASK_NOTIFY: user_input.get(TASK_NOTIFY, False),
                TASK_NOTIFY_SERVICE: user_input.get(TASK_NOTIFY_SERVICE, ""),
                TASK_NOTIFY_TIME: user_input.get(TASK_NOTIFY_TIME, DEFAULT_NOTIFY_TIME),
            }
            await coordinator.async_update_task(self._selected_task_id, updates)
            return self.async_create_entry(title="", data={})

        prefill = vol.Schema(
            {
                vol.Required(TASK_NAME, default=task.get(TASK_NAME, "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(TASK_INTERVAL_DAYS, default=task.get(TASK_INTERVAL_DAYS, 7)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=3650, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(TASK_WARN_BEFORE_DAYS, default=task.get(TASK_WARN_BEFORE_DAYS, DEFAULT_WARN_BEFORE_DAYS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(TASK_ICON, default=task.get(TASK_ICON, DEFAULT_ICON)): selector.IconSelector(),
                vol.Optional(TASK_NOTES, default=task.get(TASK_NOTES, "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT, multiline=True)
                ),
                vol.Optional(TASK_NOTIFY, default=task.get(TASK_NOTIFY, False)): selector.BooleanSelector(),
                vol.Optional(TASK_NOTIFY_SERVICE, default=task.get(TASK_NOTIFY_SERVICE, "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Optional(TASK_NOTIFY_TIME, default=task.get(TASK_NOTIFY_TIME, DEFAULT_NOTIFY_TIME)): selector.TimeSelector(),
            }
        )

        return self.async_show_form(step_id="edit_task_form", data_schema=prefill)

    # ── DELETE ────────────────────────────────────────────────────────────────

    async def async_step_delete_task(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select and delete a task."""
        coordinator = self.hass.data[DOMAIN]["coordinator"]
        tasks = coordinator.storage.get_tasks()

        if not tasks:
            return self.async_abort(reason="no_tasks")

        if user_input is not None:
            await coordinator.async_delete_task(user_input["task_id"])
            return self.async_create_entry(title="", data={})

        task_options = {tid: t[TASK_NAME] for tid, t in tasks.items()}
        return self.async_show_form(
            step_id="delete_task",
            data_schema=vol.Schema({
                vol.Required("task_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in task_options.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }),
        )
