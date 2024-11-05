from nicegui import ui
from datetime import datetime, timedelta, date
import threading
import time
import queue


class TaskManager:
    def __init__(self):
        self.tasks = []
        self.task_lock = threading.Lock()
        self.completed_tasks = 0
        self.incomplete_tasks = 0
        self.task_queue = queue.Queue()
        self.task_display = None

        # Start background threads for task checking and processing
        threading.Thread(target=self.check_expired_tasks, daemon=True).start()
        threading.Thread(target=self.process_expired_tasks, daemon=True).start()

    def update_task_list(self):
        """Update the displayed list of tasks."""
        if self.task_display is None:
            return

        self.task_display.clear()
        with self.task_lock:
            if self.tasks:
                for task in self.tasks:
                    self.display_task(task)
            else:
                with self.task_display:
                    ui.label("No tasks yet").classes("text-gray-500")

    def display_task(self, task):
        """Display a single task in the UI."""
        with self.task_display:
            with ui.card().classes(
                "p-6 mb-4 shadow-lg rounded-xl border border-gray-200"
            ).style("background-color: #f9fafb;"):
                with ui.row().classes("items-center"):
                    ui.icon("assignment").classes("text-blue-600 mr-3 text-xl")
                    ui.label(task["name"]).classes("text-xl font-bold")
                ui.label(task["description"]).classes("text-sm text-gray-500")

                # Calculate time left
                time_left = max((task["end_time"] - datetime.now()).total_seconds(), 0)
                ui.label(
                    f"Time Left: {str(timedelta(seconds=int(time_left)))}"
                ).classes(
                    "text-sm text-red-500 font-semibold"
                    if time_left < 60
                    else "text-sm text-gray-600"
                )

    def check_expired_tasks(self):
        """Check for and process expired tasks."""
        while True:
            current_time = datetime.now()
            expired_tasks = []
            near_expiry_tasks = []

            with self.task_lock:
                for task in self.tasks[:]:
                    remaining_time = task["end_time"] - current_time
                    if remaining_time.total_seconds() <= 0:
                        expired_tasks.append(task)
                        self.tasks.remove(task)
                    elif (
                        not task.get("notified")
                        and remaining_time <= task["five_percent_time"]
                    ):
                        near_expiry_tasks.append(task)
                        task["notified"] = True

            for task in expired_tasks:
                self.task_queue.put(task)

            for task in near_expiry_tasks:
                with notify:
                    ui.notify(
                        f"Task {task['name']} is about to expire! 💣",
                        close_button="OK",
                        type="info",
                        multi_line=True,
                    )

            self.update_task_list()
            time.sleep(1)

    def ask_completion(self, task):
        """Prompt user if the task was completed."""
        with ui.dialog() as completion_dialog:
            with ui.column().classes("p-5 items-center"):
                ui.label(f"Did you complete the task '{task['name']}'?").classes(
                    "text-lg font-bold"
                )
                with ui.row():
                    ui.button(
                        "Yes",
                        on_click=lambda: (
                            self.mark_task_completed(True),
                            completion_dialog.close(),
                        ),
                    ).classes("bg-green-500 text-white")
                    ui.button(
                        "No",
                        on_click=lambda: (
                            self.mark_task_completed(False),
                            completion_dialog.close(),
                        ),
                    ).classes("bg-red-500 text-white")

        completion_dialog.open()

    def mark_task_completed(self, completed):
        """Mark a task as completed or incomplete."""
        if completed:
            self.completed_tasks += 1
        else:
            self.incomplete_tasks += 1
        self.update_analytics_chart()

    def add_task(self, name, end_time, description):
        """Add a new task."""
        with self.task_lock:
            self.tasks.append(
                {
                    "name": name,
                    "description": description,
                    "end_time": datetime.now() + timedelta(seconds=end_time),
                    "five_percent_time": timedelta(seconds=end_time * 0.1),
                    "notified": False,
                }
            )
        self.update_task_list()

    def update_analytics_chart(self):
        """Update the analytics chart with task completion data."""
        echart.options["series"][0]["data"][0]["value"] = self.completed_tasks
        echart.options["series"][0]["data"][1]["value"] = self.incomplete_tasks
        echart.update()

    def process_expired_tasks(self):
        """Process expired tasks and ask for completion."""

        def check_queue():
            try:
                task = self.task_queue.get_nowait()
                self.ask_completion(task)
            except queue.Empty:
                pass

        ui.timer(1, check_queue)


# Create an instance of the TaskManager
task_manager = TaskManager()

# Main layout
with ui.column().classes("items-center"):
    ui.label("💣 timeBOMB: Tasks that don’t wait").classes(
        "text-3xl font-extrabold text-center mt-6"
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

        # Task Name input
        task_name = ui.input("Task Name").props("placeholder='E.g., Complete report'")
        ui.label("Enter a unique name for the task").classes("text-gray-500 text-sm")

        # Task Description (optional)
        task_description = ui.textarea("Task Description").props(
            "placeholder='Brief description of the task'"
        )
        ui.label("Optional: Provide additional details about the task").classes(
            "text-gray-500 text-sm"
        )

        # Deadline Date picker
        today = datetime.now().date()
        date_picker = ui.date().props(f"min='{today}' width=20px height=20px")
        ui.label("Select the date by which the task should be completed").classes(
            "text-gray-500 text-sm"
        )

        # Deadline Time input (optional)
        time_input = ui.input(
            "Enter Time (e.g., '3:00 PM')",
            placeholder="3:00 PM",
            validation={
                "Improper Time (Hours).": lambda value: int(value.strip()[0])
                in range(0, 13),
                "Improper Time (Minutes).": lambda value: int(value.strip()[2:4])
                in range(0, 61),
            },
        )
        ui.label("Optional: Specify the time the task should be completed by").classes(
            "text-gray-500 text-sm"
        )

        # Duration Dropdown
        duration_dropdown = ui.select(
            {
                86400: "1 Day",
                604800: "1 Week",
                2592000: "1 Month",
                31536000: "1 Year",
            }
        ).props("placeholder='Select task duration'")

        ui.label(
            "Choose a default duration if no specific deadline date is set"
        ).classes("text-gray-500 text-sm")

        # Add Task button with no validation
        add_task_button = ui.button(
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
