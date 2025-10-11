# Anil Pathak's weather interactive BOT : This demonstartes the Prompt Engineeing : Function calling

#This section is to import various packages
import os
import json
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Weather API function
def get_weather(location, unit="celsius"):
    units = "metric" if unit == "celsius" else "imperial"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units={units}"
    response = requests.get(url)

    if response.status_code != 200:
        return f"Sorry, I couldn't fetch the weather for {location}."

    data = response.json()
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"].capitalize()
    return f"{temp}°{'C' if unit=='celsius' else 'F'}, {description}"

# Define function schema
functions = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a given city",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
            },
            "required": ["location"]
        }
    }
]

while True:
    user_query = input("\nAnil's Weather BOT: Ask about weather (or type 'exit' to quit): ")
    if user_query.lower() == "exit":
        break

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_query}],
        functions=functions,
        function_call="auto"
    )

    message = response.choices[0].message
    
    if message.function_call:
        function_name = message.function_call.name
        arguments = json.loads(message.function_call.arguments)

        if function_name == "get_weather":
            result = get_weather(**arguments)
          
            second_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": None, "function_call": message.function_call},
                    {"role": "function", "name": function_name, "content": result}
                ]
            )
            print("Assistant:", second_response.choices[0].message.content)
    else:
        print("Assistant:", message.content)
