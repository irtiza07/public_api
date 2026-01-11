"""
Simple MCP Server for TODO Management

This MCP server provides tools to manage TODOs in a local CSV file.
Tools:
- list_todos: Read and list all TODOs
- add_todo: Add a new TODO item
- update_todo: Update an existing TODO
- delete_todo: Delete a TODO by ID
"""

import asyncio
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


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


# Create MCP server instance
app = Server("todo-manager")


@app.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="list_todos",
            description="List all TODOs from the CSV file. Optionally filter by status (pending, completed).",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["pending", "completed"],
                        "description": "Optional status filter",
                    }
                },
            },
        ),
        Tool(
            name="add_todo",
            description="Add a new TODO to the CSV file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "TODO name"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "TODO priority (default: medium)",
                    },
                    "time_due": {
                        "type": "string",
                        "description": "Due date/time (ISO format or any string)",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed"],
                        "description": "TODO status (default: pending)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_todo",
            description="Update an existing TODO. Provide the ID and any fields to update.",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "string",
                        "description": "ID of the TODO to update",
                    },
                    "name": {"type": "string", "description": "New name"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority",
                    },
                    "time_due": {"type": "string", "description": "New due date/time"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed"],
                        "description": "New status",
                    },
                },
                "required": ["todo_id"],
            },
        ),
        Tool(
            name="delete_todo",
            description="Delete a TODO by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "string",
                        "description": "ID of the TODO to delete",
                    }
                },
                "required": ["todo_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any):
    """Handle tool calls."""
    try:
        if name == "list_todos":
            status_filter = arguments.get("status_filter")
            todos = list_todos(status_filter)

            if not todos:
                result = "No TODOs found."
            else:
                result = "TODOs:\n\n"
                for todo in todos:
                    result += f"ID: {todo['id']}\n"
                    result += f"Name: {todo['name']}\n"
                    result += f"Priority: {todo['priority']}\n"
                    result += f"Status: {todo['status']}\n"
                    result += f"Created: {todo['time_created']}\n"
                    result += f"Due: {todo['time_due']}\n"
                    result += "-" * 50 + "\n"

            return [TextContent(type="text", text=result)]

        elif name == "add_todo":
            name = arguments["name"]
            priority = arguments.get("priority", "medium")
            time_due = arguments.get("time_due", "")
            status = arguments.get("status", "pending")

            todo = add_todo(name, priority, time_due, status)

            result = f"✅ TODO added successfully!\n\n"
            result += f"ID: {todo['id']}\n"
            result += f"Name: {todo['name']}\n"
            result += f"Priority: {todo['priority']}\n"
            result += f"Status: {todo['status']}\n"
            result += f"Due: {todo['time_due']}\n"

            return [TextContent(type="text", text=result)]

        elif name == "update_todo":
            todo_id = arguments["todo_id"]
            name = arguments.get("name")
            priority = arguments.get("priority")
            time_due = arguments.get("time_due")
            status = arguments.get("status")

            todo = update_todo(todo_id, name, priority, time_due, status)

            result = f"✅ TODO updated successfully!\n\n"
            result += f"ID: {todo['id']}\n"
            result += f"Name: {todo['name']}\n"
            result += f"Priority: {todo['priority']}\n"
            result += f"Status: {todo['status']}\n"
            result += f"Due: {todo['time_due']}\n"

            return [TextContent(type="text", text=result)]

        elif name == "delete_todo":
            todo_id = arguments["todo_id"]

            if delete_todo(todo_id):
                result = f"✅ TODO with ID {todo_id} deleted successfully!"
            else:
                result = f"❌ TODO with ID {todo_id} not found."

            return [TextContent(type="text", text=result)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
