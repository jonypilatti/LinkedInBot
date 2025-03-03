"""
LinkedIn Job Search Bot with LM Studio Integration
-------------------------------------------------
This bot automates job searching on LinkedIn with two main functionalities:
1. Contact recruiters from your connections (excluding current company)
2. Apply to Easy Apply jobs automatically

Requirements:
- Python 3.8+
- LinkedIn API credentials
- LM Studio with QWEN model
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import requests

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
    """Interface for LinkedIn API interactions with error handling and retries"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        logger.info("Initializing LinkedInAPI with client_id=%s, redirect_uri=%s", client_id, redirect_uri)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.base_url = "https://api.linkedin.com/v2"

    def authenticate(self, auth_code: str = None) -> bool:
        """
        Authenticate with LinkedIn API
        
        If auth_code is given, we exchange it for an access token.
        Otherwise, we try to load a previously saved token.
        
        Returns:
            bool: True if authentication successful
        """
        if auth_code:
            logger.info("Authenticating with LinkedIn using auth_code=%s", auth_code)
            # Exchange auth code for access token
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
               
                logger.info("Successfully obtained access_token=%s", self.access_token)
                # Save token for future use
                self._save_token(token_data)
                return True
            else:
                logger.error("Authentication failed with status=%s, response=%s", response.status_code, response.text)
                return False
        else:
            logger.info("No auth_code provided, attempting to load existing token.")
            # Try to load existing token
            return self._load_token()

    def _save_token(self, token_data: Dict) -> None:
        """Save token data to file"""
        logger.info("Saving token to linkedin_token.json")
        with open("linkedin_token.json", "w") as f:
            json.dump(token_data, f)

    def _load_token(self) -> bool:
        """Load token data from file"""
        logger.info("Attempting to load token from linkedin_token.json")
        try:
            with open("linkedin_token.json", "r") as f:
                token_data = json.load(f)
                self.access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at", 0)
                if expires_at < time.time():
                    logger.warning("Token expired at %s, needs refresh", expires_at)
                    return False
                logger.info("Token loaded successfully, access_token=%s", self.access_token)
                return True
        except FileNotFoundError:
            logger.warning("No saved token found in linkedin_token.json")
            return False

    def get_current_user_profile(self) -> Dict:
        """Get current user's profile data"""
        logger.info("Fetching current user profile from LinkedIn.")
        endpoint = f"{self.base_url}/userinfo"
        # endpoint = f"{self.base_url}/me"
        return self._make_request("GET", endpoint)

    def get_user_connections(self) -> List[Dict]:
        """
        Get user's connections

        NOTE: 
        The actual LinkedIn API for retrieving connections may differ. 
        This is a placeholder based on hypothetical REST endpoints.
        """
        logger.info("Fetching user connections from LinkedIn.")
        endpoint = f"{self.base_url}/connections"
        return self._make_request("GET", endpoint)

    def filter_recruiter_connections(self, exclude_company: str = "Stori") -> List[Dict]:
        """
        Filter connections to find recruiters not from specific company
        
        Args:
            exclude_company: Company to exclude from results
            
        Returns:
            List of filtered recruiter connections
        """
        logger.info("Filtering recruiter connections, excluding company=%s", exclude_company)
        connections = self.get_user_connections()
        recruiters = []

        for connection in connections:
            title = connection.get("title", "").lower()
            company = connection.get("company", {}).get("name", "")
            
            is_recruiter = any(keyword in title for keyword in
                               ["recruiter", "talent", "hr", "hiring", "recruitment"])
            
            if is_recruiter and company != exclude_company:
                recruiters.append(connection)

        logger.info("Found %d recruiters after filtering out %s", len(recruiters), exclude_company)
        return recruiters

    def search_jobs(self, keywords: List[str], location: str = "", easy_apply_only: bool = True) -> List[Dict]:
        """
        Search for jobs matching criteria
        
        Args:
            keywords: List of job keywords
            location: Job location
            easy_apply_only: Filter to only Easy Apply jobs
            
        Returns:
            List of matching job postings
        """
        logger.info("Searching for jobs with keywords=%s, location=%s, easy_apply_only=%s", keywords, location, easy_apply_only)
        endpoint = f"{self.base_url}/job-search"
        params = {
            "keywords": ",".join(keywords),
            "location": location,
            "easy_apply": easy_apply_only
        }
        return self._make_request("GET", endpoint, params=params)

    def send_message(self, recipient_id: str, message: str) -> bool:
        """
        Send a message to a connection
        
        Args:
            recipient_id: Recipient's LinkedIn ID
            message: Message content
            
        Returns:
            bool: True if message sent successfully
        """
        logger.info("Sending message to recipient_id=%s", recipient_id)
        endpoint = f"{self.base_url}/messages"
        data = {
            "recipients": [{"person": {"id": recipient_id}}],
            "body": message
        }
        response = self._make_request("POST", endpoint, json=data)
        return response.get("status", "") == "success"

    def apply_to_job(self, job_id: str, resume_id: str = None) -> bool:
        """
        Apply to a job posting
        
        Args:
            job_id: LinkedIn job ID
            resume_id: ID of resume to use
            
        Returns:
            bool: True if application submitted successfully
        """
        logger.info("Applying to job_id=%s, using resume_id=%s", job_id, resume_id)
        endpoint = f"{self.base_url}/jobs/{job_id}/applications"
        data = {}

        if resume_id:
            data["resume"] = {"id": resume_id}

        response = self._make_request("POST", endpoint, json=data)
        return response.get("status", "") == "success"

    def _make_request(self, method: str, endpoint: str, params: Dict = None, json: Dict = None) -> Dict:
        """
        Make request to LinkedIn API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body data
            
        Returns:
            Response data as dictionary or error
        """
        logger.debug("Making %s request to endpoint=%s with params=%s, json=%s", method, endpoint, params, json)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.request(method=method, url=endpoint, headers=headers, params=params, json=json)

        if 200 <= response.status_code < 300:
            logger.debug("Request to %s successful (status=%s).", endpoint, response.status_code)
            return response.json()
        else:
            logger.error("API request failed: %s - %s", response.status_code, response.text)
            return {"error": response.text, "status": "error"}


