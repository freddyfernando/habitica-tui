import csv
import requests
import json
import time
import os
import sys
import yaml
import re
from typing import List, Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListItem, ListView, Label, Input, Button
from rich.markdown import Markdown as RichMarkdown
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.binding import Binding
from textual.screen import ModalScreen

# Configuration
BASE_URL = "https://habitica.com/api/v3"

class HabiticaClient:
    def __init__(self, user_id, api_token):
        self.headers = {
            "x-api-user": user_id,
            "x-api-key": api_token,
            "x-client": f"{user_id}-habitica-cli",
            "Content-Type": "application/json"
        }

    def _api_call(self, method, endpoint, payload=None, params=None):
        url = f"{BASE_URL}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=payload, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return None

    def list_tasks(self, task_type=None):
        params = {"type": task_type} if task_type else {}
        result = self._api_call("GET", "tasks/user", params=params)
        return result.get("data", []) if result else []

    def create_task(self, text, task_type="todo", notes="", priority=1):
        payload = {"text": text, "type": task_type, "notes": notes, "priority": priority}
        return self._api_call("POST", "tasks/user", payload=payload)

    def update_task(self, task_id, **updates):
        return self._api_call("PUT", f"tasks/{task_id}", payload=updates)

    def delete_task(self, task_id):
        return self._api_call("DELETE", f"tasks/{task_id}")

    def score_task(self, task_id, direction="up"):
        return self._api_call("POST", f"tasks/{task_id}/score/{direction}")

def get_credentials():
    user_id = os.environ.get("HABITICA_USER_ID")
    api_token = os.environ.get("HABITICA_API_TOKEN")
    return user_id, api_token

class EditTaskModal(ModalScreen):
    def __init__(self, task: Dict[str, Any]):
        super().__init__()
        self.task_data = task

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Edit Task", id="modal-title"),
            Label("Text:"),
            Input(value=self.task_data['text'], id="task-text"),
            Label("Notes:"),
            Input(value=self.task_data.get('notes', ''), id="task-notes"),
            Label("Priority:"),
            Input(value=str(self.task_data.get('priority', 1)), id="task-priority"),
            Horizontal(
                Button("Save", variant="primary", id="save"),
                Button("Cancel", variant="error", id="cancel"),
                classes="modal-buttons"
            ),
            id="edit-grid"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            new_text = self.query_one("#task-text", Input).value
            new_notes = self.query_one("#task-notes", Input).value
            try:
                new_priority = float(self.query_one("#task-priority", Input).value or 1)
            except ValueError:
                new_priority = 1
            
            updates = {
                "text": new_text,
                "notes": new_notes,
                "priority": new_priority
            }
            self.dismiss(updates)
        else:
            self.dismiss(None)

class TaskDetail(Static):
    def update_task(self, task: Optional[Dict[str, Any]]):
        if not task:
            self.update("No task selected")
            return
        
        # Determine Color based on value (score)
        val = task.get('value', 0)
        color = "white"
        if val < -10: color = "red"
        elif val < -1: color = "orange"
        elif val < 1: color = "yellow"
        elif val < 5: color = "green"
        else: color = "blue"

        priority_map = {0.1: "Trivial", 1: "Easy", 1.5: "Medium", 2: "Hard"}
        priority_str = priority_map.get(task.get('priority', 1), str(task.get('priority', 1)))

        md = f"""# {task['text']}

**Type:** {task['type'].upper()}
**Value:** [{color}]{val:.2f}[/{color}]
**Priority:** {priority_str}

## Notes
{task.get('notes', '_No notes_')}

---
**ID:** `{task['id']}`
"""
        self.update(RichMarkdown(md))

