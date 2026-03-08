# Anil Pathak's Prompt Engineering : Example - 4: React:

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

prompt = """You are a helpful assistant.
Question: What is the color of Apple? Give another fuit name with same color
Think step by step and if needed, say 'Search[...]' before answering."""


response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)
print(response.choices[0].message.content)
