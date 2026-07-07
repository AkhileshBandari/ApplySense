import os
import logging
import requests
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class AIFallbackManager:
    """Manage fallback between multiple LLM providers.

    The manager attempts to generate content using the providers in the
    order defined by ``self.providers``.  Each provider requires its API key to
    be present in Django settings.  If a provider fails, the error is logged
    and the next provider is tried.  If all providers fail, a ``RuntimeError``
    containing the aggregated error messages is raised.
    """

    def __init__(self):
        # Read keys from settings
        self.openai_key = getattr(settings, "OPENAI_API_KEY", "")
        self.groq_key = getattr(settings, "GROQ_API_KEY", "")
        self.openrouter_key = getattr(settings, "OPENROUTER_API_KEY", "")
        self.hf_key = getattr(settings, "HUGGINGFACE_API_KEY", "")

        # Priority order for fallback
        self.providers = ["openai", "groq", "openrouter", "huggingface"]

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format_json: bool = False,
    ) -> str:
        """Generate content using the configured providers.

        Args:
            system_prompt: The system‑level instruction for the model.
            user_prompt: The user‑provided prompt.
            response_format_json: If ``True`` the model should return JSON.

        Returns:
            The generated text from the first successful provider.
        """
        errors = []
        for provider in self.providers:
            try:
                logger.info(f"Attempting content generation with provider: {provider}")
                result = None

                if provider == "openai" and self.openai_key:
                    result = self._call_openai(system_prompt, user_prompt, response_format_json)
                elif provider == "groq" and self.groq_key:
                    result = self._call_groq(system_prompt, user_prompt, response_format_json)
                elif provider == "openrouter" and self.openrouter_key:
                    result = self._call_openrouter(system_prompt, user_prompt, response_format_json)
                elif provider == "huggingface" and self.hf_key:
                    result = self._call_huggingface(system_prompt, user_prompt)

                if result:
                    logger.info(f"Successful content generation using provider: {provider}")
                    return result
                else:
                    errors.append(f"{provider}: API key not configured or returned empty")
            except Exception as e:
                err_msg = f"{provider}: {e}"
                errors.append(err_msg)
                logger.error(err_msg)
        raise RuntimeError("All providers failed: " + "; ".join(errors))

    # Placeholder methods for each provider – to be implemented later
    def _call_openai(self, system_prompt, user_prompt, json_format):
        raise NotImplementedError

    def _call_groq(self, system_prompt, user_prompt, json_format):
        raise NotImplementedError

    def _call_openrouter(self, system_prompt, user_prompt, json_format):
        raise NotImplementedError

    def _call_huggingface(self, system_prompt, user_prompt):
        raise NotImplementedError