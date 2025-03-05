def get_current_weather(location, format):
    # In a real application, you would make an API call to a weather service
    # For this example, we'll return mock data
    temperature = 25 if format == "celsius" else 77  # Mock temperature
    return {
        "location": location,
        "temperature": temperature,
        "unit": format,
        "condition": "sunny"
    }