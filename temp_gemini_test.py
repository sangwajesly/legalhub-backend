import asyncio
from app.services import gemini_service
from app.config import settings
import os
from dotenv import load_dotenv  # Import load_dotenv

# Explicitly load environment variables from .env file
load_dotenv()

# Re-instantiate the Settings class to reload from .env after loading it
settings = settings.__class__()

# Explicitly set GEMINI_MODEL for this test
settings.GEMINI_MODEL = "gemini-pro"


async def main():
    print(
        f"DEBUG_MOCK_GEMINI (from settings object) is set to: {settings.DEBUG_MOCK_GEMINI}"
    )
    print(f"GEMINI_MODEL is set to: {settings.GEMINI_MODEL}")
    print(f"GOOGLE_API_KEY is set: {bool(settings.GOOGLE_API_KEY)}")
    print(f"GEMINI_API_URL is set: {bool(settings.GEMINI_API_URL)}")

    # Also check environment variable directly
    debug_mock_env = os.getenv("DEBUG_MOCK_GEMINI")
    print(f"DEBUG_MOCK_GEMINI (from OS environment) is set to: {debug_mock_env}")

    prompt = "What is the capital of France?"
    print(f"\nSending prompt: '{prompt}' to Gemini service...")

    try:
        response = await gemini_service.send_message(prompt)
        print("\nGemini Response:")
        print(f"Model: {response.get('model')}")
        print(f"Response Text: {response.get('response')}")
        print(f"Raw Response: {response.get('raw')}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