class LMStudioInterface:
    """Interface for LM Studio with QWEN model"""

    def __init__(self, api_url: str = "http://localhost:1234/v1"):
        """
        Initialize LM Studio interface
        
        Args:
            api_url: URL for LM Studio API
        """
        logger.info("Initializing LMStudioInterface with api_url=%s", api_url)
        self.api_url = api_url
        self.model = "qwen2.5-7b-instruct-1m"  # Example model name, or your actual QWEN model

    def generate_message(self, prompt_template: str, context: Dict) -> str:
        """
        Generate a message using LM Studio
        
        Args:
            prompt_template: Template for the prompt
            context: Context variables to fill in the template
            
        Returns:
            Generated message text
        """
        logger.info("Generating message using LMStudio with prompt_template=%s, context=%s", prompt_template, context)
        # Fill template with context
        prompt = self._fill_template(prompt_template, context)

        # Call LM Studio API
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
            response = requests.post(endpoint, json=data)
            if response.status_code == 200:
                logger.debug("LM Studio request succeeded with status=%s", response.status_code)
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error("LM Studio request failed: %s - %s", response.status_code, response.text)
                return ""
        except Exception as e:
            logger.error("Error calling LM Studio: %s", e)
            return ""

    def _fill_template(self, template: str, context: Dict) -> str:
        """Fill template with given context"""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


