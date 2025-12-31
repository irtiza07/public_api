"""
Mock data for OpenAI Function Calling Tutorial

This module contains realistic mock response data for the three demo functions:
- Weather data with various global locations and conditions
- Todo items across different categories and priorities  
- Traffic scenarios from light to heavy congestion

Each function has 6-7 prepared responses that are randomly selected
to demonstrate OpenAI's tool selection capabilities.
"""

# =============================================================================
# WEATHER MOCK DATA - 7 realistic weather scenarios
# =============================================================================

WEATHER_RESPONSES = [
    {
        "location": "Paris, France",
        "temperature": 15,
        "condition": "Partly cloudy with light drizzle",
        "humidity": 78,
        "wind": "12 mph NW",
        "forecast": "Cloudy afternoon, clearing by evening"
    },
    {
        "location": "New York, USA",
        "temperature": 22,
        "condition": "Sunny and clear",
        "humidity": 45,
        "wind": "8 mph SW",
        "forecast": "Perfect weather continuing through the day"
    },
    {
        "location": "Tokyo, Japan",
        "temperature": 18,
        "condition": "Light rain showers",
        "humidity": 85,
        "wind": "15 mph E",
        "forecast": "Rain expected until late afternoon"
    },
    {
        "location": "London, UK",
        "temperature": 12,
        "condition": "Overcast with fog",
        "humidity": 82,
        "wind": "6 mph NE",
        "forecast": "Fog lifting by midday, then partly sunny"
    },
    {
        "location": "Sydney, Australia",
        "temperature": 24,
        "condition": "Warm and sunny",
        "humidity": 52,
        "wind": "10 mph S",
        "forecast": "Beautiful clear skies all day"
    },
    {
        "location": "Vancouver, Canada",
        "temperature": 8,
        "condition": "Cool with scattered clouds",
        "humidity": 71,
        "wind": "14 mph W",
        "forecast": "Cloudy morning, some sun breaks later"
    },
    {
        "location": "Default Location",
        "temperature": 20,
        "condition": "Pleasant and mild",
        "humidity": 60,
        "wind": "5 mph variable",
        "forecast": "Typical pleasant weather"
    }
]

# =============================================================================
# TODO MOCK DATA - 7 diverse task scenarios
# =============================================================================

TODO_RESPONSES = [
    {
        "task": "Team standup meeting",
        "priority": "high",
        "due": "9:00 AM",
        "category": "work",
        "estimated_time": "30 minutes"
    },
    {
        "task": "Complete quarterly project report",
        "priority": "high",
        "due": "End of week",
        "category": "work",
        "estimated_time": "3 hours"
    },
    {
        "task": "Grocery shopping for dinner party",
        "priority": "medium",
        "due": "This evening",
        "category": "personal",
        "estimated_time": "1 hour"
    },
    {
        "task": "Call mom about weekend plans",
        "priority": "medium",
        "due": "Today",
        "category": "family",
        "estimated_time": "20 minutes"
    },
    {
        "task": "Review and respond to emails",
        "priority": "medium",
        "due": "Before lunch",
        "category": "work",
        "estimated_time": "45 minutes"
    },
    {
        "task": "Schedule dentist appointment",
        "priority": "low",
        "due": "This week",
        "category": "health",
        "estimated_time": "10 minutes"
    },
    {
        "task": "Plan vacation itinerary",
        "priority": "low",
        "due": "Next month",
        "category": "travel",
        "estimated_time": "2 hours"
    }
]

# =============================================================================
# TRAFFIC MOCK DATA - 7 traffic condition scenarios
# =============================================================================

TRAFFIC_RESPONSES = [
    {
        "route": "Downtown via Highway 101",
        "current_time": "28 minutes",
        "normal_time": "18 minutes",
        "status": "Heavy traffic",
        "incidents": "Construction near Exit 15",
        "alternative": "Take Broadway for 5 minutes faster"
    },
    {
        "route": "Airport via I-95",
        "current_time": "35 minutes",
        "normal_time": "25 minutes",
        "status": "Moderate delays",
        "incidents": "Minor accident cleared, residual delays",
        "alternative": "Route 1 is clear and only 2 minutes longer"
    },
    {
        "route": "Shopping Center via Main Street",
        "current_time": "12 minutes",
        "normal_time": "10 minutes",
        "status": "Light traffic",
        "incidents": "No incidents reported",
        "alternative": "Oak Avenue is equally fast"
    },
    {
        "route": "University District via 5th Avenue",
        "current_time": "22 minutes",
        "normal_time": "15 minutes",
        "status": "Heavy congestion",
        "incidents": "School zone delays and road work",
        "alternative": "University Way bypass saves 8 minutes"
    },
    {
        "route": "Financial District via Downtown Core",
        "current_time": "45 minutes",
        "normal_time": "20 minutes",
        "status": "Severe delays",
        "incidents": "Multiple accidents and rush hour peak",
        "alternative": "Take the subway - much faster during rush hour"
    },
    {
        "route": "Suburbs via Residential Streets",
        "current_time": "15 minutes",
        "normal_time": "15 minutes",
        "status": "Normal flow",
        "incidents": "Clear roads",
        "alternative": "All routes similar, this is optimal"
    },
    {
        "route": "Beach Area via Coastal Highway",
        "current_time": "32 minutes",
        "normal_time": "25 minutes",
        "status": "Weekend beach traffic",
        "incidents": "Popular destination causing backups",
        "alternative": "Inland route adds 10 minutes but more predictable"
    }
]