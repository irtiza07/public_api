"""
Mock Functions for OpenAI Function Calling Tutorial

This module contains the three core functions that demonstrate OpenAI's tool selection:
- get_weather: Weather information with location and unit conversion
- get_todos: Todo management with category and priority filtering  
- get_traffic: Traffic conditions with destination and timing

Each function uses realistic mock data and focuses on showcasing OpenAI's 
decision-making process rather than complex implementation logic.
"""

import random
from mock_data import WEATHER_RESPONSES, TODO_RESPONSES, TRAFFIC_RESPONSES


def get_weather(location: str, units: str = "celsius") -> str:
    """
    Get current weather information for a specified location.
    
    This function demonstrates how OpenAI identifies location-based queries
    and matches them to weather-related tools based on keywords like:
    'weather', 'temperature', 'forecast', 'climate', 'conditions'
    """
    # Select a random weather response
    weather_data = random.choice(WEATHER_RESPONSES)
    
    # Use provided location or fall back to random location
    if location:
        weather_data["location"] = location
    
    # Convert temperature if needed
    temp = weather_data["temperature"]
    if units.lower() == "fahrenheit":
        temp = (temp * 9/5) + 32
        unit_symbol = "°F"
    else:
        unit_symbol = "°C"
    
    return f"""Weather for {weather_data['location']}:
    🌡️  Temperature: {temp}{unit_symbol}
    ☁️  Conditions: {weather_data['condition']}
    💧 Humidity: {weather_data['humidity']}%
    💨 Wind: {weather_data['wind']}
    📅 Forecast: {weather_data['forecast']}"""


def get_todos(category: str = "all", priority: str = "all") -> str:
    """
    Retrieve todo items, optionally filtered by category or priority.
    
    OpenAI recognizes todo/task-related queries through keywords like:
    'todo', 'tasks', 'schedule', 'reminder', 'add', 'list', 'agenda'
    """
    # Start with all todos, then apply filters
    available_todos = TODO_RESPONSES.copy()
    
    # Apply category filter first
    if category != "all":
        filtered_by_category = [t for t in available_todos if t.get("category", "").lower() == category.lower()]
        if filtered_by_category:  # Only apply filter if results exist
            available_todos = filtered_by_category
    
    # Apply priority filter
    if priority != "all":
        filtered_by_priority = [t for t in available_todos if t.get("priority", "").lower() == priority.lower()]
        if filtered_by_priority:  # Only apply filter if results exist
            available_todos = filtered_by_priority
    
    # If we have no todos after filtering, provide helpful message
    if not available_todos:
        return f"📋 No todos found for category '{category}' and priority '{priority}'.\n\nTry 'all' for category or priority to see more items."
    
    # Select 2-4 random todos from the filtered results
    num_to_show = min(len(available_todos), random.randint(2, 4))
    selected_todos = random.sample(available_todos, k=num_to_show)
    
    result = f"📋 Your Todo Items"
    if category != "all" or priority != "all":
        filters = []
        if category != "all":
            filters.append(f"category: {category}")
        if priority != "all":
            filters.append(f"priority: {priority}")
        result += f" ({', '.join(filters)})"
    result += ":\n\n"
    
    for i, todo in enumerate(selected_todos, 1):
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo["priority"], "⚪")
        result += f"{i}. {priority_emoji} {todo['task']}\n"
        result += f"   📅 Due: {todo['due']}\n"
        result += f"   ⏱️  Estimated: {todo['estimated_time']}\n"
        result += f"   📂 Category: {todo['category']}\n\n"
    
    return result


def get_traffic(destination: str, departure_time: str = "now") -> str:
    """
    Get current traffic conditions and travel time to a destination.
    
    OpenAI identifies traffic queries through keywords like:
    'traffic', 'drive', 'commute', 'travel time', 'route', 'directions'
    """
    # Select a random traffic scenario
    traffic_data = random.choice(TRAFFIC_RESPONSES)
    
    # Update destination if provided
    if destination:
        traffic_data["route"] = f"{destination} via optimal route"
    
    status_emoji = {
        "Normal flow": "🟢",
        "Light traffic": "🟡", 
        "Moderate delays": "🟠",
        "Heavy traffic": "🔴",
        "Heavy congestion": "🔴",
        "Severe delays": "🔴",
        "Weekend beach traffic": "🟠"
    }.get(traffic_data["status"], "⚪")
    
    return f"""🚗 Traffic Report - {traffic_data['route']}:
    
    {status_emoji} Status: {traffic_data['status']}
    ⏱️  Current Time: {traffic_data['current_time']} (normally {traffic_data['normal_time']})
    🚧 Incidents: {traffic_data['incidents']}
    💡 Alternative: {traffic_data['alternative']}
    
    Departure: {departure_time}"""