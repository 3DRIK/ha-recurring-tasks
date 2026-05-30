# 📋 Recurring Tasks – Home Assistant Integration

A Home Assistant custom integration for managing recurring household tasks with notifications, dashboard visualization, and flexible scheduling.

---

## Features

- Add recurring tasks via the UI (no YAML required)
- Tracks last completion date and calculates next due date
- Three states: **ok**, **soon** (configurable warning threshold), **overdue**
- Human-readable `time_remaining` attribute (e.g. "In 3 days", "Overdue by 2 days")
- Set a custom past date when you forgot to check off a task
- Optional daily push notifications per task
- Compatible with [Bubble Card](#bubble-card-example), `decluttering-card`, and the bundled `recurring-tasks-card`

---

## Requirements

- Home Assistant **2023.1.0** or newer
- [HACS](https://hacs.xyz/) installed

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → click the three-dot menu → **Custom repositories**
2. Add your repository URL and select category **Integration**
3. Find **Recurring Tasks** in the list and click **Download**
4. Restart Home Assistant

### Manual

1. Download or clone this repository
2. Copy the `custom_components/recurring_tasks/` folder into your HA config directory:
   ```
   config/
   └── custom_components/
       └── recurring_tasks/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── coordinator.py
           ├── storage.py
           ├── sensor.py
           ├── button.py
           ├── const.py
           └── strings.json
   ```
3. Restart Home Assistant

---

## Setup

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Recurring Tasks** and click it
3. Click **Submit** – the integration is now active
4. Click **Configure** (the pencil icon) to add your first task

---

## Managing Tasks

All task management is done through the integration's **Configure** menu:

| Action | Description |
|---|---|
| ➕ Add task | Create a new recurring task |
| ✏️ Edit task | Change name, interval, icon, notifications |
| 📅 Set completion date | Set a past date if you forgot to check off |
| 🗑️ Delete task | Remove a task and its entities |

### Task fields

| Field | Description |
|---|---|
| **Name** | Display name of the task |
| **Interval (days)** | How often the task repeats. `7` = weekly, `30` = monthly, `365` = yearly |
| **Warn before (days)** | How many days before the due date the state changes to `soon` |
| **Icon** | Any MDI icon (e.g. `mdi:vacuum`) |
| **Notes** | Optional reminder text shown in the dashboard card |
| **Enable notifications** | Send a daily push notification when the task is `soon` or `overdue` |
| **Notify service** | Name of your notify service, e.g. `mobile_app_my_phone` |
| **Notify time** | Time of day to send the notification |

---

## Entities

Each task creates two entities:

### Sensor – `sensor.<task_name>`

Tracks the current state of the task.

**States:**

| State | Meaning |
|---|---|
| `ok` | Task is up to date |
| `soon` | Due within the warning threshold |
| `overdue` | Past the due date |
| `unknown` | Never completed |

**Attributes:**

| Attribute | Example | Description |
|---|---|---|
| `task_id` | `a3f9bc12` | Internal ID used by services |
| `due_date` | `2025-06-07` | Next due date (ISO format) |
| `due_date_formatted` | `07.06.2025` | Next due date (readable) |
| `last_done` | `2025-05-31` | Last completion date (ISO) |
| `last_done_formatted` | `31.05.2025 14:30` | Last completion (readable) |
| `days_remaining` | `7` | Days until due |
| `days_overdue` | `0` | Days past due |
| `time_remaining` | `In 1 week` | Human-readable time until due |
| `interval_days` | `7` | Configured interval |
| `notes` | `Use the Dyson` | Optional notes |

### Button – `button.<task_name>_mark_done`

Press to mark the task as completed right now. The due date is recalculated from the current timestamp.

---

## Services

### `recurring_tasks.mark_done`

Mark a task as completed now.

```yaml
service: recurring_tasks.mark_done
data:
  task_id: a3f9bc12
```

### `recurring_tasks.add_task`

Create a task from an automation or script.

```yaml
service: recurring_tasks.add_task
data:
  name: Clean the filter
  interval_days: 90
  warn_before_days: 7
  icon: mdi:air-filter
  notify: true
  notify_service: mobile_app_my_phone
  notify_time: "09:00"
```

### `recurring_tasks.delete_task`

```yaml
service: recurring_tasks.delete_task
data:
  task_id: a3f9bc12
```

> **Finding task_id:** Open the sensor entity in Developer Tools → States and look at the `task_id` attribute.

---

## Dashboard Cards

### Bundled Card – `recurring-tasks-card`

Shows all tasks automatically without any manual configuration.

**Installation:**

1. Copy `www/recurring-tasks-card/recurring-tasks-card.js` to `config/www/recurring-tasks-card/`
2. Add the resource in `configuration.yaml`:
   ```yaml
   lovelace:
     resources:
       - url: /local/recurring-tasks-card/recurring-tasks-card.js
         type: module
   ```
3. Add the card to your dashboard:
   ```yaml
   type: custom:recurring-tasks-card
   title: Household Tasks
   show_notes: true
   show_progress: true
   sort_by: state   # state | name | due_date
   ```

The card auto-discovers all recurring task sensors, shows color-coded status, a progress bar, and a ✓ button to mark tasks done inline.

---

## Bubble Card Example

Requires [Bubble Card](https://github.com/Clooos/Bubble-Card) and [decluttering-card](https://github.com/custom-cards/decluttering-card) from HACS.

For dynamic background color based on task state, also install [card-mod](https://github.com/thomasloven/lovelace-card-mod).

### 1. Define the template (once in your dashboard YAML)

```yaml
decluttering_templates:
  recurring_task:
    default:
      - sensor_entity: null
      - button_entity: null
      - task_name: "Task"
    card:
      type: custom:bubble-card
      card_type: button
      button_type: state
      name: "[[task_name]]"
      entity: "[[sensor_entity]]"
      show_last_changed: false
      show_attribute: true
      attribute: last_done_formatted
      rows: 1.719
      card_mod:
        style: |
          ha-card {
            {% if is_state('[[sensor_entity]]', 'overdue') %}
              background: rgba(239, 68, 68, 0.15) !important;
              border: 1px solid rgba(239, 68, 68, 0.6) !important;
            {% elif is_state('[[sensor_entity]]', 'soon') %}
              background: rgba(245, 158, 11, 0.15) !important;
              border: 1px solid rgba(245, 158, 11, 0.6) !important;
            {% endif %}
          }
      sub_button:
        main:
          - entity: "[[button_entity]]"
        bottom:
          - entity: "[[sensor_entity]]"
            show_attribute: true
            attribute: time_remaining
            name: Next due
            show_name: true
            icon: mdi:clock-time-four-outline
```

### 2. Add a card per task

```yaml
type: custom:decluttering-card
template: recurring_task
variables:
  - task_name: Vacuum the apartment
  - sensor_entity: sensor.vacuum_apartment_vacuum_apartment
  - button_entity: button.vacuum_apartment_vacuum_apartment_mark_done
```

Each new task only needs these 3 lines. The template handles all styling and layout automatically.

**Color coding:**

| State | Color |
|---|---|
| `overdue` | 🔴 Red background + red border |
| `soon` | 🟡 Orange background + orange border |
| `ok` | Default card background |

---

## Examples

### Weekly vacuum reminder with notification

```yaml
service: recurring_tasks.add_task
data:
  name: Vacuum apartment
  interval_days: 7
  warn_before_days: 1
  icon: mdi:vacuum
  notify: true
  notify_service: mobile_app_my_phone
  notify_time: "08:00"
```

### Annual filter replacement

```yaml
service: recurring_tasks.add_task
data:
  name: Replace HVAC filter
  interval_days: 365
  warn_before_days: 14
  icon: mdi:air-filter
  notes: Filter size: 500x200mm, bought at OBI
  notify: true
  notify_service: mobile_app_my_phone
  notify_time: "09:00"
```

### Automation – mark done when robot vacuum finishes

```yaml
automation:
  - alias: "Mark vacuum done when robot finishes"
    trigger:
      - platform: state
        entity_id: sensor.robot_vacuum_status
        to: "idle"
    action:
      - service: recurring_tasks.mark_done
        data:
          task_id: a3f9bc12
```

---

## Troubleshooting

**Sensor shows `unknown` after adding a task**
This is expected – the task has never been completed. Press the button entity or use `recurring_tasks.mark_done` to set the first completion date.

**Notification not arriving**
Check that the `notify_service` value matches your actual service name. Go to Developer Tools → Services, search for `notify` and find your device's service name (e.g. `notify.mobile_app_martins_iphone`). Enter only the part after `notify.`.

**State not updating**
The coordinator refreshes every 30 minutes. To force an update, go to Developer Tools → Services and call `homeassistant.reload_config_entry` or restart HA.

---

## License

MIT
