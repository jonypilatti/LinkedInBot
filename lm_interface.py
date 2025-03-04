import requests
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LMStudioInterface:
    def __init__(self, api_url="http://localhost:1234/v1"):
        self.api_url = api_url

    def generate_message(self, prompt, context, retries=3):
        """Genera un mensaje usando LM Studio con reintentos en caso de error."""
        for attempt in range(retries):
            try:
                payload = {"prompt": prompt, "context": context}
                response = requests.post(f"{self.api_url}/generate", json=payload, timeout=10)
                response.raise_for_status()
                return response.json().get("message", "Error en la generación del mensaje.")
            except requests.RequestException as e:
                logger.error(f"Error en LM Studio (Intento {attempt+1}/{retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff para reintentar
        return "Error en la generación del mensaje después de varios intentos."
    
    def check_connection(self):
        """Verifica si LM Studio está disponible antes de usarlo."""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            logger.error("LM Studio no está disponible. Asegúrate de que esté ejecutándose.")
            return False
