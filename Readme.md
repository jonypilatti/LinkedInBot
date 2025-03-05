# **LinkedInBot 🤖 - Automated LinkedIn Job Search & Messaging Bot**

LinkedInBot is a Python-based automation tool that interacts with LinkedIn to:

- **Search for jobs** based on specific keywords and location.
- **Apply to jobs** using the "Easy Apply" feature.
- **Send personalized messages** to recruiters with AI-generated responses via **LM Studio**.
- **Operate in different modes**: `observacion`, `semi_automatico`, and `full_automatico`.
- **Log actions** into an SQLite database for tracking.
- **Control automation via a GUI** using `tkinter` and `ttkbootstrap`.

---

## **📌 Features**

👉 **Automated LinkedIn login** using credentials stored in `.env`.  
👉 **Job search and filtering** based on keywords & location.  
👉 **Automated job applications** with the "Easy Apply" feature.  
👉 **AI-powered recruiter messaging** via **LM Studio**.  
👉 **Graphical User Interface (GUI)** for easy bot control.  
👉 **Headless mode** for running automation without a visible browser.  
👉 **Proxy support** for enhanced security.  
👉 **SQLite logging** to track performed actions.

---

## **🚀 Installation & Setup**

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/LinkedInBot.git
cd LinkedInBot
```

### **2️⃣ Create a Virtual Environment (Optional but Recommended)**

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### **3️⃣ Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4️⃣ Set Up Environment Variables**

Create a `.env` file in the root directory and add the following:

```ini
# LinkedIn Credentials
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-secure-password

# Proxy Configuration (optional, separated by commas)
LINKEDIN_PROXIES=proxy1:port,proxy2:port

# Headless Mode (True to run in background, False to see browser interactions)
HEADLESS=True

# LM Studio API Configuration
LM_API_URL=http://localhost:1234/v1
LM_TIMEOUT=10
LM_RETRIES=3
```

⚠️ **Warning:** Do NOT share your `.env` file, as it contains sensitive data.

---

### **5️⃣ Run LM Studio (For AI Messaging)**

If you are using LM Studio for recruiter messaging, start the server before running the bot:

```bash
lm-studio --server --port 1234
```

Alternatively, check that LM Studio is running by testing its API:

```bash
curl http://localhost:1234/status
```

---

## **🎮 Running the Bot**

### **Start the GUI**

```bash
python gui.py
```

This opens an interactive window where you can:

- **Start the bot**
- **Search for jobs**
- **Apply automatically**
- **Send recruiter messages**
- **View application history**
- **Export logs to CSV**

### **Run the Bot in CLI Mode (Optional)**

To run the bot directly without a GUI, modify and use the script below:

```python
from bot import LinkedInBot

bot = LinkedInBot()
bot.login()
jobs = bot.search_jobs("Python Developer", "Remote", max_results=5)
bot.apply_to_jobs(jobs)
bot.close()
```

---

## **🛠️ Technologies Used**

- **Python 3.8+** (Main programming language)
- **Selenium** (Web automation)
- **WebDriver Manager** (Chrome driver auto-install)
- **Requests** (API interactions with LM Studio)
- **ttkbootstrap** (GUI framework for enhanced styling)
- **SQLite** (Local database for action history)
- **python-dotenv** (Secure environment variable management)

---

## **📝 Logs & Database**

All actions (job searches, applications, messages) are stored in `history.db`. Use the GUI to view or export logs to a CSV file.

---

## **💬 Contact**

Have any issues or suggestions? Feel free to open an issue or reach out via LinkedIn! 🚀
