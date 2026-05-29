"""Data coordinator for Recurring Tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_NOTIFY_TIME,
    DEFAULT_WARN_BEFORE_DAYS,
    DOMAIN,
    STATE_OK,
    STATE_OVERDUE,
    STATE_SOON,
    STATE_UNKNOWN,
    TASK_INTERVAL_DAYS,
    TASK_LAST_DONE,
    TASK_NAME,
    TASK_NOTIFY,
    TASK_NOTIFY_SERVICE,
    TASK_NOTIFY_TIME,
    TASK_WARN_BEFORE_DAYS,
)
from .storage import RecurringTasksStorage

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=30)


class RecurringTasksCoordinator(DataUpdateCoordinator):
    """Coordinator managing all recurring tasks."""

    def __init__(self, hass: HomeAssistant, storage: RecurringTasksStorage) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.storage = storage
        self._notify_unsub: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and compute task states."""
        tasks = self.storage.get_tasks()
        computed = {}
        for task_id, task in tasks.items():
            computed[task_id] = self._compute_task_state(task)
        return computed

    def _compute_task_state(self, task: dict[str, Any]) -> dict[str, Any]:
        """Compute derived state for a task."""
        last_done_raw = task.get(TASK_LAST_DONE)
        interval = int(task.get(TASK_INTERVAL_DAYS, 7))
        warn_days = int(task.get(TASK_WARN_BEFORE_DAYS, DEFAULT_WARN_BEFORE_DAYS))

        if not last_done_raw:
            return {
                **task,
                "state": STATE_UNKNOWN,
                "due_date": None,
                "days_remaining": None,
                "days_overdue": None,
            }

        try:
            last_done = datetime.fromisoformat(last_done_raw)
        except (ValueError, TypeError):
            return {**task, "state": STATE_UNKNOWN, "due_date": None, "days_remaining": None, "days_overdue": None}

        due_date = last_done + timedelta(days=interval)
        now = datetime.now()
        diff_days = (due_date.date() - now.date()).days

        if diff_days < 0:
            state = STATE_OVERDUE
        elif diff_days <= warn_days:
            state = STATE_SOON
        else:
            state = STATE_OK

        return {
            **task,
            "state": state,
            "due_date": due_date,
            "days_remaining": max(0, diff_days),
            "days_overdue": max(0, -diff_days),
            "last_done_dt": last_done,
        }

    async def async_create_task(self, task_data: dict[str, Any]) -> str:
        """Create a new task."""
        task_id = await self.storage.async_create_task(task_data)
        await self.async_refresh()
        self._setup_notify(task_id)
        return task_id

    async def async_update_task(self, task_id: str, updates: dict[str, Any]) -> None:
        """Update a task."""
        await self.storage.async_update_task(task_id, updates)
        await self.async_refresh()
        self._teardown_notify(task_id)
        self._setup_notify(task_id)

    async def async_delete_task(self, task_id: str) -> None:
        """Delete a task."""
        self._teardown_notify(task_id)
        await self.storage.async_delete_task(task_id)
        await self.async_refresh()

    async def async_mark_done(self, task_id: str) -> None:
        """Mark task as done."""
        await self.storage.async_mark_done(task_id)
        await self.async_refresh()

    def _setup_notify(self, task_id: str) -> None:
        """Set up daily notification for a task."""
        task = self.storage.get_task(task_id)
        if not task or not task.get(TASK_NOTIFY):
            return

        notify_time_str = task.get(TASK_NOTIFY_TIME, DEFAULT_NOTIFY_TIME)
        try:
            t = datetime.strptime(notify_time_str, "%H:%M")
            hour, minute = t.hour, t.minute
        except ValueError:
            hour, minute = 9, 0

        @callback
        def _notify_callback(now: datetime) -> None:
            self.hass.async_create_task(self._async_send_notification(task_id))

        unsub = async_track_time_change(
            self.hass, _notify_callback, hour=hour, minute=minute, second=0
        )
        self._notify_unsub[task_id] = unsub
        _LOGGER.debug("Scheduled notification for task %s at %02d:%02d", task_id, hour, minute)

    def _teardown_notify(self, task_id: str) -> None:
        """Remove scheduled notification."""
        if task_id in self._notify_unsub:
            self._notify_unsub.pop(task_id)()

    async def _async_send_notification(self, task_id: str) -> None:
        """Send notification if task is due/overdue."""
        computed = (self.data or {}).get(task_id)
        if not computed:
            return

        state = computed.get("state")
        if state not in (STATE_SOON, STATE_OVERDUE):
            return

        task_name = computed.get(TASK_NAME, "Úloha")
        notify_service = computed.get(TASK_NOTIFY_SERVICE, "notify")
        due_date = computed.get("due_date")
        days_remaining = computed.get("days_remaining", 0)
        days_overdue = computed.get("days_overdue", 0)

        if state == STATE_OVERDUE:
            msg = f"⚠️ {task_name} je po termíne ({days_overdue} dní)"
            title = "🔴 Úloha po termíne"
        else:
            msg = f"⏰ {task_name} je splatná o {days_remaining} dní ({due_date.strftime('%d.%m.%Y') if due_date else ''})"
            title = "🟡 Blížiaci sa termín"

        try:
            await self.hass.services.async_call(
                "notify",
                notify_service.replace("notify.", "") if notify_service.startswith("notify.") else notify_service,
                {"title": title, "message": msg},
            )
        except Exception as err:
            _LOGGER.error("Failed to send notification for task %s: %s", task_id, err)

    async def async_setup_notifications(self) -> None:
        """Set up all task notifications on startup."""
        for task_id in self.storage.get_tasks():
            self._setup_notify(task_id)

    def get_task_state(self, task_id: str) -> dict[str, Any] | None:
        """Get computed state for a task."""
        return (self.data or {}).get(task_id)
