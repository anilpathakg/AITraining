# Anil Pathak's Prompt Engineering : Example - 2: Few Shot :
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from openai import OpenAI
client = OpenAI()

prompt = """Translate English to Hindi:
- English: Good morning → Hindi: सुप्रभात
- English: How are you? → French: आप कैसे हैं?
- English: I love learning AI and prompt engineering  → मुझे एआई और प्रॉम्प्ट इंजीनियरिंग सीखना बहुत पसंद है :"""

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}]
)
print(response.choices[0].message.content)
