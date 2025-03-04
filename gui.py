import os
import json
import logging
import sqlite3
import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import ttkbootstrap as ttk
from tkinter.ttk import Progressbar
from bot import LinkedInBot
from linkedin_api import LinkedInAPI
from lm_studio import LMStudioInterface

db_file = "history.db"

class LinkedInGUI:
    def __init__(self, bot: LinkedInBot):
        self.bot = bot
        self.root = ttk.Window(themename="darkly")
        self.root.title("LinkedIn Bot - Gestión de Empleo")
        self.root.geometry("900x750")
        self.root.configure(bg="#2c2f33")

        self.create_widgets()
        self.root.mainloop()
    
    def create_widgets(self):
        """Crea los elementos de la interfaz gráfica."""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="🔍 LinkedIn Job Bot", font=("Arial", 18, "bold"), background="#2c2f33", foreground="#ffffff").pack(pady=10)
        
        self.console = scrolledtext.ScrolledText(frame, height=10, width=90, state=tk.DISABLED, bg="#1e1f22", fg="#00ff00")
        self.console.pack(pady=10, fill="both", expand=True)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="📁 Exportar Historial", command=self.export_history, bootstyle="primary").grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="📜 Ver Historial", command=self.view_history, bootstyle="info").grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="✏️ Editar Plantilla Reclutador", command=lambda: self.edit_template("Reclutador"), bootstyle="warning").grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="✏️ Editar Plantilla Cover Letter", command=lambda: self.edit_template("Cover Letter"), bootstyle="warning").grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="📊 Ver Compatibilidad Trabajos", command=self.show_job_compatibility, bootstyle="success").grid(row=0, column=4, padx=5)
    
    def log_message(self, message):
        """Escribe en la consola de la GUI."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"{message}\n")
        self.console.yview(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def export_history(self):
        """Exporta el historial de mensajes y aplicaciones guardadas en SQLite."""
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history")
        data = cursor.fetchall()
        conn.close()

        if not data:
            messagebox.showinfo("Exportación", "No hay datos en el historial.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("id, action, details, timestamp\n")
                for row in data:
                    f.write(",".join(map(str, row)) + "\n")
            messagebox.showinfo("Exportación", f"Historial exportado correctamente a {file_path}.")
            self.log_message("✅ Historial exportado con éxito.")

    def view_history(self):
        """Muestra el historial de mensajes y aplicaciones guardadas en SQLite."""
        self.log_message("📜 Cargando historial...")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT action, details, timestamp FROM history ORDER BY timestamp DESC")
        records = cursor.fetchall()
        conn.close()

        history_text = "\n".join([f"{rec[0]} | {rec[1]} | {rec[2]}" for rec in records])
        self.log_message(history_text if history_text else "⚠️ No hay registros en el historial.")
    
    def edit_template(self, template_type):
        """Permite editar las plantillas de mensajes o cover letters desde la GUI."""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt *.md")])
        if not file_path:
            return
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        edit_window = tk.Toplevel()
        edit_window.title(f"Editar Plantilla - {template_type}")
        edit_window.geometry("600x400")

        text_area = scrolledtext.ScrolledText(edit_window, height=20, width=80)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content)

        def save_template():
            new_content = text_area.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            messagebox.showinfo("Guardado", "Plantilla actualizada correctamente.")
            edit_window.destroy()
            self.log_message(f"✅ Plantilla {template_type} actualizada.")

        save_button = ttk.Button(edit_window, text="Guardar", command=save_template)
        save_button.pack(pady=10)
    
    def show_job_compatibility(self):
        """Muestra el puntaje de compatibilidad de los trabajos encontrados."""
        self.log_message("🔍 Analizando compatibilidad de trabajos...")
        jobs = self.bot.linkedin.search_jobs(["Python", "NextJS"])
        compatibility_results = "\n".join([f"{job.get('title')} | {job.get('company')} | {self.bot._calculate_compatibility(job.get('description', ''), ['Python', 'NextJS'])}%" for job in jobs])
        self.log_message(compatibility_results if compatibility_results else "⚠️ No se encontraron trabajos.")

if __name__ == "__main__":
    linkedin_api = LinkedInAPI(client_id="", client_secret="", redirect_uri="")
    lm_studio = LMStudioInterface()
    bot = LinkedInBot(linkedin_api, lm_studio)
    LinkedInGUI(bot)