class HabiticaTUI(App):
    CSS = """
    Screen {
        layout: horizontal;
        background: $surface;
    }
    #left-col {
        width: 15%;
        border-right: tall $primary-darken-2;
    }
    #mid-col {
        width: 35%;
        border-right: tall $primary-darken-2;
    }
    #right-col {
        width: 50%;
        padding: 1 2;
        background: $surface-lighten-1;
    }
    ListView {
        background: transparent;
    }
    ListView:focus {
        border: double $accent;
        background: $primary-darken-3;
    }
    ListItem {
        padding: 0 1;
        margin: 0;
    }
    .task-positive {
        color: lightgreen;
    }
    .task-negative {
        color: lightcoral;
    }
    .task-neutral {
        color: lightyellow;
    }
    #edit-grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 2;
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        align: center middle;
    }
    #modal-title {
        column-span: 2;
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    .modal-buttons {
        column-span: 2;
        align: center middle;
        height: auto;
    }
    .modal-buttons Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "score_up", "Score +"),
        Binding("x", "score_down", "Score -"),
        Binding("e", "edit_task", "Edit"),
        Binding("d", "delete_task", "Delete"),
        Binding("i", "import_tasks", "Import"),
        Binding("h", "focus_left", "Focus Left", show=False),
        Binding("l", "focus_right", "Focus Right", show=False),
        Binding("left", "focus_left", "Focus Left", show=False),
        Binding("right", "focus_right", "Focus Right", show=False),
        Binding("tab", "focus_next", "Next Pane", show=False),
        Binding("shift+tab", "focus_previous", "Prev Pane", show=False),
    ]

    def __init__(self, client: HabiticaClient):
        super().__init__()
        self.client = client
        self.selected_type = "todos"
        self.tasks = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="left-col"):
            yield Label("[b]Category[/b]")
            yield ListView(
                ListItem(Label("Habits"), id="habits"),
                ListItem(Label("Dailies"), id="dailys"),
                ListItem(Label("Todos"), id="todos"),
                ListItem(Label("Rewards"), id="rewards"),
                id="type-list"
            )
        with Container(id="mid-col"):
            yield Label("[b]Tasks[/b]")
            yield ListView(id="task-list")
        with Container(id="right-col"):
            yield TaskDetail(id="task-detail")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_tasks()
        self.query_one("#type-list").focus()

    def refresh_tasks(self):
        self.tasks = self.client.list_tasks(self.selected_type)
        task_list = self.query_one("#task-list", ListView)
        task_list.clear()
        
        for task in self.tasks:
            val = task.get('value', 0)
            cls = "task-neutral"
            if val > 1: cls = "task-positive"
            if val < -1: cls = "task-negative"
            
            task_list.append(ListItem(Label(task['text'], classes=cls)))
            
        self.update_detail()

    def update_detail(self):
        task_list = self.query_one("#task-list", ListView)
        detail_view = self.query_one("#task-detail", TaskDetail)
        if task_list.index is not None and task_list.index < len(self.tasks):
            detail_view.update_task(self.tasks[task_list.index])
        else:
            detail_view.update_task(None)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "type-list":
            if event.item and event.item.id:
                self.selected_type = event.item.id
                self.refresh_tasks()
        elif event.list_view.id == "task-list":
            self.update_detail()

    def action_focus_left(self):
        self.query_one("#type-list").focus()

    def action_focus_right(self):
        if self.tasks:
            self.query_one("#task-list").focus()

    def action_focus_next(self):
        self.screen.focus_next()

    def action_focus_previous(self):
        self.screen.focus_previous()

    def action_score_up(self):
        task_list = self.query_one("#task-list", ListView)
        if task_list.index is not None:
            task = self.tasks[task_list.index]
            self.client.score_task(task['id'], "up")
            self.notify(f"Scored up: {task['text']}")
            self.refresh_tasks()

    def action_score_down(self):
        task_list = self.query_one("#task-list", ListView)
        if task_list.index is not None:
            task = self.tasks[task_list.index]
            self.client.score_task(task['id'], "down")
            self.notify(f"Scored down: {task['text']}")
            self.refresh_tasks()

    def action_edit_task(self):
        task_list = self.query_one("#task-list", ListView)
        if task_list.index is not None:
            task = self.tasks[task_list.index]
            self.push_screen(EditTaskModal(task), self.refresh_on_edit)

    def refresh_on_edit(self, updates: Optional[Dict[str, Any]]):
        if updates:
            task_list = self.query_one("#task-list", ListView)
            task = self.tasks[task_list.index]
            self.client.update_task(task['id'], **updates)
            self.notify("Task updated")
            self.refresh_tasks()

    def action_delete_task(self):
        task_list = self.query_one("#task-list", ListView)
        if task_list.index is not None:
            task = self.tasks[task_list.index]
            self.client.delete_task(task['id'])
            self.notify(f"Deleted: {task['text']}")
            self.refresh_tasks()

    def action_import_tasks(self):
        self.push_screen(ImportModal(), self.run_import)

    def run_import(self, path: Optional[str]):
        if not path or not os.path.exists(path):
            if path: self.notify(f"File not found: {path}", severity="error")
            return
        
        new_tasks = []
        try:
            if path.endswith('.csv'):
                with open(path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        new_tasks.append({
                            "text": row.get('Task Name', row.get('text')),
                            "type": row.get('Type', row.get('type', 'todo')).lower()
                        })
            elif path.endswith(('.yaml', '.yml')):
                with open(path, 'r') as f:
                    new_tasks = yaml.safe_load(f) or []
            elif path.endswith('.md'):
                with open(path, 'r') as f:
                    content = f.read()
                checklist_matches = re.findall(r"-\s*\[\s*\]\s*(.*)", content)
                for task_text in checklist_matches:
                    new_tasks.append({"text": task_text.strip(), "type": "todo"})
        except Exception as e:
            self.notify(f"Import error: {e}", severity="error")
            return
        
        for task in new_tasks:
            self.client.create_task(task.get('text'), task.get('type', 'todo'))
        
        self.notify(f"Imported {len(new_tasks)} tasks")
        self.refresh_tasks()

class ImportModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Import Tasks", id="modal-title"),
            Label("Enter file path:"),
            Input(placeholder="sample_tasks.yaml", id="import-path"),
            Horizontal(
                Button("Import", variant="primary", id="btn-import"),
                Button("Cancel", variant="error", id="btn-cancel"),
                classes="modal-buttons"
            ),
            id="edit-grid"
        )
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-import":
            self.dismiss(self.query_one("#import-path", Input).value)
        else:
            self.dismiss(None)

if __name__ == "__main__":
    user_id, api_token = get_credentials()
    if not user_id or not api_token:
        print("Set HABITICA_USER_ID and HABITICA_API_TOKEN env variables.")
        sys.exit(1)
    client = HabiticaClient(user_id, api_token)
    app = HabiticaTUI(client)
    app.run()
