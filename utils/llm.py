import os
from google import genai
from google.genai import types


class _GeminiWrapper:
    """Thin wrapper so agents keep the same `.invoke(messages)` call signature."""

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def invoke(self, messages) -> object:
        # Accept a list of LangChain-style messages or a plain string
        if isinstance(messages, list):
            content = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
        else:
            content = str(messages)

        response = self._client.models.generate_content(
            model="gemini-2.0-flash",
            contents=content,
        )
        return type("Resp", (), {"content": response.text})()


def get_llm():
    """
    Returns a Gemini wrapper if an API key is set, else None.
    All agents have fallbacks for the None case.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        return _GeminiWrapper(api_key=api_key)
    except Exception:
        return None
