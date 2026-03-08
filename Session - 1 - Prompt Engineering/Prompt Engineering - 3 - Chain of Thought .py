# Anil Pathak's Prompt Engineering : Example - 3: Chain of Thoughts:

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

prompt = "If a train travels 60 km in 1 hour, how far will it travel in 4 hours? Think step by step. Do not use LaTeX or math formatting, just plain text."
#prompt = "If a train travels 60 km in 1 hour, how far will it travel in 4 hours? Do not use LaTeX or math formatting, just plain text."

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)
print(response.choices[0].message.content)

