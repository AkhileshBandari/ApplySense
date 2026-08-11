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

    def _call_openai(self, system_prompt, user_prompt, json_format):
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        if json_format:
            data["response_format"] = {"type": "json_object"}
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _call_groq(self, system_prompt, user_prompt, json_format):
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        if json_format:
            data["response_format"] = {"type": "json_object"}
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _call_openrouter(self, system_prompt, user_prompt, json_format):
        headers = {"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"}
        data = {
            "model": "openrouter/auto",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        if json_format:
            data["response_format"] = {"type": "json_object"}
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

    def _call_huggingface(self, system_prompt, user_prompt):
        headers = {"Authorization": f"Bearer {self.hf_key}", "Content-Type": "application/json"}
        prompt = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 1024, "return_full_text": False}
        }
        res = requests.post("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2", headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()[0]["generated_text"]