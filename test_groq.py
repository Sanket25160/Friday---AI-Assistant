from config import GROQ_API_KEY
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)

print("Testing Groq API...")

try:
    models = client.models.list()

    print("\nAVAILABLE MODELS:\n")

    for model in models.data:
        print(model.id)

except Exception as e:
    print("\nERROR:")
    print(type(e).__name__)
    print(e)