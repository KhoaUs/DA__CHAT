import requests
import os
key = os.getenv("GOOGLE_API_KEY") or "YOUR_API_KEY"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
r = requests.get(url, timeout=20)
r.raise_for_status()
print(r.json())