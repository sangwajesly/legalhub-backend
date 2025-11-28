"""Quick script to test the Gemini adapter locally.

Usage:
  python scripts/test_gemini.py

It reads configuration from `app.config.settings` (and `.env` if present).
"""
import asyncio

from app.config import settings
from app.services.gemini_service import send_message, stream_send_message


async def main():
    # For quick local debugging you can enable mock mode here, but prefer
    # setting DEBUG_MOCK_GEMINI in your .env so behavior matches runtime.
    # settings.DEBUG_MOCK_GEMINI = True

    prompt = "Explain the concept of 'due process' in simple language."

    print("=== Single (non-stream) call ===")
    res = await send_message(prompt)
    print("response:", res.get("response"))
    print("raw:", res.get("raw"))

    print("\n=== Streaming call ===")
    async for chunk in stream_send_message(prompt):
        # chunk is a dict with keys 'model', 'response', 'raw'
        print('chunk:', chunk.get('response'))


if __name__ == '__main__':
    asyncio.run(main())