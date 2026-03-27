import os
import openai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
CBORG_API_URL = "https://api.cborg.lbl.gov/v1"

if not api_key:
    print("Error: OPENAI_API_KEY not found in .env")
    exit(1)

# Using the openai library (legacy or modern, the notebook uses legacy style)
# The notebook uses:
# import openai
# openai.api_key = api_key
# openai.api_base = CBORG_API_URL
# models = openai.Model.list()

# Let's try to use the modern client if possible, but let's stick to what works for a quick check.
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=CBORG_API_URL)
    models = client.models.list()
    print("Available CBORG Models:")
    for m in models.data:
        print(f" - {m.id}")
except ImportError:
    import openai
    openai.api_key = api_key
    openai.api_base = CBORG_API_URL
    try:
        models = openai.Model.list()
        print("Available CBORG Models:")
        for m in models['data']:
            print(f" - {m['id']}")
    except Exception as e:
        print(f"Legacy listing failed: {e}")
except Exception as e:
    print(f"Listing failed: {e}")
