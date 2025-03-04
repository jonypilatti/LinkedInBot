import logging
import sqlite3
import json
import time
from typing import List, Dict, Callable, Optional

from linkedin_api import LinkedInAPI
from lm_studio import LMStudioInterface

logger = logging.getLogger(__name__)

class LinkedInBot:
    """
    Coordina la LinkedInAPI y LMStudio para contactar reclutadores,
    aplicar a empleos, almacenar historial en SQLite, y generar cover letters.
    """

    def __init__(self, linkedin_api: LinkedInAPI, lm_studio: LMStudioInterface):
        self.linkedin = linkedin_api
        self.lm_studio = lm_studio
        self.user_profile = {}
        self.db_conn = sqlite3.connect("history.db")
        self._init_db()

        logger.info("Inicializando LinkedInBot...")
        self._initialize()

    def _initialize(self):
        logger.info("Intentando autenticación con LinkedIn...")
        if self.linkedin.authenticate():
            logger.info("Autenticación exitosa. Obteniendo perfil de usuario...")
            self.user_profile = self.linkedin.get_profile()
            logger.info("Perfil cargado: %s", self.user_profile)
        else:
            logger.error("Falló la autenticación con LinkedIn. Revisar config o token.")

    def _init_db(self):
        """Crea la tabla history si no existe."""
        with self.db_conn:
            self.db_conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT,
                    details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _save_history(self, action: str, details: dict):
        """Guarda un registro (acción + detalles) en la tabla history."""
        with self.db_conn:
            self.db_conn.execute(
                "INSERT INTO history (action, details) VALUES (?, ?)",
                (action, json.dumps(details))
            )

    def contact_recruiters(self, skills="NextJS/Python", exclude_company="Stori") -> dict:
        """Envía mensajes a reclutadores excluyendo la compañía indicada."""
        results = {"success": 0, "failed": 0, "skipped": 0, "details": []}
        recruiters = self.linkedin.filter_recruiter_connections(exclude_company=exclude_company)
        user_name = f"{self.user_profile.get('firstName', '')} {self.user_profile.get('lastName', '')}"

        default_template = """
Hello {recruiter_name},

I'm exploring new opportunities as a {skills} developer. {personalized_note}

Best regards,
{user_name}
        """
        
        for rec in recruiters:
            recruiter_first = rec.get("firstName", "")
            recruiter_company = rec.get("company", {}).get("name", "")
            note = self.lm_studio.generate_message(
                f"Generate a brief, polite note for recruiter {recruiter_first} at {recruiter_company}", {}
            )
            
            context = {
                "recruiter_name": recruiter_first,
                "skills": skills,
                "personalized_note": note.strip(),
                "user_name": user_name
            }
            
            message = self._fill_template(default_template, context)
            recruiter_id = rec.get("id", "")
            if not recruiter_id:
                results["skipped"] += 1
                continue

            success = self.linkedin.send_message(recruiter_id, message)
            detail = {"recruiter_id": recruiter_id, "company": recruiter_company, "message": message, "success": success}
            results["success" if success else "failed"] += 1
            results["details"].append(detail)

            self._save_history("message", detail)

        return results

    def search_and_apply_jobs(self, keywords: List[str], location="", max_jobs=20, easy_apply_only=True, cancel_flag: Callable[[], bool] = lambda: False) -> dict:
        """Busca empleos, obtiene descripciones, genera cover letters y aplica."""
        results = {"searched_jobs": 0, "applied": 0, "failed": 0, "details": []}
        jobs = self.linkedin.search_jobs(keywords, location, easy_apply_only)
        results["searched_jobs"] = len(jobs)

        for job in jobs[:max_jobs]:
            if cancel_flag():
                logger.warning("Proceso cancelado por el usuario.")
                break

            job_id = job.get("id")
            if not job_id:
                continue

            description = self.linkedin.get_job_description(job_id)
            score = self._calculate_compatibility(description, keywords)
            cover_letter = self.lm_studio.generate_message(
                f"Generate a short cover letter for a {keywords} position.", {}
            ) if self.cover_letter_template else ""
            
            success = self.linkedin.apply_to_job(job_id)
            detail = {"job_id": job_id, "success": success, "compatibility_score": score, "cover_letter": cover_letter}
            results["applied" if success else "failed"] += 1
            results["details"].append(detail)
            self._save_history("apply", detail)
        
        return results

    def _calculate_compatibility(self, description: str, keywords: List[str]) -> float:
        """Calcula la compatibilidad entre la descripción del trabajo y las palabras clave."""
        if not description:
            return 0
        desc_lower = description.lower()
        match_count = sum(1 for kw in keywords if kw.lower().strip() in desc_lower)
        return round((match_count / len(keywords) * 100) if keywords else 0, 2)

    def _fill_template(self, template: str, context: dict) -> str:
        for k, v in context.items():
            template = template.replace(f"{{{k}}}", str(v))
        return template.strip()

    def set_recruiter_template(self, template_content):
        """Guarda la plantilla personalizada para contactar reclutadores."""
        self.recruiter_template = template_content

    def set_cover_template(self, template_content):
        """Guarda la plantilla personalizada para cover letters."""
        self.cover_letter_template = template_content