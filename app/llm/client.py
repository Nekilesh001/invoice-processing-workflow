import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from openai import OpenAI, APIError, AuthenticationError

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenAI-compatible client wrapper for LLM invoice extraction and agentic tool calling.
    Compatible with GLM-4, OpenAI GPT, and any OpenAI API-compatible provider.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        prompt_path: Optional[Path] = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model = model or settings.LLM_MODEL
        self.prompt_path = prompt_path or (
            settings.BASE_DIR / "app" / "prompts" / "invoice_extraction_v1.txt"
        )
        self.system_prompt = self._load_system_prompt()
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """Lazy initialization of OpenAI-compatible client."""
        if not self.api_key or self.api_key == "your_api_key_here" or self.api_key == "dummy_key_until_configured":
            raise ValueError(
                "LLM API Key is not configured. Please set LLM_API_KEY in your .env file."
            )

        if self._client is None:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _load_system_prompt(self) -> str:
        """Reads system prompt file from disk."""
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"System prompt file missing: {self.prompt_path}")
        return self.prompt_path.read_text(encoding="utf-8")

    def extract_invoice_json(self, document_text: str) -> Dict[str, Any]:
        """
        Sends extracted document text to the LLM and requests structured JSON output.
        Returns parsed dictionary matching ExtractedInvoice schema.
        """
        client = self._get_client()

        user_content = f"Extracted Document Text:\n```text\n{document_text}\n```"

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("LLM returned empty response content.")

            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

            return json.loads(cleaned_content)

        except AuthenticationError as e:
            logger.error("LLM Authentication failed: %s", str(e))
            raise RuntimeError(f"LLM API Authentication failed: {str(e)}") from e
        except APIError as e:
            logger.error("LLM API Error: %s", str(e))
            raise RuntimeError(f"LLM API request failed: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response: %s", str(e))
            raise ValueError(f"LLM output is not valid JSON: {str(e)}") from e

    def chat_completion_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> Any:
        """
        Executes OpenAI chat completion call supplying function/tool specs.
        Returns response message choice object (which may contain tool_calls or content).
        """
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.0,
            )
            return response.choices[0].message
        except AuthenticationError as e:
            logger.error("LLM Tool Authentication failed: %s", str(e))
            raise RuntimeError(f"LLM API Authentication failed: {str(e)}") from e
        except APIError as e:
            logger.error("LLM Tool API Error: %s", str(e))
            raise RuntimeError(f"LLM API request failed: {str(e)}") from e
