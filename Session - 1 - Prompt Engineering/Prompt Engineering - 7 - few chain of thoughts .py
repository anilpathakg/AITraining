# Anil Pathak's Prompt Engineering : Example - 7: Few chain of thoughts
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

from openai import OpenAI
client = OpenAI()

prompt = """Example:
Q: If I have 2 apples and buy 3 more, how many apples total?
A: Let's think step by step. 2 + 3 = 5. Answer: 5 apples.

Now you solve:
Q: If I have 10 chocolates and eat 4, how many left?"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)
print(response.choices[0].message.content)
