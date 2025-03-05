import os
import tkinter as tk
import ttkbootstrap as ttk

from tkinter import scrolledtext, messagebox, filedialog
import threading
import time
import random
import sqlite3
import csv
from bot import LinkedInBot
from lm_interface import LMStudioInterface

class LinkedInGUI:
    def __init__(self):
        # Se leen las variables de entorno necesarias.
        self.linkedin_email = os.environ.get("LINKEDIN_EMAIL")
        self.linkedin_password = os.environ.get("LINKEDIN_PASSWORD")
        if not self.linkedin_email or not self.linkedin_password:
            messagebox.showerror("Error de Configuración", 
                                 "Las variables de entorno LINKEDIN_EMAIL y LINKEDIN_PASSWORD son obligatorias.")
            exit(1)

        # Variable opcional para proxies (se esperan separados por comas)
        proxy_str = os.environ.get("LINKEDIN_PROXIES")
        self.proxy_list = [proxy.strip() for proxy in proxy_str.split(",")] if proxy_str else None

        # Variable opcional para modo headless
        headless_str = os.environ.get("HEADLESS", "True")
        self.headless = headless_str.lower() in ["true", "1", "yes"]

        # Variable opcional para la URL de LM Studio
        self.lm_api_url = os.environ.get("LM_API_URL", "http://localhost:1234/v1")

        self.root = ttk.Window(themename="darkly")
        self.root.title("LinkedIn Job Search Bot")
        self.root.geometry("850x700")

        self.bot = None
        # Se pasa la URL obtenida desde la variable de entorno a LMStudioInterface
        self.lm_studio = LMStudioInterface(api_url=self.lm_api_url)
        self.selected_mode = tk.StringVar(value="observacion")
        self.paused = False
        
        self.create_widgets()
        # Inicia el panel de estadísticas
        self.update_stats()
        self.root.mainloop()

    def create_widgets(self):
        """Crea los elementos de la interfaz gráfica."""
        ttk.Label(self.root, text="LinkedIn Job Bot", font=("Arial", 18, "bold"), foreground="white").pack(pady=10)

        ttk.Label(self.root, text="Modo de Operación:", foreground="white").pack()
        mode_dropdown = ttk.Combobox(self.root, textvariable=self.selected_mode, 
                                     values=["observacion", "semi_automatico", "full_automatico"])
        mode_dropdown.pack(pady=5)

        self.console = scrolledtext.ScrolledText(self.root, height=10, width=90, state=tk.DISABLED)
        self.console.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        frame = ttk.Frame(self.root)
        frame.pack(pady=10)
        
        self.start_bot_button = ttk.Button(frame, text="Iniciar Bot", command=self.start_bot, bootstyle="primary")
        self.start_bot_button.grid(row=0, column=0, padx=5)
        
        self.search_jobs_button = ttk.Button(frame, text="Buscar Trabajos", command=self.search_jobs, bootstyle="success")
        self.search_jobs_button.grid(row=0, column=1, padx=5)
        
        self.apply_jobs_button = ttk.Button(frame, text="Aplicar Automáticamente", command=self.apply_jobs, bootstyle="warning")
        self.apply_jobs_button.grid(row=0, column=2, padx=5)
        
        self.message_recruiters_button = ttk.Button(frame, text="Contactar Reclutadores", command=self.message_recruiters, bootstyle="danger")
        self.message_recruiters_button.grid(row=0, column=3, padx=5)
        
        self.show_history_button = ttk.Button(frame, text="Ver Historial", command=self.show_history, bootstyle="info")
        self.show_history_button.grid(row=0, column=4, padx=5)
        
        self.pause_resume_button = ttk.Button(frame, text="Pausar/Reanudar", command=self.toggle_pause, bootstyle="secondary")
        self.pause_resume_button.grid(row=0, column=5, padx=5)
        
        self.export_history_button = ttk.Button(frame, text="Exportar Historial CSV", command=self.export_history, bootstyle="outline")
        self.export_history_button.grid(row=0, column=6, padx=5)

        # Panel para estadísticas
        self.stats_label = ttk.Label(self.root, text="Estadísticas: ", foreground="white", font=("Arial", 12))
        self.stats_label.pack(pady=5)

    def set_buttons_state(self, state):
        """Cambia el estado de los botones (normal o disabled)."""
        self.start_bot_button.config(state=state)
        self.search_jobs_button.config(state=state)
        self.apply_jobs_button.config(state=state)
        self.message_recruiters_button.config(state=state)
        self.show_history_button.config(state=state)
        self.pause_resume_button.config(state=state)
        self.export_history_button.config(state=state)

    def log_message(self, message):
        """Escribe mensajes en la consola de la GUI."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"{message}\n")
        self.console.yview(tk.END)
        self.console.config(state=tk.DISABLED)

    def start_bot(self):
        """Inicia sesión en LinkedIn con Selenium."""
        self.set_buttons_state("disabled")
        mode = self.selected_mode.get()
        self.bot = LinkedInBot(self.linkedin_email, self.linkedin_password, 
                               mode=mode, headless=self.headless, proxy_list=self.proxy_list)
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        self.log_message("🔵 Iniciando sesión en LinkedIn...")
        if self.bot.login():
            self.log_message("✅ Sesión iniciada correctamente.")
        else:
            self.log_message("⚠️ Error en el inicio de sesión. Verifica credenciales o posibles restricciones.")
        self.set_buttons_state("normal")

    def search_jobs(self):
        """Busca empleos y los muestra en la consola."""
        self.set_buttons_state("disabled")
        threading.Thread(target=self._search_jobs_thread, daemon=True).start()
    
    def _search_jobs_thread(self):
        self.log_message("🔍 Buscando empleos...")
        jobs = self.bot.search_jobs("Python Developer", "Argentina", max_results=5)
        for job in jobs:
            self.log_message(f"📌 {job['title']} en {job['company']} (Easy Apply: {job['easy_apply']})")
        self.log_message("✅ Búsqueda completada.")
        self.set_buttons_state("normal")
    
    def apply_jobs(self):
        """Aplica automáticamente a empleos con Easy Apply."""
        self.set_buttons_state("disabled")
        threading.Thread(target=self._apply_jobs_thread, daemon=True).start()
    
    def _apply_jobs_thread(self):
        self.log_message("🚀 Aplicando a trabajos...")
        # Llamamos a la nueva función integrada que busca y aplica uno a uno.
        self.bot.search_and_apply_jobs("Python Developer", "Argentina", max_results=5)
        self.log_message("✅ Aplicación completada.")
        self.set_buttons_state("normal")

    def message_recruiters(self):
        """Contacta automáticamente a reclutadores con mensajes personalizados generados por IA."""
        self.set_buttons_state("disabled")
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
        self.set_buttons_state("normal")

    def toggle_pause(self):
        """Alterna el estado de pausa del bot."""
        if not self.bot:
            messagebox.showwarning("Advertencia", "El bot no está iniciado.")
            return
        if self.bot.paused:
            self.bot.resume()
            self.log_message("▶️ Bot reanudado.")
        else:
            self.bot.pause()
            self.log_message("⏸️ Bot pausado.")

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

    def export_history(self):
        """Exporta el historial de la base de datos a un archivo CSV."""
        try:
            conn = self.bot.db_conn if self.bot else sqlite3.connect("history.db")
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, action, details FROM history ORDER BY timestamp DESC")
            records = cursor.fetchall()
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
            if not file_path:
                return
            with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Timestamp", "Action", "Details"])
                for record in records:
                    writer.writerow(record)
            messagebox.showinfo("Éxito", f"Historial exportado a {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el historial: {e}")

    def update_stats(self):
        """Actualiza el panel de estadísticas cada 5 segundos."""
        if self.bot:
            stats = self.bot.get_stats()
            self.stats_label.config(text=f"Estadísticas: Aplicaciones: {stats['applied']} | Mensajes: {stats['messages']}")
        self.root.after(5000, self.update_stats)

if __name__ == "__main__":
    LinkedInGUI()
