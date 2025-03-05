import os
import random
import logging
import sqlite3
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LinkedInBot:
    MODES = {
        "observacion": {"max_apps": 0, "max_msgs": 0},
        "semi_automatico": {"max_apps": 1, "max_msgs": 1},
        "full_automatico": {"max_apps": 3, "max_msgs": 2}
    }
    
    def __init__(self, email: str = None, password: str = None, mode="observacion", headless: bool = None, proxy_list=None):
        logging.basicConfig(
        level=logging.DEBUG,  # Cambia a DEBUG para ver más detalles
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
        logging.StreamHandler()  # Para imprimir en consola
            ]
        )

        # Si no se pasan los parámetros, se leen de las variables de entorno.
        self.email = email or os.environ.get("LINKEDIN_EMAIL")
        self.password = password or os.environ.get("LINKEDIN_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("Las variables de entorno LINKEDIN_EMAIL y LINKEDIN_PASSWORD son obligatorias.")
        
        # Configurar headless según variable de entorno
        if headless is None:
            headless_str = os.environ.get("HEADLESS", "True")
            headless = headless_str.lower() in ["true", "1", "yes"]
        self.headless = headless
        
        # Configurar proxies si existen en la variable de entorno
        if proxy_list is None:
            proxies_str = os.environ.get("LINKEDIN_PROXIES")
            if proxies_str:
                proxy_list = [p.strip() for p in proxies_str.split(",")]
            else:
                proxy_list = None
        self.proxy_list = proxy_list
        
        self.mode = mode
        self.driver = self._init_driver()
        self.db_lock = threading.Lock()
        self.db_conn = sqlite3.connect("history.db", check_same_thread=False)
        self._init_db()
        self.max_apps = self.MODES[mode]["max_apps"]
        self.max_msgs = self.MODES[mode]["max_msgs"]
        self.applied_today = 0
        self.messages_sent_today = 0
        self.paused = False  # Para controlar la pausa

    def _init_db(self):
        with self.db_lock:
            cursor = self.db_conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                              action TEXT,
                              details TEXT)''')
            self.db_conn.commit()
    
    def _log_history(self, action, details):
        with self.db_lock:
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
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
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
    def simulate_typing(self, element, text):
        logger.info(f"⌨️ Simulando escritura: '{text}' en {element.tag_name}")
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.2, 0.5))  # Aumenta el retardo para simular escritura humana


    def _check_for_captcha(self):
        """Verifica si aparece un captcha en la página."""
        page_source = self.driver.page_source.lower()
        if "captcha" in page_source or "verificación" in page_source:
            logger.warning("Captcha detectado. Pausando acción para intervención manual.")
            self._log_history("Captcha", "Captcha detectado en la página.")
            return True
        return False


    def login(self):
        """Inicia sesión en LinkedIn con ingreso de contraseña tecla por tecla."""
        logger.info("🔑 Iniciando sesión en LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
    
        try:
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            self.simulate_typing(username_field, self.email)

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            self.simulate_typing(password_field, self.password)

            self.simulate_scroll()

            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            submit_button.click()

            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.current_url != "https://www.linkedin.com/login"
            )

            if self._check_for_captcha():
                logger.warning("⚠️ Captcha detectado, intervención manual requerida.")
                self._log_history("Captcha", "Captcha detectado en el login.")
                return False

            logger.info("✅ Inicio de sesión exitoso.")
            self._log_history("Login", f"Inicio de sesión con email {self.email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en login: {e}")
            self._log_history("Login Error", str(e))
            return False

    def extract_form_fields(self):
        try:
            logger.info("🔍 Buscando campos del formulario de Easy Apply...")
        
            # Esperar a que aparezca el contenedor del formulario de Easy Apply
            easy_apply_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-modal-container]"))
                )

        
            form_fields = {}
        
            # Buscar inputs dentro del contenedor del formulario
            input_fields = easy_apply_container.find_elements(By.TAG_NAME, "input")
            for field in input_fields:
                field_name = field.get_attribute("name") or field.get_attribute("aria-label")
                if field_name:
                    form_fields[field_name] = "text"
        
            # Buscar selects dentro del contenedor
            select_fields = easy_apply_container.find_elements(By.TAG_NAME, "select")
            for field in select_fields:
                field_name = field.get_attribute("name") or field.get_attribute("aria-label")
                if field_name:
                    form_fields[field_name] = "select"
        
            # Buscar textareas dentro del contenedor
            textarea_fields = easy_apply_container.find_elements(By.TAG_NAME, "textarea")
            for field in textarea_fields:
                field_name = field.get_attribute("name") or field.get_attribute("aria-label")
                if field_name:
                    form_fields[field_name] = "textarea"
        
            logger.info(f"📋 Campos detectados en el formulario: {form_fields}")
            return form_fields
    
        except Exception as e:
            logger.error(f"❌ Error al extraer campos del formulario: {e}")
            return {}

    def get_mock_data_for_fields(self, form_fields):
        """Genera valores mock para cada campo en el formulario."""
        logger.info("🤖 Solicitando a la IA valores mock para el formulario...")

        # Diccionario de datos simulados
        mock_data = {}

        for field_name, field_type in form_fields.items():
            if "name" in field_name.lower():
                mock_data[field_name] = "John Doe"
            elif "email" in field_name.lower():
                mock_data[field_name] = "johndoe@example.com"
            elif "phone" in field_name.lower():
                mock_data[field_name] = "+1 234 567 8901"
            elif "linkedin" in field_name.lower():
                mock_data[field_name] = "https://www.linkedin.com/in/johndoe"
            elif field_type == "select":
                mock_data[field_name] = "First Option"
            elif field_type == "textarea":
                mock_data[field_name] = "I am very excited about this opportunity!"
            else:
                mock_data[field_name] = "Sample Data"

        logger.info(f"📝 Datos generados: {mock_data}")
        return mock_data
    def fill_easy_apply_form(self):
        try:
            form_fields = self.extract_form_fields()
            if not form_fields:
                logger.warning("⚠️ No se encontraron campos en el formulario.")
                return False

            mock_data = self.get_mock_data_for_fields(form_fields)
            for field_name, value in mock_data.items():
                try:
                    field = self.driver.find_element(By.NAME, field_name)
                    if field.tag_name in ["input", "textarea"]:
                        field.clear()
                        self.simulate_typing(field, value)
                    elif field.tag_name == "select":
                        options = field.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if option.text == value:
                                option.click()
                                break
                    logger.info(f"✅ Campo '{field_name}' llenado con: {value}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo llenar el campo '{field_name}': {e}")
                    # Se pausa el bot para intervención manual
                    self.pause()
                    logger.info(f"El bot se ha pausado esperando intervención manual para el campo: {field_name}")
                    # Se espera hasta que el usuario reanude el bot
                    while self.paused:
                        time.sleep(1)
                    # Opcional: se podría intentar nuevamente llenar el campo
            return True

        except Exception as e:
            logger.error(f"❌ Error al completar el formulario de Easy Apply: {e}")
            return False


    def search_jobs(self, keywords, location="", max_results=10):
        """Busca empleos en LinkedIn."""
        if self.mode == "observacion":
            logger.info("Modo observación activo. Solo explorando trabajos.")
        
        logger.info("Buscando empleos en LinkedIn...")
        query = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location}&f_LF=f_AL"
        self.driver.get(query)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-card-container"))
            )
            self.simulate_scroll()
            
            jobs = []
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")[:max_results]
            for job in job_cards:
                while self.paused:
                    time.sleep(1)
                title = job.find_element(By.CSS_SELECTOR, "a.job-card-container__link.job-card-list__title--link").text
                company = job.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle span").text
                self.simulate_mouse_hover(job)
                job.click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button"))
                )
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
    
    def search_and_apply_jobs(self, keywords, location="", max_results=10):
        logger.info("Buscando empleos en LinkedIn y aplicando de inmediato...")
        query = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location}&f_LF=f_AL"
        self.driver.get(query)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-card-container"))
            )
            self.simulate_scroll()
        
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-card-container")[:max_results]
            for job in job_cards:
                while self.paused:
                    time.sleep(1)
                title = job.find_element(By.CSS_SELECTOR, "a.job-card-container__link.job-card-list__title--link").text
                company = job.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle span").text
                self.simulate_mouse_hover(job)
                job.click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button"))
                )
                if self._check_easy_apply():
                    logger.info(f"Aplicando de inmediato a {title} en {company}")
                    # Aquí se podría invocar directamente el proceso de aplicación
                    if self.apply_job():
                        self.applied_today += 1
                        self._log_history("Apply Job", f"Aplicado a {title} en {company}")
                    else:
                        logger.warning(f"Fallo al aplicar a {title} en {company}")
                else:
                    logger.info(f"{title} en {company} no tiene opción Easy Apply")
            logger.info("Proceso de búsqueda y aplicación completado.")
        except Exception as e:
            logger.error(f"Error en búsqueda y aplicación: {e}")
            self._log_history("Search Apply Error", str(e))

    def apply_job(self):
        try:
            # Localiza y haz clic en el botón "Easy Apply"
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "jobs-apply-button"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView();", apply_button)
            time.sleep(1)
            ActionChains(self.driver).move_to_element(apply_button).click().perform()
            logger.info("🖱️ Se hizo clic en Easy Apply.")

            # Completa el formulario de aplicación
            if self.fill_easy_apply_form():
                logger.info("📋 Formulario completado correctamente.")
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "artdeco-button--primary"))
                )
                submit_button.click()
                logger.info("✅ Aplicación enviada.")
                return True
            else:
                logger.warning("⚠️ No se pudo completar el formulario.")
                return False
        except Exception as e:
            logger.error(f"❌ Error al aplicar: {e}")
            return False

    def message_recruiters(self, message_generator):
        """
    Envía mensajes a reclutadores con límites diarios.
    message_generator: función que recibe el nombre del reclutador y devuelve un mensaje personalizado.
    """
        if self.messages_sent_today >= self.max_msgs:
            logger.info("🚫 Límite de mensajes diarios alcanzado.")
            self._log_history("Message Limit", "Límite de mensajes diarios alcanzado.")
            return
    
        logger.info("🕵️ Buscando reclutadores...")
        self.driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mn-connection-card__name"))
            )
            recruiters = self.driver.find_elements(By.CLASS_NAME, "mn-connection-card__name")[:5]

            for recruiter in recruiters:
                while self.paused:
                    time.sleep(1)
            
                if self.messages_sent_today >= self.max_msgs:
                    break
            
                try:
                    recruiter.click()
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "message-anywhere-button"))
                    )

                    self.simulate_scroll()
                    self.driver.find_element(By.CLASS_NAME, "message-anywhere-button").click()

                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "msg-form__contenteditable"))
                    )

                    text_area = self.driver.find_element(By.CLASS_NAME, "msg-form__contenteditable")
                    personalized_message = message_generator(recruiter.text)
                
                    # ✍️ Simular escritura humana del mensaje
                    self.simulate_typing(text_area, personalized_message)

                    send_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "msg-form__send-button"))
                    )
                    send_button.click()

                    self.messages_sent_today += 1
                    logger.info(f"✅ Mensaje enviado a {recruiter.text}.")
                    self._log_history("Message Sent", f"Mensaje enviado a {recruiter.text}: {personalized_message}")

                except Exception as e:
                    logger.warning(f"❌ No se pudo enviar mensaje a {recruiter.text}: {e}")
                    self._log_history("Message Error", f"{recruiter.text}: {e}")

        except Exception as e:
            logger.error(f"❌ Error al buscar reclutadores: {e}")
            self._log_history("Message Recruiters Error", str(e))

    
    def get_stats(self):
        """Devuelve estadísticas actuales del bot."""
        return {
            "applied": self.applied_today,
            "messages": self.messages_sent_today
        }
    
    def pause(self):
        """Pausa la ejecución del bot."""
        self.paused = True
        logger.info("Bot pausado.")
        self._log_history("Pause", "El bot ha sido pausado.")
    
    def resume(self):
        """Reanuda la ejecución del bot."""
        self.paused = False
        logger.info("Bot reanudado.")
        self._log_history("Resume", "El bot ha sido reanudado.")
    
    def close(self):
        """Cierra el navegador y finaliza la sesión."""
        self.driver.quit()
        logger.info("Sesión cerrada.")
        self._log_history("Session Closed", "El navegador se cerró correctamente.")
