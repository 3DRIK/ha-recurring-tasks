"""Constants for Recurring Tasks integration."""

DOMAIN = "recurring_tasks"
STORAGE_KEY = f"{DOMAIN}.tasks"
STORAGE_VERSION = 1

# Config entry keys
CONF_TASKS = "tasks"

# Task keys
TASK_ID = "id"
TASK_NAME = "name"
TASK_ICON = "icon"
TASK_INTERVAL_DAYS = "interval_days"
TASK_WARN_BEFORE_DAYS = "warn_before_days"
TASK_LAST_DONE = "last_done"
TASK_NOTIFY = "notify"
TASK_NOTIFY_SERVICE = "notify_service"
TASK_NOTIFY_TIME = "notify_time"
TASK_NOTES = "notes"

# Sensor states
STATE_OK = "ok"
STATE_SOON = "soon"
STATE_OVERDUE = "overdue"
STATE_UNKNOWN = "unknown"

# Default values
DEFAULT_WARN_BEFORE_DAYS = 2
DEFAULT_NOTIFY_TIME = "09:00"
DEFAULT_ICON = "mdi:clipboard-check"

# Icons for common tasks
TASK_ICONS = [
    "mdi:vacuum",
    "mdi:broom",
    "mdi:washing-machine",
    "mdi:dishwasher",
    "mdi:air-filter",
    "mdi:water-pump",
    "mdi:fire-extinguisher",
    "mdi:smoke-detector",
    "mdi:car-wrench",
    "mdi:flower",
    "mdi:grass",
    "mdi:lightbulb",
    "mdi:wrench",
    "mdi:hammer",
    "mdi:clipboard-check",
    "mdi:calendar-check",
    "mdi:home",
    "mdi:bed",
    "mdi:shower",
    "mdi:toilet",
    "mdi:fridge",
    "mdi:microwave",
    "mdi:stove",
    "mdi:window-open",
    "mdi:garage",
]

PLATFORMS = ["sensor", "button"]
