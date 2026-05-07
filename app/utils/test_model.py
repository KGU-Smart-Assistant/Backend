import os

from dotenv import load_dotenv
from google import genai


def main() -> None:
    load_dotenv()
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    print("--- Available models ---")
    try:
        for model in client.models.list():
            if "generateContent" in model.supported_methods:
                print(f"Model: {model.name}")
    except Exception:
        print("Falling back to full model list")
        for model in client.models.list():
            print(f"Model: {model.name}")


if __name__ == "__main__":
    main()
