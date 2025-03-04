# LinkedIn Job Search Bot

Este bot automatiza la búsqueda de empleo en LinkedIn con ayuda de **inteligencia artificial**, permitiendo contactar reclutadores y aplicar a trabajos de manera automatizada. Utiliza la biblioteca **python3-linkedin** para la autenticación y la **API REST de LinkedIn Talent Solutions** para funcionalidades avanzadas, como búsqueda y aplicación a empleos.

## Tecnologías Utilizadas

- [**python3-linkedin**](https://github.com/ozgur/python-linkedin): Cliente oficial de LinkedIn para autenticación y manejo de perfiles.
- [**requests**](https://docs.python-requests.org/): Para realizar llamadas REST a la API de LinkedIn.
- [**tkinter**](https://docs.python.org/3/library/tkinter.html): Proporciona una **interfaz gráfica** para facilitar la interacción con el bot.
- [**pytest**](https://docs.pytest.org/) y [**unittest**](https://docs.python.org/3/library/unittest.html): Para pruebas unitarias.
- [**LM Studio**](https://lmstudio.ai/): Genera mensajes personalizados con IA (por ejemplo, para contactar reclutadores o redactar cover letters).
- [**backoff**](https://pypi.org/project/backoff/): Maneja reintentos automáticos en solicitudes a la API de LinkedIn, ayudando con errores temporales.
- [**asyncio**](https://docs.python.org/3/library/asyncio.html): Permite una mejor concurrencia en la ejecución del bot (opcional).

## Características

- **Interfaz gráfica (GUI)**: Construida en Tkinter, con área de logs en tiempo real, barra de progreso y controles básicos.
- **Autenticación con LinkedIn**: Usa `python3-linkedin` para gestionar el token de acceso y soporta reautenticación si expira.
- **Obtención de perfil y conexiones**: Recupera información básica del usuario y lista de conexiones.
- **Mensajería a reclutadores**: Envía mensajes personalizados usando plantillas y LM Studio.
- **Búsqueda de empleos**: Integra la API Talent Solutions de LinkedIn (sujeto a permisos) para encontrar ofertas.
- **Aplicación a empleos**: Envía solicitudes automáticamente a empleos con "Easy Apply".
- **Reintentos y manejo de Rate Limit**: Usa `backoff` y chequea código 429 para evitar bloqueos.
- **Logs en vivo**: Muestra el estado en la GUI y en un archivo de log.
- **Modo oscuro**: Permite alternar entre tema claro y oscuro.
- **Exportación a CSV**: Guarda los resultados de búsqueda en un archivo .csv en la ubicación elegida.
- **Historial en SQLite**: (opcional) Guarda información de postulaciones y mensajes en una base local.

## Estructura del Proyecto (Código Modular)

A continuación se sugiere dividir el código en múltiples módulos para una mejor organización:

```
linkedin-bot/
├─ client_interface.py           # Punto de entrada principal
├─ linkedin_api.py              # Maneja autenticación y llamadas REST a LinkedIn
├─ lm_studio.py                 # Conexión con LM Studio para IA
├─ bot.py                       # Lógica principal: contactar, aplicar, plantillas, historial
├─ gui.py                       # Interfaz gráfica en Tkinter
├─ config.json                  # Configuración de credenciales y endpoints
├─ requirements.txt             # Dependencias
├─ history.db                   # DB local (opcional) para historial
└─ README.md
```

- **linkedin_api.py**: Contiene la clase `LinkedInAPI`, que combina la autenticación con `python3-linkedin` y llamadas REST.
- **lm_studio.py**: Clase `LMStudioInterface`, genera mensajes con IA (plantillas para reclutadores, cover letters, etc.).
- **bot.py**: Clase `LinkedInBot`, coordina la API y la IA, maneja la lógica de contacto y postulaciones.
- **gui.py**: Clase `LinkedInGUI`, construida en Tkinter; se encarga de la interfaz con área de logs, modo oscuro, etc.
- **client_interface.py**: Archivo principal para iniciar la aplicación, leer `config.json` y lanzar la GUI.

## Configuración

### Requisitos

1. **Crear una aplicación en LinkedIn Developer Portal** ([Enlace](https://www.linkedin.com/developers/))

   - Obtener `client_id` y `client_secret`.
   - Configurar `redirect_uri` (ejemplo: `http://localhost:8000/callback`).

2. **config.json**

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

3. **Instalar dependencias**

   ```bash
   pip install requests python3-linkedin pytest backoff asyncio
   ```

4. **Ejecución**

   ```bash
   python client_interface.py
   ```

## Uso

### Autenticación

El bot usa `python3-linkedin` para autenticar usuarios y obtener un token de acceso. Si el token está guardado en `linkedin_token.json`, lo reutiliza. El proceso es manejado por la GUI.

### Contactar Reclutadores

1. **Buscar conexiones**: Obtiene la lista de conexiones.
2. **Enviar mensajes**: Usa plantillas (personalizables) y LM Studio para redactar mensajes.

### Búsqueda y Aplicación de Empleos

```python
bot.search_jobs(["Software Engineer", "Python"], location="Argentina", easy_apply_only=True)
```

```python
bot.apply_to_job("job_id")
```

O un proceso automático:

```python
bot.search_and_apply_jobs(["Full Stack Developer"], location="Remote", max_jobs=10)
```

## Docker

1. **Dockerfile**

   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   ENTRYPOINT ["python", "client_interface.py"]
   ```

2. **docker-compose.yml**

   ```yaml
   version: "3.8"

   services:
     bot:
       build: .
       container_name: linkedin-bot
       volumes:
         - .:/app
       command: python client_interface.py

     test:
       build: .
       container_name: linkedin-bot-tests
       volumes:
         - .:/app
       command: pytest tests/
   ```

3. **Ejecutar con Docker**

   ```bash
   docker-compose up --build bot
   ```

## Notas Adicionales

- **Token de Acceso**: Si el token expira, el bot permite reautenticarse sin reiniciar la aplicación.
- **Restricciones de LinkedIn**: La API Talent Solutions requiere aprobaciones especiales. Consultar la documentación oficial.
- **Seguridad**: No compartas tu `client_secret` ni los tokens de acceso.
- **Multiplataforma**: El bot usa `winsound` en Windows para la alerta sonora, pero en macOS/Linux la omite (puedes integrar `playsound` si deseas).
- **Historial en SQLite** (opcional): El bot puede almacenar información de mensajes y postulaciones en `history.db`.
- **Modo Oscuro** y **Logs en Vivo**: Mejoran la experiencia de usuario.

### Mejoras Adicionales

1. **Plantillas de Mensajes Dinámicas**: Cargar archivos `.txt`/`.md` para reclutadores o cover letters.
2. **Control Avanzado de Rate Limit**: Manejar código 429 con backoff y contadores regresivos.
3. **Exclusión de Compañías Configurable**: Permite al usuario filtrar qué compañías ignorar.
4. **Escaneo de Descripciones**: Obtén y analiza la descripción del empleo (requiere Talent Solutions) para calcular un puntaje de compatibilidad.
5. **Cover Letters con IA**: Autogenera cartas más detalladas para aplicar a empleos.
6. **Internacionalización (i18n)**: Podrías traducir la GUI y mensajes según el idioma del usuario.
7. **Almacenamiento de Historial**: Registra acciones en una BD (SQLite, PostgreSQL, etc.) para análisis posterior.

Con este enfoque modular y las mejoras listadas, tu bot se vuelve más escalable, mantenible y flexible ante distintas necesidades.

---

Para más información, revisa la [documentación de LinkedIn API](https://docs.microsoft.com/en-us/linkedin/).
