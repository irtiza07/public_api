"""
TODO CRUD Operations

This module provides all CRUD operations for managing TODOs in a CSV file.
"""

import csv
from datetime import datetime
from pathlib import Path


# Path to the CSV file
TODO_FILE = Path(__file__).parent / "todos.csv"

# CSV headers
CSV_HEADERS = ["id", "name", "priority", "time_created", "time_due", "status"]


def get_next_id() -> int:
    """Get the next available ID for a new TODO."""
    max_id = 0

    with open(TODO_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                current_id = int(row["id"])
                max_id = max(max_id, current_id)
            except (ValueError, KeyError):
                continue

    return max_id + 1


def list_todos(status_filter: str = None):
    """Read all TODOs from the CSV file."""
    todos = []

    with open(TODO_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if status_filter and row.get("status") != status_filter:
                continue
            todos.append(row)

    return todos


def add_todo(
    name: str, priority: str = "medium", time_due: str = "", status: str = "pending"
):
    """Add a new TODO to the CSV file."""
    todo = {
        "id": str(get_next_id()),
        "name": name,
        "priority": priority,
        "time_created": datetime.now().isoformat(),
        "time_due": time_due,
        "status": status,
    }

    with open(TODO_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(todo)

    return todo


def update_todo(
    todo_id: str,
    name: str = None,
    priority: str = None,
    time_due: str = None,
    status: str = None,
):
    """Update an existing TODO."""
    todos = []
    updated_todo = None

    with open(TODO_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == str(todo_id):
                if name is not None:
                    row["name"] = name
                if priority is not None:
                    row["priority"] = priority
                if time_due is not None:
                    row["time_due"] = time_due
                if status is not None:
                    row["status"] = status
                updated_todo = row
            todos.append(row)

    if updated_todo is None:
        raise ValueError(f"TODO with ID {todo_id} not found")

    with open(TODO_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(todos)

    return updated_todo


def delete_todo(todo_id: str):
    """Delete a TODO by ID."""
    todos = []
    found = False

    with open(TODO_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == str(todo_id):
                found = True
            else:
                todos.append(row)

    if not found:
        return False

    with open(TODO_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(todos)

    return True
