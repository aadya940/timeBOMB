from nicegui import ui
from datetime import datetime, timedelta
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