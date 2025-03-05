import os
import requests
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LMStudioInterface:
    def __init__(self, api_url: str = None, timeout: int = None, retries: int = None):
        # Se leen las variables de entorno si los parámetros no fueron pasados.
        self.api_url = api_url or os.environ.get("LM_API_URL", "http://localhost:1234/v1")
        self.timeout = timeout if timeout is not None else int(os.environ.get("LM_TIMEOUT", "10"))
        self.retries = retries if retries is not None else int(os.environ.get("LM_RETRIES", "3"))

    def generate_message(self, prompt: str, context: dict) -> str:
        """
        Genera un mensaje usando LM Studio.
        Valida la respuesta y realiza reintentos en caso de error.
        """
        payload = {"prompt": prompt, "context": context}
        for attempt in range(self.retries):
            try:
                response = requests.post(f"{self.api_url}/generate", json=payload, timeout=self.timeout)
                response.raise_for_status()
                json_response = response.json()
                if isinstance(json_response, dict) and "message" in json_response:
                    return json_response["message"]
                else:
                    logger.error(f"Respuesta inesperada de LM Studio: {json_response}")
            except requests.RequestException as e:
                logger.error(f"Error en LM Studio (Intento {attempt+1}/{self.retries}): {e}")
            time.sleep(2 ** attempt)
        return "Error en la generación del mensaje después de varios intentos."
    
    def check_connection(self) -> bool:
        """
        Verifica si LM Studio está disponible.
        """
        try:
            response = requests.get(f"{self.api_url}/status", timeout=self.timeout)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"LM Studio respondió con estado {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"LM Studio no está disponible: {e}")
        return False
