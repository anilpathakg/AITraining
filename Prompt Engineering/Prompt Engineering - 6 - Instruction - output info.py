# Anil Pathak's Prompt Engineering : Example - 6: Insutcion + output info :
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

from openai import OpenAI
client = OpenAI()

prompt = """
Extract the following info from text and return it in JSON format:
- Name
- Age
- City

Text: My name is Anil Pathak, I am 49 years old, and I live in Noida.
"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}],
    response_format={ "type":"json_object" }
)

print(response.choices[0].message.content)

