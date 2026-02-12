import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"✅ Success! Key loaded: {key[:10]}...")
else:
    print("❌ Error: Key not loaded.")
