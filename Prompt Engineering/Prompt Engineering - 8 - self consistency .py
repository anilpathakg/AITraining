# Anil Pathak's Prompt Engineering : Example - 8: Self Consistency
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

question = "If a pen costs 10 rupees, how much do 5 pens cost? Think step by step. Do not use LaTeX or math formatting, just plain text."

answers = []

# Ask multiple times
for i in range(2):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":question}],
        temperature=1.0  # randomness ON
    )
    ans = response.choices[0].message.content
    answers.append(ans)

print("=== Different Reasoning Paths ===")
for idx, ans in enumerate(answers, 1):
    print(f"\nAttempt {idx}:\n{ans}")
