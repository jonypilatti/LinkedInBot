"""
LinkedIn Bot Client Interface
----------------------------
A simple interface to interact with the LinkedIn Job Search Bot
"""

import sys
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Dict, List, Any
from datetime import datetime
import requests
# Import the updated bot classes (with error handling and token management)
from linkedin_bot import LinkedInAPI, LMStudioInterface, LinkedInBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("linkedin_bot_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInBotGUI:
    """GUI for the LinkedIn Job Search Bot"""
    
    def __init__(self, root):
        """Initialize the GUI"""
        self.root = root
        self.root.title("LinkedIn Job Search Bot")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        self.bot = None
        self.is_bot_initialized = False
        
        # Configuration frame
        self.create_config_frame()
        
        # Main functionality tabs
        self.create_tabs()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load saved configuration
        self.load_config()
    
    def create_config_frame(self):
        """Create configuration frame"""
        config_frame = ttk.LabelFrame(self.root, text="LinkedIn & LM Studio Configuration")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # LinkedIn API credentials
        ttk.Label(config_frame, text="LinkedIn Client ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.client_id_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.client_id_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(config_frame, text="LinkedIn Client Secret:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.client_secret_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.client_secret_var, width=30, show="*").grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(config_frame, text="Redirect URI:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.redirect_uri_var = tk.StringVar(value="http://localhost:8000/callback")
        ttk.Entry(config_frame, textvariable=self.redirect_uri_var, width=30).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # LM Studio configuration
        ttk.Label(config_frame, text="LM Studio API URL:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.lm_studio_url_var = tk.StringVar(value="http://localhost:1234/v1")
        ttk.Entry(config_frame, textvariable=self.lm_studio_url_var, width=30).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Current company (to exclude)
        ttk.Label(config_frame, text="Your Current Company:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.current_company_var = tk.StringVar(value="Stori")
        ttk.Entry(config_frame, textvariable=self.current_company_var, width=30).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Skills
        ttk.Label(config_frame, text="Your Skills:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.skills_var = tk.StringVar(value="NextJS/Python with FastAPI or NodeJS+ExpressJS")
        ttk.Entry(config_frame, textvariable=self.skills_var, width=30).grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ttk.Button(buttons_frame, text="Initialize Bot", command=self.initialize_bot).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Test LM Studio", command=self.test_lm_studio).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Authenticate LinkedIn", command=self.authenticate_linkedin).pack(side=tk.LEFT, padx=5)
    
    def create_tabs(self):
        """Create main functionality tabs"""
        self.tab_control = ttk.Notebook(self.root)
        
        # Contact recruiters tab
        self.recruiter_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.recruiter_tab, text="Contact Recruiters")
        self.setup_recruiter_tab()
        
        # Job application tab
        self.job_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.job_tab, text="Apply to Jobs")
        self.setup_job_tab()
        
        # Chat tab
        self.chat_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.chat_tab, text="Chat with Assistant")
        self.setup_chat_tab()
        
        # Log tab
        self.log_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.log_tab, text="Logs")
        self.setup_log_tab()
        
        self.tab_control.pack(expand=1, fill=tk.BOTH, padx=10, pady=10)
    
    def setup_recruiter_tab(self):
        """Setup recruiter contact tab"""
        frame = ttk.Frame(self.recruiter_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Options
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_frame, text="Maximum recruiters to contact:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_recruiters_var = tk.IntVar(value=10)
        ttk.Spinbox(options_frame, from_=1, to=100, textvariable=self.max_recruiters_var, width=5).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(options_frame, text="Delay between messages (seconds):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.message_delay_var = tk.IntVar(value=5)
        ttk.Spinbox(options_frame, from_=1, to=60, textvariable=self.message_delay_var, width=5).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Message template
        template_frame = ttk.LabelFrame(frame, text="Message Template")
        template_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.message_template_text = scrolledtext.ScrolledText(template_frame, height=10)
        self.message_template_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.message_template_text.insert(tk.END, """Hello {recruiter_name},

I noticed you're a {recruiter_title} at {recruiter_company}. I'm currently exploring new opportunities as a Full Stack Engineer with expertise in {skills}.

{personalized_note}

I'd appreciate the opportunity to discuss how my skills might align with roles you're currently hiring for.

Best regards,
{user_name}""")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Find Recruiters", command=self.find_recruiters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Contacting", command=self.start_contacting_recruiters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_operation).pack(side=tk.LEFT, padx=5)
        
        # Results
        results_frame = ttk.LabelFrame(frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.recruiter_results_text = scrolledtext.ScrolledText(results_frame, height=10)
        self.recruiter_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_job_tab(self):
        """Setup job application tab"""
        frame = ttk.Frame(self.job_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Search options
        search_frame = ttk.LabelFrame(frame, text="Job Search Options")
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Keywords (comma separated):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.keywords_var = tk.StringVar(value="full stack, nextjs, python, fastapi, nodejs, expressjs")
        ttk.Entry(search_frame, textvariable=self.keywords_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(search_frame, text="Location:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.location_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.location_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(search_frame, text="Maximum jobs to apply:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_jobs_var = tk.IntVar(value=20)
        ttk.Spinbox(search_frame, from_=1, to=100, textvariable=self.max_jobs_var, width=5).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Easy Apply Only checkbox
        self.easy_apply_only_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(search_frame, text="Easy Apply Only", variable=self.easy_apply_only_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Search Jobs", command=self.search_jobs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Applying", command=self.start_applying_jobs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_operation).pack(side=tk.LEFT, padx=5)
        
        # Results
        results_frame = ttk.LabelFrame(frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.job_results_text = scrolledtext.ScrolledText(results_frame, height=10)
        self.job_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_chat_tab(self):
        """Setup chat tab (AI assistant interface)"""
        frame = ttk.Frame(self.chat_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat history
        self.chat_history = scrolledtext.ScrolledText(frame, state=tk.DISABLED, height=15)
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.chat_input = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=self.chat_input, width=60)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(input_frame, text="Send", command=self.send_chat_message).pack(side=tk.LEFT, padx=5)
    
    def setup_log_tab(self):
        """Setup log tab to view the logs"""
        frame = ttk.Frame(self.log_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Auto-refresh check
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Auto Refresh Logs", variable=self.auto_refresh_var).pack(anchor=tk.W)
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(frame, state=tk.DISABLED, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Manual refresh button
        ttk.Button(frame, text="Refresh Logs", command=self.load_logs).pack(pady=5)
    
    def load_config(self):
        """Load previously saved config from config.json (if any)"""
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                self.client_id_var.set(cfg["linkedin"]["client_id"])
                self.client_secret_var.set(cfg["linkedin"]["client_secret"])
                self.redirect_uri_var.set(cfg["linkedin"]["redirect_uri"])
                self.lm_studio_url_var.set(cfg["lm_studio"]["api_url"])
                self.current_company_var.set(cfg["options"]["current_company"])
                self.skills_var.set(cfg["options"]["skills"])
        except Exception as e:
            logger.warning(f"No config loaded or invalid. Reason: {e}")
    
    def save_config(self):
        """Save current config to config.json"""
        cfg = {
            "linkedin": {
                "client_id": self.client_id_var.get(),
                "client_secret": self.client_secret_var.get(),
                "redirect_uri": self.redirect_uri_var.get()
            },
            "lm_studio": {
                "api_url": self.lm_studio_url_var.get()
            },
            "options": {
                "current_company": self.current_company_var.get(),
                "skills": self.skills_var.get()
            }
        }
        with open("config.json", "w") as f:
            json.dump(cfg, f, indent=2)
        self.update_status("Configuration saved.")
    
    def initialize_bot(self):
        """Create instances of the LinkedInAPI, LMStudioInterface, and LinkedInBot"""
        self.linkedin_api = LinkedInAPI(
            client_id=self.client_id_var.get(),
            client_secret=self.client_secret_var.get(),
            redirect_uri=self.redirect_uri_var.get()
        )
        self.lm_studio = LMStudioInterface(
            api_url=self.lm_studio_url_var.get()
        )
        self.bot = LinkedInBot(self.linkedin_api, self.lm_studio)
        
        self.is_bot_initialized = True
        self.update_status("Bot initialized. You can now authenticate or perform actions.")
    
    def authenticate_linkedin(self):
        """Prompt for an auth code and authenticate with LinkedIn"""
        if not self.is_bot_initialized or not self.bot:
            messagebox.showerror("Error", "Please initialize the bot first.")
            return
        
        auth_code = simpledialog.askstring("LinkedIn Auth", "Enter the Auth code from LinkedIn:")
        if auth_code:
            success = self.bot.linkedin.authenticate(auth_code)
            if success:
                self.update_status("LinkedIn authenticated successfully!")
            else:
                self.update_status("Failed to authenticate LinkedIn.")
        else:
            self.update_status("No auth code provided.")
    
    def test_lm_studio(self):
        """Quick check to see if LM Studio can respond"""
        if not self.is_bot_initialized or not self.bot:
            messagebox.showerror("Error", "Please initialize the bot first.")
            return
        # Just ask a dummy prompt
        response = self.bot.lm_studio.generate_message("Hello from the test!", {})
        if response:
            self.update_status("LM Studio responded successfully.")
        else:
            self.update_status("LM Studio did not respond. Check console for errors.")
    
    def find_recruiters(self):
        """Find recruiter connections (simply logs the result)"""
        if not self.check_bot_initialized_and_authenticated():
            return
        
        # Filter by user-specified company
        recruiters = self.bot.linkedin.filter_recruiter_connections(
            exclude_company=self.current_company_var.get()
        )
        self.update_recruiter_results(f"Found {len(recruiters)} recruiters.\n")
    
    def start_contacting_recruiters(self):
        """Contact recruiters with user-defined template"""
        if not self.check_bot_initialized_and_authenticated():
            return
        
        # We can run this in a thread so it doesn't block the GUI
        def worker():
            max_recruiters = self.max_recruiters_var.get()
            delay = self.message_delay_var.get()
            
            # Overwrite the default template with the user's custom text
            self.bot.recruiter_message_template = self.message_template_text.get("1.0", tk.END)
            
            results = self.bot.contact_recruiters(skills=self.skills_var.get())
            
            # Log summary
            msg = f"Contacted {results['success']} recruiters, failed {results['failed']}."
            self.update_recruiter_results(msg + "\n")
            self.update_status("Finished contacting recruiters.")
        
        t = threading.Thread(target=worker)
        t.start()
    
    def stop_operation(self):
        """Stub to allow user to stop any running operation (not fully implemented)"""
        self.update_status("Stop is not fully implemented yet.")
    
    def search_jobs(self):
        """Search for jobs based on user input"""
        if not self.check_bot_initialized_and_authenticated():
            return
        
        keywords = [kw.strip() for kw in self.keywords_var.get().split(",")]
        location = self.location_var.get()
        easy_apply = self.easy_apply_only_var.get()
        
        jobs = self.bot.linkedin.search_jobs(keywords, location, easy_apply_only=easy_apply)
        self.update_job_results(f"Found {len(jobs)} jobs.\n")
    
    def start_applying_jobs(self):
        """Apply to Easy Apply jobs automatically"""
        if not self.check_bot_initialized_and_authenticated():
            return
        
        # We can run this in a thread so it doesn't block the GUI
        def worker():
            keywords = [kw.strip() for kw in self.keywords_var.get().split(",")]
            location = self.location_var.get()
            results = self.bot.apply_to_jobs(keywords=keywords, location=location)
            
            msg = f"Applied to {results['applied']} jobs out of {results['searched']}"
            self.update_job_results(msg + "\n")
            self.update_status("Finished applying to jobs.")
        
        t = threading.Thread(target=worker)
        t.start()
    
    def send_chat_message(self):
        """Send a chat message to the AI assistant"""
        if not self.check_bot_initialized_and_authenticated():
            return
        
        user_message = self.chat_input.get().strip()
        if not user_message:
            return
        
        # Display user message
        self.add_to_chat("You", user_message)
        self.chat_input.set("")
        
        # Call LM Studio
        response = self.bot.lm_studio.generate_message(user_message, {})
        self.add_to_chat("Assistant", response)
    
    def load_logs(self):
        """Load logs from file"""
        try:
            with open("linkedin_bot.log", "r") as f:
                log_content = f.read()
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, log_content)
            self.log_text.config(state=tk.DISABLED)
            
            self.log_text.see(tk.END)
        except FileNotFoundError:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, "No log file found.")
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
    
    def add_to_chat(self, sender, message):
        """Add a message to chat history with timestamps and coloring"""
        self.chat_history.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_history.insert(tk.END, f"[{timestamp}] ")
        
        # Add sender with styling
        if sender == "You":
            self.chat_history.insert(tk.END, f"{sender}: ", "user")
        elif sender == "Assistant":
            self.chat_history.insert(tk.END, f"{sender}: ", "assistant")
        else:
            self.chat_history.insert(tk.END, f"{sender}: ", "system")
        
        # Add message
        self.chat_history.insert(tk.END, f"{message}\n\n")
        
        # Auto-scroll
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update status bar message"""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def update_recruiter_results(self, message):
        """Update recruiter results text area"""
        self._update_text_widget(self.recruiter_results_text, message)
    
    def update_job_results(self, message):
        """Update job results text area"""
        self._update_text_widget(self.job_results_text, message)
    
    def _update_text_widget(self, widget, message):
        """Helper to update text widget from another thread"""
        widget.config(state=tk.NORMAL)
        widget.insert(tk.END, message)
        widget.see(tk.END)
        widget.config(state=tk.DISABLED)
    
    def check_bot_initialized_and_authenticated(self):
        """Check if bot is initialized and authenticated"""
        if not self.is_bot_initialized:
            messagebox.showerror("Error", "Please initialize the bot first")
            return False
        
        if not self.bot.linkedin.access_token:
            messagebox.showerror("Error", "Please authenticate with LinkedIn first")
            return False
        
        return True


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = LinkedInBotGUI(root)
    
    # Configure styles
    style = ttk.Style()
    style.configure("TButton", padding=6)
    style.configure("TLabel", padding=3)
    
    # Tag configuration for chat
    app.chat_history.tag_configure("user", foreground="blue")
    app.chat_history.tag_configure("assistant", foreground="green")
    app.chat_history.tag_configure("system", foreground="red")
    
    # Auto-refresh logs
    def refresh_logs():
        if getattr(app, "auto_refresh_var", None) and app.auto_refresh_var.get():
            app.load_logs()
        root.after(5000, refresh_logs)  # Refresh every 5 seconds
    
    refresh_logs()
    
    root.mainloop()


if __name__ == "__main__":
    main()
