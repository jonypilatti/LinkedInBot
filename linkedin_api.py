# linkedin_api.py

import os
import time
import json
import logging
import requests
import backoff
from linkedin import linkedin  # python3-linkedin

logger = logging.getLogger(__name__)

class LinkedInAPI:
    """
    Interfaz para la API de LinkedIn que combina python3‑linkedin para autenticación
    y llamadas REST adicionales para funciones no soportadas por el cliente.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,max_tries=5, base_delay=2.0):

        logger.info("Inicializando LinkedInAPI con client_id=%s", client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.max_tries = max_tries
        self.base_delay = base_delay

        self.permissions = ['r_liteprofile', 'r_emailaddress', 'w_member_social']
        self.authentication = linkedin.LinkedInAuthentication(
            self.client_id, self.client_secret, self.redirect_uri, self.permissions
        )

        self.access_token = None
        self.application = None
        self.base_url = "https://api.linkedin.com/v2"

    def authenticate(self, auth_code: str = None) -> bool:
        """
        Autentica con LinkedIn, ya sea recibiendo un auth_code nuevo o cargando uno previo
        desde linkedin_token.json. Retorna True si es exitoso.
        """
        if auth_code:
            logger.info("Autenticando con LinkedIn usando auth_code=%s", auth_code)
            try:
                self.authentication.authorization_code = auth_code
                token = self.authentication.get_access_token()
                self.access_token = token.access_token
                expires_in = token.expires_in
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

    def _save_token(self, token_data: dict):
        logger.info("Guardando token en linkedin_token.json")
        with open("linkedin_token.json", "w") as f:
            json.dump(token_data, f)

    def _load_token(self) -> bool:
        """
        Carga token de linkedin_token.json e informa si es válido.
        """
        try:
            with open("linkedin_token.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at", 0)
                if time.time() > expires_at:
                    logger.warning("El token de acceso ha expirado.")
                    return False
                logger.info("Token cargado exitosamente.")
                return True
        except Exception as e:
            logger.error("Error al cargar token: %s", e)
            return False

    def get_profile(self):
        """Obtiene el perfil del usuario autenticado usando la aplicación de python3-linkedin."""
        if not self.application:
            return {}
        try:
            return self.application.get_profile(
                selectors=['id', 'first-name', 'last-name', 'email-address']
            )
        except Exception as e:
            logger.error("Error al obtener perfil: %s", e)
            return {}

    def get_connections(self):
        """Retorna conexiones del usuario autenticado."""
        if not self.application:
            return []
        try:
            return self.application.get_connections()
        except Exception as e:
            logger.error("Error al obtener conexiones: %s", e)
            return []

    def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Envía un mensaje a un contacto. python3-linkedin no siempre implementa send_message,
        pero se asume que la versión usada lo soporta.
        """
        if not self.application:
            return False
        try:
            resp = self.application.send_message(recipients=[recipient_id], message=message)
            logger.info("Mensaje enviado: %s", resp)
            return True
        except Exception as e:
            logger.error("Error al enviar mensaje: %s", e)
            return False

    @backoff.on_exception(
        backoff.expo,  # Función exponencial
        requests.exceptions.RequestException,
        max_tries=lambda self: self.max_tries,   # Obtenido del init
        factor=lambda self: self.base_delay )
    def search_jobs(self, keywords, location="", easy_apply_only=True):
        """
        Hace una llamada REST a /job-search, manejando reintentos automáticos con @backoff.
        Maneja manualmente la respuesta 429 (rate limit).
        """
        logger.info("Buscando empleos con keywords=%s, location=%s", keywords, location)
        url = f"{self.base_url}/job-search"
        params = {
            "keywords": ",".join(keywords),
            "location": location,
            "easy_apply": str(easy_apply_only).lower()
        }
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 429:
            logger.warning("Rate Limit Excedido (429). Esperando 60s antes de continuar.")
            time.sleep(60)
            return []
        if resp.status_code == 200:
            return resp.json().get("elements", [])
        logger.error("Error en job-search: %d %s", resp.status_code, resp.text)
        return []
        pass

    def apply_to_job(self, job_id: str, resume_id: str = None):
        """
        Aplica a un empleo. Requiere permisos Talent Solutions. Maneja rate limit (429).
        """
        logger.info("Aplicando a job_id=%s", job_id)
        url = f"{self.base_url}/jobs/{job_id}/applications"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        data = {}
        if resume_id:
            data["resume"] = {"id": resume_id}
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.status_code == 429:
            logger.warning("Rate Limit Excedido al aplicar. Esperando 60s.")
            time.sleep(60)
            return False
        if 200 <= resp.status_code < 300:
            logger.info("Aplicación exitosa a job_id=%s", job_id)
            return True
        logger.error("Error al aplicar: %d %s", resp.status_code, resp.text)
        return False

    def filter_recruiter_connections(self, exclude_company="Stori"):
        """
        Filtra conexiones para obtener reclutadores, excluyendo la compañía dada.
        """
        cons = self.get_connections()
        recruiters = []
        for con in cons:
            title = con.get("headline", "").lower()
            company_name = con.get("company", {}).get("name", "").lower()
            is_recruiter = any(kw in title for kw in ["recruiter", "talent", "hr", "hiring", "recruitment"])
            if is_recruiter and company_name != exclude_company.lower():
                recruiters.append(con)
        return recruiters

    def get_job_description(self, job_id: str):
        """Ejemplo de endpoint /jobs/{job_id} para obtener descripción (requiere Talent Solutions)."""
        url = f"{self.base_url}/jobs/{job_id}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("description", "")
            else:
                logger.warning("No se pudo obtener descripción. status=%d", resp.status_code)
                return ""
        except Exception as e:
            logger.error("Excepción al obtener descripción: %s", e)
            return ""
