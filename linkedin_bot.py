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

from datetime import datetime
from typing import List, Dict, Any, Optional

# -------------------------- NEW IMPORT --------------------------
from linkedin import linkedin  # python3-linkedin

# Configure logging
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
    """Interface for LinkedIn API interactions using python3-linkedin."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Build the authentication object for python3-linkedin.
        We'll store the token locally (linkedin_token.json).
        """
        logger.info("Initializing LinkedInAPI with client_id=%s, redirect_uri=%s", client_id, redirect_uri)

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # Create the LinkedInAuthentication object. Adjust scopes as needed.
        self.permissions = [
            'r_liteprofile',
            'r_emailaddress',
            'w_member_social',
            # If you need to read connections or other advanced endpoints,
            # you'll need to request additional scopes or products on your LinkedIn app.
        ]
        self.authentication = linkedin.LinkedInAuthentication(
            self.client_id,
            self.client_secret,
            self.redirect_uri,
            self.permissions
        )

        self.access_token = None
        self.application = None
        self.base_url = "https://api.linkedin.com/v2"

    def authenticate(self, auth_code: str = None) -> bool:
        """
        Authenticate with LinkedIn API using python3-linkedin.
        
        If auth_code is provided, exchange it for an access token and save it.
        Otherwise, attempt to load a previously saved token.
        """
        if auth_code:
            # logger.info("Authenticating with LinkedIn using auth_code=%s", auth_code)
            try:
                self.authentication.authorization_code = auth_code
                token = self.authentication.get_access_token()
                self.access_token = token.access_token
                expires_in = token.expires_in  # number of seconds

                logger.info("Successfully obtained an access token from LinkedIn.")
                # Save the token for future use
                expires_at = time.time() + expires_in
                token_data = {
                    "access_token": self.access_token,
                    "expires_at": expires_at
                }
                self._save_token(token_data)

                # Build the actual LinkedInApplication for subsequent calls
                self.application = linkedin.LinkedInApplication(token=self.access_token)
                return True
            except Exception as e:
                logger.error("Authentication failed: %s", e)
                return False
        else:
            logger.info("No auth_code provided, attempting to load existing token.")
            loaded = self._load_token()
            if loaded and self.access_token:
                logger.info("Existing token loaded. Building LinkedInApplication.")
                self.application = linkedin.LinkedInApplication(token=self.access_token)
                return True
            else:
                logger.warning("Unable to load token or token expired.")
                return False

    def _save_token(self, token_data: Dict) -> None:
        """Save token data to local JSON file."""
        logger.info("Saving token to linkedin_token.json")
        with open("linkedin_token.json", "w") as f:
            json.dump(token_data, f)

    def _load_token(self) -> bool:
        """Load token data from local JSON file, if valid."""
        try:
            with open("linkedin_token.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at", 0)
                if time.time() > expires_at:
                    logger.warning("Stored LinkedIn access token has expired.")
                    return False
                logger.info("Token loaded successfully, access_token=%s", self.access_token)
                return True
        except FileNotFoundError:
            logger.warning("No saved token found in linkedin_token.json.")
            return False
        except Exception as e:
            logger.error("Error loading token: %s", e)
            return False

    def get_current_user_profile(self) -> Dict:
        """
        Fetch current user's basic profile via python3-linkedin.
        Adjust selectors based on what data you need and your app's scopes.
        """
        if not self.application:
            return {"error": "LinkedInApplication not initialized", "status": "error"}
        try:
            profile = self.application.get_profile(selectors=['id', 'first-name', 'last-name', 'email-address'])
            logger.info("User profile fetched from LinkedIn: %s", profile)
            return profile
        except Exception as e:
            logger.error("Error fetching user profile: %s", e)
            return {"error": str(e), "status": "error"}

    def get_user_connections(self) -> List[Dict]:
        """
        Example placeholder for connections. 
        python3-linkedin doesn't directly expose "connections" on v2 if the LinkedIn app doesn't have special permissions.
        You may need a specific 'connections' permission or an alternative approach.
        Here, we'll just return an empty list or do a custom request.
        """
        logger.info("Attempting to fetch user connections (this may require special LinkedIn permissions).")
        # For demonstration, we do a raw GET with the Bearer token, or return empty if not allowed.
        url = f"{self.base_url}/connections"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # The structure depends on LinkedIn's actual response
                # This is an example placeholder:
                return data.get("values", [])
            else:
                logger.error("Failed to fetch connections: %s - %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logger.error("Error while fetching connections: %s", e)
            return []

    def filter_recruiter_connections(self, exclude_company: str = "Stori") -> List[Dict]:
        """
        Filter connections to find recruiters not from specific company
        """
        logger.info("Filtering recruiter connections, excluding company=%s", exclude_company)
        connections = self.get_user_connections()
        recruiters = []

        for connection in connections:
            title = connection.get("title", "").lower()
            company_info = connection.get("company", {})
            company_name = company_info.get("name", "")
            is_recruiter = any(kw in title for kw in ["recruiter", "talent", "hr", "hiring", "recruitment"])
            if is_recruiter and company_name.lower() != exclude_company.lower():
                recruiters.append(connection)

        logger.info("Found %d recruiters after filtering out '%s'.", len(recruiters), exclude_company)
        return recruiters

    def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a message to a connection. 
        Note: v2 messaging often requires special 'w_member_social' + 'LinkedIn Messaging' product approvals.
        python3-linkedin doesn't always wrap these endpoints, so we might do a manual POST to the messaging endpoint.
        """
        logger.info("Sending message to recipient_id=%s", recipient_id)
        # Example placeholder for a raw POST to the v2 messaging endpoint:
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "recipients": [{"person": {"id": recipient_id}}],
            "body": message
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if 200 <= resp.status_code < 300:
                logger.info("Message sent successfully.")
                return True
            else:
                logger.error("Error sending message: %d - %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Exception while sending message: %s", e)
            return False

    def search_jobs(self, keywords: List[str], location: str = "", easy_apply_only: bool = True) -> List[Dict]:
        """
        Pseudocode for job searching. The library doesn't always have a direct 'search jobs' method.
        If your LinkedIn app is approved for certain job APIs, you might do a raw request with your token.
        """
        logger.info("Searching for jobs with keywords=%s, location=%s, easy_apply_only=%s", keywords, location, easy_apply_only)
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
                return resp.json().get("elements", [])
            else:
                logger.error("Job search failed: %d - %s", resp.status_code, resp.text)
                return []
        except Exception as e:
            logger.error("Exception in job search: %s", e)
            return []

    def apply_to_job(self, job_id: str, resume_id: str = None) -> bool:
        """
        Apply to a job posting (placeholder).
        This likely requires special 'Talent Solutions' or 'Recruitment' product permissions from LinkedIn.
        """
        logger.info("Applying to job_id=%s, using resume_id=%s", job_id, resume_id)
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
                logger.info("Job application submitted successfully.")
                return True
            else:
                logger.error("Failed to apply to job: %d - %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Exception while applying to job: %s", e)
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

