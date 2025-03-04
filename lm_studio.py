# lm_studio.py

import logging
import requests
import time

logger = logging.getLogger(__name__)

class LMStudioInterface:
    """
    Interface para LM Studio con un modelo GPT-like, 
    generando mensajes personalizados (reclutadores, cover letters, etc.).
    """

    def __init__(self, api_url="http://localhost:1234/v1"):
        self.api_url = api_url
        self.model = "qwen2.5-7b-instruct-1m"
        logger.info("LMStudioInterface inicializado con api_url=%s", self.api_url)

    def generate_message(self, prompt_template: str, context: dict) -> str:
        """
        Genera un mensaje usando LM Studio, inyectando variables de contexto (diccionario).
        """
        logger.info("Generando mensaje con LMStudio, prompt=%s", prompt_template)
        prompt = self._fill_template(prompt_template, context)

        endpoint = f"{self.api_url}/chat/completions"
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional job seeking assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        try:
            resp = requests.post(endpoint, json=data, timeout=30)
            if resp.status_code == 200:
                out = resp.json()
                return out["choices"][0]["message"]["content"]
            else:
                logger.error("Error en LMStudio: %d %s", resp.status_code, resp.text)
                return ""
        except Exception as e:
            logger.error("Excepción al llamar LMStudio: %s", e)
            return ""

    def _fill_template(self, template: str, context: dict) -> str:
        """
        Reemplaza llaves {var} en la plantilla con valores del contexto.
        """
        for k, v in context.items():
            template = template.replace(f"{{{k}}}", str(v))
        return template
