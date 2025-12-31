"""
OpenAI Function Schemas and Tool Configuration

This module defines the function schemas for OpenAI's function calling feature
and maps function names to their actual implementations. These schemas are 
carefully designed to optimize OpenAI's tool selection intelligence.

Key Design Principles:
1. Detailed descriptions with natural language keywords
2. Clear parameter definitions with examples
3. Strict mode for reliable schema adherence
4. Enum constraints to prevent invalid inputs
"""

from functions import get_weather, get_todos, get_traffic


# =============================================================================
# OPENAI FUNCTION SCHEMAS - Designed for optimal tool selection
# =============================================================================

# Note: These schemas are carefully crafted to help OpenAI understand
# when and how to use each function. The descriptions are detailed and
# include keywords that users might naturally say.

FUNCTION_SCHEMAS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather conditions, temperature, and forecast for any city or location. Use this when users ask about weather, temperature, climate, conditions, or forecasts.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country/state (e.g., 'Paris, France' or 'New York, USA'). Required for accurate weather data."
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units. Default is celsius."
                }
            },
            "required": ["location"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_todos",
        "description": "Retrieve and manage todo items, tasks, schedule items, or reminders. Use when users mention todos, tasks, schedule, agenda, reminders, or want to see what they need to do.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["all", "work", "personal", "family", "health", "travel"],
                    "description": "Filter todos by category. Default is 'all' to show everything."
                },
                "priority": {
                    "type": "string", 
                    "enum": ["all", "high", "medium", "low"],
                    "description": "Filter todos by priority level. Default is 'all'."
                }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_traffic",
        "description": "Get current traffic conditions, travel time, and route information to a destination. Use when users ask about traffic, commute, drive time, travel time, or directions.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The destination or area to check traffic for (e.g., 'downtown', 'airport', 'shopping center')"
                },
                "departure_time": {
                    "type": "string",
                    "description": "When to leave - 'now' for current conditions or a time like '5 PM'. Default is 'now'."
                }
            },
            "required": ["destination"],
            "additionalProperties": False
        }
    }
]

# =============================================================================
# FUNCTION DISPATCHER - Maps function names to actual Python functions
# =============================================================================

AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather,
    "get_todos": get_todos,
    "get_traffic": get_traffic
}