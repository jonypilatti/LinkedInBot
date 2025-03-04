import time
import logging
import sqlite3
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LinkedInBot:
    MODES = {
        "observacion": {"max_apps": 0, "max_msgs": 0},
        "semi_automatico": {"max_apps": 1, "max_msgs": 1},
        "full_automatico": {"max_apps": 3, "max_msgs": 2}
    }
    
    def __init__(self, email: str, password: str, mode="observacion", headless=True, proxy_list=None):
        self.email = email
        self.password = password
        self.mode = mode
        self.headless = headless
        self.proxy_list = proxy_list
        self.driver = self._init_driver()
        self.db_conn = sqlite3.connect("history.db")
        self._init_db()
        self.max_apps = self.MODES[mode]["max_apps"]
        self.max_msgs = self.MODES[mode]["max_msgs"]
        self.applied_today = 0
        self.messages_sent_today = 0
    
    def _init_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                          action TEXT,
                          details TEXT)''')
        self.db_conn.commit()
    
    def _log_history(self, action, details):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO history (action, details) VALUES (?, ?)", (action, details))
        self.db_conn.commit()
    
    def _init_driver(self):
        """Inicializa el navegador en modo automatizado con rotación de proxies y user-agent aleatorio."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Rotación de User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
        ]
        user_agent = random.choice(user_agents)
        options.add_argument(f'user-agent={user_agent}')
        
        # Rotación de proxy si se proporcionan
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            options.add_argument(f'--proxy-server={proxy}')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def simulate_scroll(self):
        """Simula el desplazamiento de página para imitar comportamiento humano."""
        scroll_distance = random.randint(100, 300)
        self.driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_distance)
        time.sleep(random.uniform(0.5, 2))

    def simulate_mouse_hover(self, element):
        """Simula movimiento del ratón sobre un elemento."""
        try:
            action = ActionChains(self.driver)
            action.move_to_element(element).perform()
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.warning(f"Error en simular hover: {e}")

    def _check_for_captcha(self):
        """Verifica si aparece un captcha en la página."""
        page_source = self.driver.page_source.lower()
        if "captcha" in page_source or "verificación" in page_source:
            logger.warning("Captcha detectado. Pausando acción para intervención manual.")
            self._log_history("Captcha", "Captcha detectado en la página.")
            return True
        return False

    def login(self):
        """Inicia sesión en LinkedIn."""
        logger.info("Iniciando sesión en LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(5, 10))
        try:
            self.driver.find_element(By.ID, "username").send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.simulate_scroll()
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(random.uniform(5, 10))
            if self._check_for_captcha():
                logger.warning("Acción detenida por captcha.")
                return False
            logger.info("Inicio de sesión exitoso.")
            self._log_history("Login", f"Inicio de sesión con email {self.email}")
            return True
        except Exception as e:
            logger.error(f"Error en login: {e}")
            self._log_history("Login Error", str(e))
            return False

    def search_jobs(self, keywords, location="", max_results=10):
        """Busca empleos en LinkedIn."""
        if self.mode == "observacion":
            logger.info("Modo observación activo. Solo explorando trabajos.")
        
        logger.info("Buscando empleos en LinkedIn...")
        query = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location}&f_LF=f_AL"
        self.driver.get(query)
        time.sleep(random.uniform(5, 10))
        self.simulate_scroll()
        
        jobs = []
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")[:max_results]
            for job in job_cards:
                title = job.find_element(By.CLASS_NAME, "job-card-list__title").text
                company = job.find_element(By.CLASS_NAME, "job-card-container__company-name").text
                # Simular interacción humana
                self.simulate_mouse_hover(job)
                job.click()
                time.sleep(random.uniform(3, 6))
                easy_apply = self._check_easy_apply()
                jobs.append({"title": title, "company": company, "easy_apply": easy_apply})
            logger.info(f"Se encontraron {len(jobs)} trabajos.")
            self._log_history("Search Jobs", f"Buscados trabajos con keywords: {keywords}, ubicación: {location}")
        except Exception as e:
            logger.error(f"Error al buscar trabajos: {e}")
            self._log_history("Search Jobs Error", str(e))
        return jobs
    
    def _check_easy_apply(self):
        """Verifica si el trabajo tiene la opción Easy Apply."""
        try:
            self.driver.find_element(By.CLASS_NAME, "jobs-apply-button")
            return True
        except Exception:
            return False
    
    def apply_to_jobs(self, jobs):
        """Aplica automáticamente a los trabajos con Easy Apply, con límites diarios."""
        for job in jobs:
            if self.applied_today >= self.max_apps:
                logger.info("🚫 Límite de aplicaciones diarias alcanzado.")
                self._log_history("Apply Limit", "Límite de aplicaciones diarias alcanzado.")
                return
            if job["easy_apply"]:
                try:
                    apply_button = self.driver.find_element(By.CLASS_NAME, "jobs-apply-button")
                    self.simulate_mouse_hover(apply_button)
                    apply_button.click()
                    time.sleep(random.uniform(2, 6))
                    submit_button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
                    submit_button.click()
                    time.sleep(random.uniform(3, 8))
                    self.applied_today += 1
                    logger.info(f"✅ Aplicado a {job['title']} en {job['company']}")
                    self._log_history("Apply Job", f"Aplicado a {job['title']} en {job['company']}")
                except Exception as e:
                    logger.warning(f"❌ No se pudo aplicar a {job['title']} en {job['company']}: {e}")
                    self._log_history("Apply Job Error", f"{job['title']} en {job['company']}: {e}")
    
    def message_recruiters(self, message_generator):
        """
        Envía mensajes a reclutadores con límites diarios.
        message_generator: función que recibe el nombre del reclutador y devuelve un mensaje personalizado.
        """
        if self.messages_sent_today >= self.max_msgs:
            logger.info("🚫 Límite de mensajes diarios alcanzado.")
            self._log_history("Message Limit", "Límite de mensajes diarios alcanzado.")
            return
        
        logger.info("Buscando reclutadores...")
        self.driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        time.sleep(random.uniform(5, 10))
        try:
            recruiters = self.driver.find_elements(By.CLASS_NAME, "mn-connection-card__name")[:5]
            for recruiter in recruiters:
                if self.messages_sent_today >= self.max_msgs:
                    break
                try:
                    recruiter.click()
                    time.sleep(random.uniform(3, 6))
                    self.simulate_scroll()
                    self.driver.find_element(By.CLASS_NAME, "message-anywhere-button").click()
                    time.sleep(random.uniform(2, 5))
                    text_area = self.driver.find_element(By.CLASS_NAME, "msg-form__contenteditable")
                    personalized_message = message_generator(recruiter.text)
                    text_area.send_keys(personalized_message)
                    time.sleep(random.uniform(1, 3))
                    send_button = self.driver.find_element(By.CLASS_NAME, "msg-form__send-button")
                    send_button.click()
                    time.sleep(random.uniform(2, 6))
                    self.messages_sent_today += 1
                    logger.info(f"✅ Mensaje enviado a {recruiter.text}.")
                    self._log_history("Message Sent", f"Mensaje enviado a {recruiter.text}: {personalized_message}")
                except Exception as e:
                    logger.warning(f"❌ No se pudo enviar mensaje a {recruiter.text}: {e}")
                    self._log_history("Message Error", f"{recruiter.text}: {e}")
        except Exception as e:
            logger.error(f"Error al buscar reclutadores: {e}")
            self._log_history("Message Recruiters Error", str(e))
    
    def close(self):
        """Cierra el navegador y finaliza la sesión."""
        self.driver.quit()
        logger.info("Sesión cerrada.")
        self._log_history("Session Closed", "El navegador se cerró correctamente.")
