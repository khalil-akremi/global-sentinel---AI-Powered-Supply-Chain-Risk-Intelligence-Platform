import requests
import os
from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
)

models = response.json()["data"]
# Affiche les modèles gratuits Mistral
mistral = [m["id"] for m in models if "mistral" in m["id"].lower()]
print("Modèles Mistral disponibles:")
for m in mistral:
    print(f"  {m}")