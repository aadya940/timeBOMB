from nicegui import ui
from datetime import datetime, timedelta
import threading
import time
import queue

from _tasks import TaskManager


# Create an instance of the TaskManager
task_manager = TaskManager()

# Main layout
with ui.column().classes("items-center"):
    ui.label("💣 timeBOMB: Tasks that don’t wait").classes(
        "text-3xl font-extrabold text-center mt-6 text-blue-600"
    )
    ui.label(
        "Create tasks with self-destruct timers. Once set, you can't change the timer!"
    ).classes("text-center text-gray-700")

    with ui.column() as task_manager.task_display:
        ui.label("No tasks yet").classes("text-gray-500")

    ui.button("Add New Task", on_click=lambda: add_task_dialog.open()).classes(
        "bg-blue-500 text-white font-semibold mt-4 px-4 py-2 rounded-lg shadow-md hover:bg-blue-600"
    )

    echart = (
        ui.echart(
            {
                "title": {
                    "text": "Task Completion Analytics",
                    "left": "center",
                    "top": "-2%",
                },
                "series": [
                    {
                        "name": "Tasks",
                        "type": "pie",
                        "data": [
                            {
                                "value": task_manager.completed_tasks,
                                "name": "Completed",
                            },
                            {
                                "value": task_manager.incomplete_tasks,
                                "name": "Incomplete",
                            },
                        ],
                        "itemStyle": {
                            "emphasis": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)",
                            }
                        },
                    }
                ],
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "left": "left", "top": "30%"},
            }
        )
        .classes("w-full max-w-xs mt-8")
        .style("height: 300px;")
    )

    with ui.element("div") as notify:
        pass

# Modal for adding a new task
with ui.dialog() as add_task_dialog:
    with ui.column().classes("p-4 items-center") as main_col:
        main_col.style(
            "background-color: rgba(255, 255, 255, 0.9); border: 2px solid #4A90E2; border-radius: 8px;"
        )

        ui.label("Add a New Task").classes("text-xl font-bold")
        task_name = ui.input("Task Name")
        task_description = ui.textarea("Task Description")

        date_picker = ui.date().props(f"width=20px height=20px")
        time_input = ui.input("Enter Time (e.g., '3:00 PM')", placeholder="3:00 PM")
        duration_dropdown = ui.select(
            {
                86400: "1 Day",
                604800: "1 Week",
                2592000: "1 Month",
                31536000: "1 Year",
            }
        )

        ui.button(
            "Add Task",
            on_click=lambda: (
                task_manager.add_task(
                    task_name.value,
                    (
                        (
                            datetime.combine(
                                datetime.strptime(date_picker.value, "%Y-%m-%d").date(),
                                (
                                    datetime.strptime(
                                        time_input.value, "%I:%M %p"
                                    ).time()
                                    if time_input.value
                                    else datetime.min.time()
                                ),
                            ).timestamp()
                            - datetime.now().timestamp()
                        )
                        if date_picker.value
                        else 0
                    )
                    + (int(duration_dropdown.value) if duration_dropdown.value else 0),
                    task_description.value,
                ),
                add_task_dialog.close(),
            ),
        ).classes(
            "bg-green-500 text-white font-bold mt-3 px-4 py-2 rounded-lg shadow-md"
        )

ui.run()
