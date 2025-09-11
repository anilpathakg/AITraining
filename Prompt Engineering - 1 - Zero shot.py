# Anil Pathak's Prompt Engineering : Example - 1: Zero Shot :
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

prompt = "Translate this sentence to Hindi: 'I love learning AI and Prompt Engineering .'"
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user", "content":prompt}]
)
print(response.choices[0].message.content)
