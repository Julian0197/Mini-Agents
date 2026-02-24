"""Mini-Agents Unified LLM Interface - Based on OpenAI API

API design (LangChain-style):
- invoke(messages, **kwargs) -> str          One-shot, returns full response. Use when you need the complete string (e.g. parsing, history).
- stream(messages, **kwargs) -> Iterator[str] Streaming, yields chunks. Use for live display or token-by-token handling.
- stream_invoke(messages, **kwargs) -> Iterator[str] Alias for the stream() method. Kept for backward compatibility.
"""

import os
from typing import Optional, Iterator
from openai import OpenAI
from .exceptions import MiniAgentsException

class MiniAgentsLLM:
    """
    LLM client built for MiniAgents.
    Configured via three environment variables: LLM_MODEL_ID, LLM_API_KEY, LLM_BASE_URL.

    Design principles:
    - Read configuration from environment variables
    - Two call styles: invoke() for full string, stream()/think() for streaming (LangChain-style)
    - Compatible with any OpenAI-format API service
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
    ):
        """
        Initialize the client. Parameters take priority; falls back to environment variables.

        Args:
            model: Model name, defaults to LLM_MODEL_ID
            api_key: API key, defaults to LLM_API_KEY
            base_url: Service endpoint, defaults to LLM_BASE_URL
            temperature: Temperature parameter
            max_tokens: Maximum number of tokens
            timeout: Request timeout in seconds
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Validate required parameters
        if not all([self.model, self.api_key, self.base_url]):
            raise MiniAgentsException("Please set required parameters in .env")

        self._client = self._create_client()

    def _create_client(self) -> OpenAI:
        """Create OpenAI client"""
        return OpenAI(
            api_key=self.api_key, base_url=self.base_url, timeout=self.timeout
        )

    def stream(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        Streaming LLM call. Returns the response as a stream of chunks.
        Suitable for scenarios where streaming output is needed.
        """
        print(f"🧠【[LLM] calling {self.model}")
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True,
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            # process streaming response
            print("[LLM] Response received:")
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                if content:
                    print(content, end="", flush=True)
                    yield content
            print() # print a new line
            
        except Exception as e:
            print(f"[LLM] Error calling LLM API: {e}")
            raise BaseException(f"LLM call failed: {str(e)}")

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        Non-streaming LLM call. Returns the complete response at once.
        Suitable for scenarios where streaming output is not needed.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM] Error calling LLM API: {e}")
            raise BaseException(f"LLM call failed: {str(e)}")

    def stream_invoke(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        """
        Alias for the think() method. Kept for backward compatibility.
        """
        temperature = kwargs.get("temperature", self.temperature)
        yield from self.stream(messages, temperature=temperature)
