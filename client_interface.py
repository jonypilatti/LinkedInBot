"""
LinkedIn Job Search Bot with LM Studio Integration (Refactored)
---------------------------------------------------------------
This refactored version replaces direct requests calls with the python3-linkedin library,
reducing manual handling of OAuth tokens. It also removes the custom _make_request method
in favor of library calls wherever possible.
"""
import os
import json
import time
import logging
import requests
from typing import List, Dict

from linkedin import linkedin  # python3-linkedin

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("linkedin_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInAPI:
    """Interface para interacciones con la API de LinkedIn usando exclusivamente el cliente python3‑linkedin para OAuth y REST para funcionalidades no soportadas."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        logger.info("Inicializando LinkedInAPI con client_id=%s, redirect_uri=%s", client_id, redirect_uri)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # Permisos requeridos
        self.permissions = ['r_liteprofile', 'r_emailaddress', 'w_member_social']
        self.authentication = linkedin.LinkedInAuthentication(
            self.client_id,
            self.client_secret,
            self.redirect_uri,
            self.permissions
        )

        self.access_token = None
        self.application = None  # Se utiliza para llamadas soportadas por el cliente.
        self.base_url = "https://api.linkedin.com/v2"  # Base URL para llamadas REST manuales.

    def authenticate(self, auth_code: str = None) -> bool:
        if auth_code:
            logger.info("Autenticando con LinkedIn usando auth_code=%s", auth_code)
            try:
                self.authentication.authorization_code = auth_code
                token = self.authentication.get_access_token()
                self.access_token = token.access_token
                expires_in = token.expires_in  # en segundos
                expires_at = time.time() + expires_in
                token_data = {"access_token": self.access_token, "expires_at": expires_at}
                self._save_token(token_data)
                self.application = linkedin.LinkedInApplication(token=self.access_token)
                return True
            except Exception as e:
                logger.error("Fallo en la autenticación: %s", e)
                return False
        else:
            logger.info("No se proporcionó auth_code, intentando cargar token existente.")
            if self._load_token() and self.access_token:
                self.application = linkedin.LinkedInApplication(token=self.access_token)
                return True
            else:
                logger.warning("No se pudo cargar el token o ha expirado.")
                return False

    def _save_token(self, token_data: Dict) -> None:
        logger.info("Guardando token en linkedin_token.json")
        with open("linkedin_token.json", "w") as f:
            json.dump(token_data, f)

    def _load_token(self) -> bool:
        try:
            with open("linkedin_token.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at", 0)
                if time.time() > expires_at:
                    logger.warning("El token de acceso ha expirado.")
                    return False
                logger.info("Token cargado exitosamente, access_token=%s", self.access_token)
                return True
        except Exception as e:
            logger.error("Error al cargar token: %s", e)
            return False

    def get_current_user_profile(self) -> Dict:
        try:
            # Se usa el método del cliente para obtener el perfil
            profile = self.application.get_profile(selectors=['id', 'first-name', 'last-name', 'email-address'])
            logger.info("Perfil de usuario obtenido: %s", profile)
            return profile
        except Exception as e:
            logger.error("Error al obtener el perfil: %s", e)
            return {"error": str(e), "status": "error"}

    def get_user_connections(self) -> List[Dict]:
        try:
            connections = self.application.get_connections()
            logger.info("Conexiones obtenidas: %s", connections)
            return connections
        except Exception as e:
            logger.error("Error al obtener conexiones: %s", e)
            return []

    def send_message(self, recipient_id: str, message: str) -> bool:
        try:
            # Se asume que el método send_message está disponible en el cliente python3‑linkedin.
            response = self.application.send_message(recipients=[recipient_id], message=message)
            logger.info("Mensaje enviado exitosamente: %s", response)
            return True
        except Exception as e:
            logger.error("Error al enviar mensaje: %s", e)
            return False

    def search_jobs(self, keywords: List[str], location: str = "", easy_apply_only: bool = True) -> List[Dict]:
        """
        Función para buscar empleos usando una llamada REST al endpoint de búsqueda de empleos.
        NOTA: Este endpoint puede requerir permisos especiales y está sujeto a cambios en la API de LinkedIn.
        """
        logger.info("Buscando empleos con keywords=%s, location=%s, easy_apply_only=%s", keywords, location, easy_apply_only)
        url = f"{self.base_url}/job-search"
        params = {
            "keywords": ",".join(keywords),
            "location": location,
            "easy_apply": str(easy_apply_only).lower()
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                jobs = resp.json().get("elements", [])
                logger.info("Empleos encontrados: %d", len(jobs))
                return jobs
            else:
                logger.error("Error en búsqueda de empleos: %d - %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logger.error("Excepción en búsqueda de empleos: %s", e)
            return []

    def apply_to_job(self, job_id: str, resume_id: str = None) -> bool:
        """
        Función para aplicar a un empleo usando una llamada REST.
        NOTA: Este endpoint puede requerir permisos especiales (Talent Solutions) y no estar disponible para todas las aplicaciones.
        """
        logger.info("Aplicando a empleo con job_id=%s, resume_id=%s", job_id, resume_id)
        url = f"{self.base_url}/jobs/{job_id}/applications"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {}
        if resume_id:
            data["resume"] = {"id": resume_id}
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if 200 <= resp.status_code < 300:
                logger.info("Aplicación enviada exitosamente.")
                return True
            else:
                logger.error("Fallo al aplicar al empleo: %d - %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Excepción al aplicar al empleo: %s", e)
            return False

class LMStudioInterface:
    """Interface for LM Studio with QWEN (or other) model"""

    def __init__(self, api_url: str = "http://localhost:1234/v1"):
        """Initialize LM Studio interface"""
        logger.info("Initializing LMStudioInterface with api_url=%s", api_url)
        self.api_url = api_url
        self.model = "qwen2.5-7b-instruct-1m"  # Example or your actual QWEN model

    def generate_message(self, prompt_template: str, context: Dict) -> str:
        """
        Generate a message using LM Studio.
        Fill prompt_template with context, then POST to the LM Studio chat/completions endpoint.
        """
        logger.info("Generating message using LMStudio with prompt_template=%s, context=%s", prompt_template, context)
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
            response = requests.post(endpoint, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error("LM Studio request failed: %s - %s", response.status_code, response.text)
                return ""
        except Exception as e:
            logger.error("Error calling LM Studio: %s", e)
            return ""

    def _fill_template(self, template: str, context: Dict) -> str:
        """Fill template placeholders with the given context keys."""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


class LinkedInBot:
    """
    Main bot class that coordinates LinkedIn API and LM Studio
    for contacting recruiters and applying to jobs.
    """

    def __init__(self, linkedin_api: LinkedInAPI, lm_studio: LMStudioInterface):
        logger.info("Initializing LinkedInBot...")
        self.linkedin = linkedin_api
        self.lm_studio = lm_studio
        self.user_profile = None

        # Template for contacting recruiters
        self.recruiter_message_template = """
Hello {recruiter_name},

I noticed you're a {recruiter_title} at {recruiter_company}. I'm currently exploring new opportunities as a Full Stack Engineer with expertise in {skills}.

{personalized_note}

I'd appreciate the opportunity to discuss how my skills might align with roles you're currently hiring for.

Best regards,
{user_name}
        """

        # Initialize and authenticate if a saved token exists
        self._initialize()

    def _initialize(self) -> None:
        """Attempt to load an existing token and fetch user profile."""
        logger.info("Attempting LinkedIn authentication in LinkedInBot._initialize()...")
        if self.linkedin.authenticate():
            logger.info("Successfully authenticated with LinkedIn, fetching user profile...")
            self.user_profile = self.linkedin.get_current_user_profile()
            logger.info("User profile loaded: %s", self.user_profile)
        else:
            logger.error("Failed to authenticate with LinkedIn. Provide a new code or check config.")

    def contact_recruiters(self, skills: str = "NextJS/Python with FastAPI or NodeJS+ExpressJS") -> Dict:
        """Contact recruiters in your connections."""
        logger.info("Starting contact_recruiters with skills=%s", skills)
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        recruiters = self.linkedin.filter_recruiter_connections(exclude_company="Stori")
        logger.info("Found %d potential recruiter connections", len(recruiters))

        # Attempt to get user name from profile
        user_first = self.user_profile.get('firstName', '') if isinstance(self.user_profile, dict) else ''
        user_last = self.user_profile.get('lastName', '') if isinstance(self.user_profile, dict) else ''

        for recruiter in recruiters:
            # Prepare context
            recruiter_first = recruiter.get("firstName", "")
            recruiter_title = recruiter.get("title", "Recruiter")
            recruiter_company = recruiter.get("company", {}).get("name", "your company")

            context = {
                "recruiter_name": recruiter_first,
                "recruiter_title": recruiter_title,
                "recruiter_company": recruiter_company,
                "skills": skills,
                "user_name": f"{user_first} {user_last}"
            }

            # Generate a short personalized note
            personalization_prompt = (
                f"Generate a brief, professional, personalized note for a recruiter named {recruiter_first} "
                f"who works at {recruiter_company} as a {recruiter_title}. "
                f"The note should be 1-2 sentences explaining why I'm interested in potential opportunities."
            )
            logger.debug("Generating personalized note for recruiter=%s", recruiter_first)
            personalized_note = self.lm_studio.generate_message(personalization_prompt, {})
            context["personalized_note"] = personalized_note.strip()

            # Fill the recruiter message template
            message = self._fill_template(self.recruiter_message_template, context)

            # Send
            recruiter_id = recruiter.get("id", "")
            if not recruiter_id:
                logger.warning("No recruiter_id found, skipping.")
                results["skipped"] += 1
                continue

            logger.info("Sending message to recruiter=%s at company=%s", recruiter_first, recruiter_company)
            success = self.linkedin.send_message(recruiter_id, message)
            result = {
                "recruiter": f"{recruiter_first} {recruiter.get('lastName', '')}",
                "company": recruiter_company,
                "message": message,
                "success": success
            }
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
            results["details"].append(result)

        return results

    def search_and_apply_jobs(
        self,
        keywords: List[str],
        location: str = "",
        max_jobs: int = 20,
        easy_apply_only: bool = True
    ) -> Dict:
        """
        Search for jobs on LinkedIn, optionally apply to them using easy apply.
        """
        logger.info("Starting search_and_apply_jobs with keywords=%s, location=%s, max_jobs=%d, easy_apply_only=%s",
                    keywords, location, max_jobs, easy_apply_only)
        results = {
            "searched_jobs": 0,
            "applied": 0,
            "failed": 0,
            "details": []
        }
        jobs = self.linkedin.search_jobs(keywords, location, easy_apply_only)
        results["searched_jobs"] = len(jobs)

        # Just iterate through jobs up to max_jobs
        for job in jobs[:max_jobs]:
            job_id = job.get("id")
            if not job_id:
                logger.warning("No job ID found in listing, skipping.")
                continue

            logger.info("Applying to job_id=%s", job_id)
            success = self.linkedin.apply_to_job(job_id)
            job_result = {
                "job_id": job_id,
                "success": success
            }
            if success:
                results["applied"] += 1
            else:
                results["failed"] += 1
            results["details"].append(job_result)

        return results

    def _fill_template(self, template: str, context: Dict) -> str:
        """Helper to fill in placeholders in the message template."""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template.strip()