class LinkedInBot:
    """Main bot class that coordinates LinkedIn API and LM Studio"""

    def __init__(self, linkedin_api: LinkedInAPI, lm_studio: LMStudioInterface):
        """
        Initialize LinkedIn Bot
        
        Args:
            linkedin_api: LinkedIn API interface
            lm_studio: LM Studio interface
        """
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

        # Initialize and authenticate
        self._initialize()

    def _initialize(self) -> None:
        """Authenticate and load user profile"""
        logger.info("Attempting LinkedIn authentication in LinkedInBot._initialize()...")
        if self.linkedin.authenticate():
            logger.info("Successfully authenticated with LinkedIn, fetching user profile...")
            self.user_profile = self.linkedin.get_current_user_profile()
            logger.info("User profile loaded: %s", self.user_profile)
        else:
            logger.error("Failed to authenticate with LinkedIn")

    def contact_recruiters(self, skills: str = "NextJS/Python with FastAPI or NodeJS+ExpressJS") -> Dict:
        """
        Contact recruiters in your connections
        
        Args:
            skills: Skills to highlight in messages
            
        Returns:
            Dictionary with results (success/failed/skipped + details)
        """
        logger.info("Starting contact_recruiters with skills=%s", skills)
        results = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        recruiters = self.linkedin.filter_recruiter_connections(exclude_company="Stori")
        logger.info("Found %d potential recruiter connections", len(recruiters))

        for recruiter in recruiters:
            # Prepare context for the message
            context = {
                "recruiter_name": recruiter.get("firstName", ""),
                "recruiter_title": recruiter.get("title", "Recruiter"),
                "recruiter_company": recruiter.get("company", {}).get("name", "your company"),
                "skills": skills,
                "user_name": f"{self.user_profile.get('firstName', '')} {self.user_profile.get('lastName', '')}"
            }

            # Generate personalized note
            personalization_prompt = (
                f"Generate a brief, professional, personalized note for a recruiter named {context['recruiter_name']} "
                f"who works at {context['recruiter_company']} as a {context['recruiter_title']}. "
                f"The note should be 1-2 sentences explaining why I'm interested in potential opportunities at their company."
            )
            logger.debug("Generating personalized note for recruiter=%s", recruiter.get("firstName", ""))
            personalized_note = self.lm_studio.generate_message(personalization_prompt, {})
            context["personalized_note"] = personalized_note

            # Fill the template
            message = self._fill_template(self.recruiter_message_template, context)
            logger.debug("Final message for recruiter_id=%s: %s", recruiter.get("id"), message.strip())

            # Send message
            logger.info("Sending message to recruiter=%s at company=%s", recruiter.get("firstName", ""), recruiter.get("company", {}).get("name", ""))
            success = self.linkedin.send_message(recruiter.get("id"), message)
            result = {
                "recruiter": f"{recruiter.get('firstName', '')} {recruiter.get('lastName', '')}",
                "company": recruiter.get("company", {}).get("name", ""),
                "message": message,
                "success": success
            }

            if success:
                logger.info("Message sent successfully to %s", result["recruiter"])
                results["success"] += 1
            else:
                logger.error("Failed to send message to %s", result["recruiter"])
                results["failed"] += 1

            results["details"].append(result)

            # Delay to avoid hitting rate limits
            logger.debug("Sleeping 5 seconds to avoid rate limit...")
            time.sleep(5)

        return results

    def apply_to_jobs(self, keywords: List[str] = None, location: str = "") -> Dict:
        """
        Search for and apply to Easy Apply jobs
        
        Args:
            keywords: Job search keywords
            location: Job location
            
        Returns:
            Dictionary with results (searched/applied/skipped + details)
        """
        if keywords is None:
            keywords = ["full stack", "nodejs", "python", "nextjs", "expressjs", "fastapi"]

        logger.info("Starting apply_to_jobs with keywords=%s, location=%s", keywords, location)
        results = {
            "searched": 0,
            "applied": 0,
            "skipped": 0,
            "details": []
        }

        jobs = self.linkedin.search_jobs(keywords, location, easy_apply_only=True)
        results["searched"] = len(jobs)
        logger.info("Found %d matching Easy Apply jobs", len(jobs))

        for job in jobs:
            job_id = job.get("id")
            logger.debug("Applying to job_id=%s, job_title=%s", job_id, job.get("title", ""))
            success = self.linkedin.apply_to_job(job_id)
            result = {
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("name", ""),
                "location": job.get("location", ""),
                "applied": success
            }

            if success:
                logger.info("Successfully applied to %s at %s", result["title"], result["company"])
                results["applied"] += 1
            else:
                logger.warning("Failed to apply to %s at %s", result["title"], result["company"])
                results["skipped"] += 1

            results["details"].append(result)
            logger.debug("Sleeping 3 seconds to avoid rate limit after applying to job_id=%s...", job_id)
            time.sleep(3)

        return results

    def _fill_template(self, template: str, context: Dict) -> str:
        """Fill the recruiter message template with the given context"""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


def main():
    """Main function to run the bot via command line arguments"""
    logger.info("Starting main function for LinkedIn Bot.")
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        logger.info("Loaded config from config.json")
    except FileNotFoundError:
        logger.error("Config file not found. Please create config.json")
        config = {
            "linkedin": {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://localhost:8000/callback"
            },
            "lm_studio": {
                "api_url": "http://localhost:1234/v1"
            }
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        logger.info("Created template config.json. Please fill in your credentials.")
        return

    # Initialize API clients
    logger.info("Initializing LinkedInAPI and LMStudioInterface...")
    linkedin_api = LinkedInAPI(
        client_id=config["linkedin"]["client_id"],
        client_secret=config["linkedin"]["client_secret"],
        redirect_uri=config["linkedin"]["redirect_uri"]
    )

    lm_studio = LMStudioInterface(api_url=config["lm_studio"]["api_url"])

    # Create bot instance
    logger.info("Creating LinkedInBot instance...")
    bot = LinkedInBot(linkedin_api, lm_studio)

    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Job Search Bot")
    parser.add_argument("--contact-recruiters", action="store_true", help="Contact recruiters")
    parser.add_argument("--apply-jobs", action="store_true", help="Apply to jobs")
    parser.add_argument("--skills", type=str, default="NextJS/Python with FastAPI or NodeJS+ExpressJS",
                       help="Skills to highlight")
    parser.add_argument("--location", type=str, default="", help="Job location")

    args = parser.parse_args()

    if args.contact_recruiters:
        logger.info("User requested to contact recruiters.")
        results = bot.contact_recruiters(skills=args.skills)
        logger.info("Contacted %d recruiters, failed: %d", results["success"], results["failed"])

    if args.apply_jobs:
        logger.info("User requested to apply to jobs.")
        results = bot.apply_to_jobs(location=args.location)
        logger.info("Applied to %d jobs out of %d searched.", results["applied"], results["searched"])

    if not args.contact_recruiters and not args.apply_jobs:
        logger.info("No action specified. Use --contact-recruiters or --apply-jobs")
        parser.print_help()


if __name__ == "__main__":
    main()
