import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import random
import json
import sqlite3
from bot import LinkedInBot
from lm_interface import LMStudioInterface

class LinkedInGUI:
    def __init__(self):
        self.root = ttk.Window(themename="darkly")
        self.root.title("LinkedIn Job Search Bot")
        self.root.geometry("800x650")

        # Cargar configuración desde config.json
        with open("config.json", "r") as f:
            self.config = json.load(f)

        # Leer proxies del config si existen
        proxy_list = self.config.get("proxies", None)
        headless = self.config.get("headless", True)

        self.bot = None
        self.lm_studio = LMStudioInterface()
        self.selected_mode = tk.StringVar(value="observacion")
        
        self.create_widgets()
        self.root.mainloop()

    def create_widgets(self):
        """Crea los elementos de la interfaz gráfica."""
        ttk.Label(self.root, text="LinkedIn Job Bot", font=("Arial", 18, "bold"), foreground="white").pack(pady=10)

        ttk.Label(self.root, text="Modo de Operación:", foreground="white").pack()
        mode_dropdown = ttk.Combobox(self.root, textvariable=self.selected_mode, values=["observacion", "semi_automatico", "full_automatico"])
        mode_dropdown.pack(pady=5)

        self.console = scrolledtext.ScrolledText(self.root, height=10, width=80, state=tk.DISABLED)
        self.console.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        frame = ttk.Frame(self.root)
        frame.pack(pady=10)
        
        ttk.Button(frame, text="Iniciar Bot", command=self.start_bot, bootstyle="primary").grid(row=0, column=0, padx=5)
        ttk.Button(frame, text="Buscar Trabajos", command=self.search_jobs, bootstyle="success").grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Aplicar Automáticamente", command=self.apply_jobs, bootstyle="warning").grid(row=0, column=2, padx=5)
        ttk.Button(frame, text="Contactar Reclutadores", command=self.message_recruiters, bootstyle="danger").grid(row=0, column=3, padx=5)
        ttk.Button(frame, text="Ver Historial", command=self.show_history, bootstyle="info").grid(row=0, column=4, padx=5)
        
    def log_message(self, message):
        """Escribe mensajes en la consola de la GUI."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"{message}\n")
        self.console.yview(tk.END)
        self.console.config(state=tk.DISABLED)

    def start_bot(self):
        """Inicia sesión en LinkedIn con Selenium."""
        email = self.config["linkedin"].get("email", "")
        password = self.config["linkedin"].get("password", "")
        mode = self.selected_mode.get()
        proxy_list = self.config.get("proxies", None)
        headless = self.config.get("headless", True)
        self.bot = LinkedInBot(email, password, mode=mode, headless=headless, proxy_list=proxy_list)
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        self.log_message("🔵 Iniciando sesión en LinkedIn...")
        if self.bot.login():
            self.log_message("✅ Sesión iniciada correctamente.")
        else:
            self.log_message("⚠️ Error en el inicio de sesión. Verifica credenciales o posibles restricciones.")

    def search_jobs(self):
        """Busca empleos y los muestra en la consola."""
        threading.Thread(target=self._search_jobs_thread, daemon=True).start()
    
    def _search_jobs_thread(self):
        self.log_message("🔍 Buscando empleos...")
        jobs = self.bot.search_jobs("Python Developer", "Argentina", max_results=5)
        for job in jobs:
            self.log_message(f"📌 {job['title']} en {job['company']} (Easy Apply: {job['easy_apply']})")
        self.log_message("✅ Búsqueda completada.")
    
    def apply_jobs(self):
        """Aplica automáticamente a empleos con Easy Apply."""
        threading.Thread(target=self._apply_jobs_thread, daemon=True).start()
    
    def _apply_jobs_thread(self):
        self.log_message("🚀 Aplicando a trabajos...")
        jobs = self.bot.search_jobs("Python Developer", "Argentina", max_results=5)
        self.bot.apply_to_jobs(jobs)
        self.log_message("✅ Aplicación completada.")

    def message_recruiters(self):
        """Contacta automáticamente a reclutadores con mensajes personalizados generados por IA."""
        threading.Thread(target=self._message_recruiters_thread, daemon=True).start()
    
    def _message_recruiters_thread(self):
        self.log_message("✉️ Preparando para contactar reclutadores...")
        
        # Función callback para generar mensajes personalizados
        def personalized_message(recruiter_name):
            prompt = f"Genera un mensaje profesional y personalizado para contactar al reclutador {recruiter_name}."
            context = {"recruiter_name": recruiter_name}
            return self.lm_studio.generate_message(prompt, context)
        
        if messagebox.askyesno("Confirmación", "¿Deseas enviar mensajes personalizados a los reclutadores?"):
            self.bot.message_recruiters(personalized_message)
            self.log_message("✅ Mensajes enviados correctamente.")
        else:
            self.log_message("🚫 Mensajes cancelados.")
    
    def show_history(self):
        """Muestra el historial de acciones guardado en la base de datos SQLite."""
        try:
            conn = self.bot.db_conn if self.bot else sqlite3.connect("history.db")
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, action, details FROM history ORDER BY timestamp DESC")
            records = cursor.fetchall()
            history_window = tk.Toplevel(self.root)
            history_window.title("Historial de Acciones")
            text_area = scrolledtext.ScrolledText(history_window, width=100, height=30)
            text_area.pack(padx=10, pady=10)
            for record in records:
                timestamp, action, details = record
                text_area.insert(tk.END, f"{timestamp} - {action}: {details}\n")
            text_area.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")

if __name__ == "__main__":
    LinkedInGUI()
