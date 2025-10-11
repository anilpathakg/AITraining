# Anil Pathak's Prompt Engineering : Example - 5: Role Prompting:

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

#prompt = "You are a Doctor. Explain critcal operation to a beginner with an example."
#response = client.chat.completions.create(
#    model="gpt-4o-mini",
#    messages=[{"role":"system","content":"You are a doctor"},
#              {"role":"user","content":"Explain operation with an example."}]
#)
#print(response.choices[0].message.content)

prompt = "You are a Police Officer. Explain critcal operation to a beginner with an example."
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"system","content":"You are a police officer"},
              {"role":"user","content":"Explain operation with an example."}]
)

print(response.choices[0].message.content)
