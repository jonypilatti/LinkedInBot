# LinkedIn Job Search Bot (Automatización Web)

Este bot automatiza la búsqueda de empleo en LinkedIn utilizando **automatización web con Selenium**, permitiendo: ✅ **Iniciar sesión automáticamente** en LinkedIn.  
✅ **Buscar empleos filtrando por _Easy Apply_**.  
✅ **Aplicar automáticamente** a trabajos con Easy Apply.  
✅ **Enviar mensajes automáticos a reclutadores**.  
✅ **Mantener un historial de acciones en SQLite**.

## 🛠 Tecnologías Utilizadas

- **Selenium + Undetected ChromeDriver**: Automatización web sin ser detectado.
- **Tkinter + ttkbootstrap (futuro agregado)**: Para una interfaz gráfica moderna.
- **SQLite**: Para almacenar historial de postulaciones.
- **WebDriver Manager**: Para manejar la versión correcta de ChromeDriver.

## 📂 Estructura del Proyecto

```
linkedin-bot/
├─ bot.py                   # Lógica principal del bot (Selenium)
├─ gui.py                   # Interfaz gráfica (por implementar)
├─ client_interface.py       # Punto de entrada principal
├─ requirements.txt         # Dependencias del proyecto
├─ README.md                # Documentación del proyecto
└─ history.db               # Base de datos SQLite (opcional)
```

## 🔧 Instalación y Configuración

### 1️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Ejecutar el bot

```bash
python bot.py
```

⚠️ **Antes de ejecutar, edita `bot.py` y coloca tu usuario y contraseña de LinkedIn**:

```python
bot = LinkedInBot(email="tu_email", password="tu_contraseña")
```

## 🐳 Uso con Docker (próximamente)

🚀 **¿Qué sigue?**

- **Agregar una GUI interactiva** para ver logs en tiempo real.
- **Optimizar la detección de trabajos relevantes con IA**.
- **Soporte para manejo de captchas si LinkedIn los detecta**.
