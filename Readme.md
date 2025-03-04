# LinkedIn Job Search Bot

Este bot automatiza la búsqueda de empleo en LinkedIn con ayuda de **inteligencia artificial**, permitiendo contactar reclutadores y aplicar a trabajos de manera automatizada. Ahora cuenta con una **interfaz gráfica moderna**, almacenamiento de historial y mejoras en la compatibilidad con Docker.

## 🛠 Tecnologías Utilizadas

- **python3-linkedin**: Cliente de LinkedIn para autenticación y manejo de perfiles.
- **requests**: Para llamadas REST a la API de LinkedIn.
- **tkinter + ttkbootstrap**: Interfaz gráfica con logs en vivo y diseño moderno.
- **pytest y unittest**: Para pruebas unitarias.
- **LM Studio**: IA generativa para mensajes y cover letters.
- **backoff**: Manejo de reintentos automáticos en LinkedIn.
- **SQLite**: Base de datos para almacenar historial de interacciones.
- **Docker y Docker Compose**: Para ejecutar el bot en un entorno aislado.

## 🚀 Características

✅ **Interfaz gráfica (GUI) con logs en vivo y diseño oscuro.**  
✅ **Autenticación con LinkedIn y reuso de tokens.**  
✅ **Mensajería automática a reclutadores con IA.**  
✅ **Búsqueda de empleos y aplicación automática.**  
✅ **Historial de mensajes y postulaciones en SQLite.**  
✅ **Exportación de resultados a CSV.**  
✅ **Compatibilidad con Docker.**

## 📂 Estructura del Proyecto

```
linkedin-bot/
├─ client_interface.py       # Punto de entrada principal
├─ linkedin_api.py          # Autenticación y API de LinkedIn
├─ lm_studio.py             # Generación de mensajes con IA
├─ bot.py                   # Lógica principal del bot
├─ gui.py                   # Interfaz gráfica con logs
├─ config.json              # Configuración de credenciales
├─ requirements.txt         # Dependencias del proyecto
├─ Dockerfile               # Configuración del contenedor
├─ docker-compose.yml       # Orquestación de contenedores
├─ history.db               # Base de datos SQLite (opcional)
└─ README.md                # Documentación del proyecto
```

## 🔧 Configuración

### 1️⃣ Crear una aplicación en LinkedIn Developer Portal

1. Ir a [LinkedIn Developer Portal](https://www.linkedin.com/developers/).
2. Crear una aplicación y obtener `client_id` y `client_secret`.
3. Configurar `redirect_uri` como `http://localhost:8000/callback`.

### 2️⃣ Configurar `config.json`

```json
{
  "linkedin": {
    "client_id": "TU_CLIENT_ID",
    "client_secret": "TU_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8000/callback"
  },
  "lm_studio": {
    "api_url": "http://localhost:1234/v1"
  }
}
```

### 3️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4️⃣ Ejecutar el bot

```bash
python client_interface.py
```

## 🐳 Uso con Docker

### 1️⃣ Construir y ejecutar el contenedor

```bash
docker-compose up --build
```

### 2️⃣ Ejecutar pruebas dentro del contenedor

```bash
docker-compose run test
```

### 3️⃣ Acceder al historial de SQLite

```bash
docker exec -it linkedin-db sqlite3 /var/lib/sqlite3/history.db
```

## 📌 Notas Adicionales

- **Token de Acceso**: Si el token expira, el bot permite reautenticarse sin reiniciar la aplicación.
- **Historial en SQLite**: Registra acciones en `history.db`.
- **Internacionalización (i18n)**: La interfaz puede traducirse a otros idiomas en futuras actualizaciones.

---

🔗 **Para más información, revisa la [documentación de LinkedIn API](https://docs.microsoft.com/en-us/linkedin/).**
