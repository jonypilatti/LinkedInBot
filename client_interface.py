import os
import json
import logging
import colorama
from colorama import Fore, Style
from linkedin_api import LinkedInAPI
from lm_studio import LMStudioInterface
from bot import LinkedInBot
from gui import LinkedInGUI

def main():
    """Inicializa el bot de LinkedIn y la interfaz gráfica."""
    colorama.init()  # Inicializa colorama en Windows para logs en color
    
    logging.basicConfig(
        level=logging.INFO,
        format=f"{Fore.GREEN}%(asctime)s{Style.RESET_ALL} - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info("Iniciando LinkedIn Job Search Bot...")

    config_file = "config.json"
    if not os.path.exists(config_file):
        logger.error("No se encontró config.json. Asegúrate de que el archivo existe y contiene la configuración necesaria.")
        return

    with open(config_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    linkedin_cfg = cfg.get("linkedin", {})
    lm_cfg = cfg.get("lm_studio", {})
    retry_cfg = cfg.get("retry_policy", {})

    max_tries = retry_cfg.get("max_tries", 5)
    base_delay = retry_cfg.get("base_delay", 2.0)

    # Inicializar LinkedIn API
    linkedin_api = LinkedInAPI(
        client_id=linkedin_cfg.get("client_id", ""),
        client_secret=linkedin_cfg.get("client_secret", ""),
        redirect_uri=linkedin_cfg.get("redirect_uri", ""),
        max_tries=max_tries,
        base_delay=base_delay
    )

    # Inicializar LM Studio API
    lm_studio = LMStudioInterface(api_url=lm_cfg.get("api_url", "http://localhost:1234/v1"))
    
    # Crear instancia del bot
    bot = LinkedInBot(linkedin_api, lm_studio)
    
    # Lanzar la GUI
    LinkedInGUI(bot)

if __name__ == "__main__":
    main()