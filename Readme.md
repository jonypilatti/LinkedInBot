# LinkedIn Job Search Bot

Este bot automatiza la búsqueda de empleo en LinkedIn con ayuda de inteligencia artificial, permitiendo contactar reclutadores y aplicar a trabajos de manera automatizada. Usa la biblioteca **python3-linkedin** para autenticación y la API REST de LinkedIn para funcionalidades avanzadas como búsqueda y aplicación a empleos.

## Tecnologías Utilizadas

- **[python3-linkedin](https://github.com/ozgur/python-linkedin)**: Cliente oficial de LinkedIn para autenticación y manejo de perfiles.
- **[requests](https://docs.python-requests.org/)**: Para realizar llamadas REST a la API de LinkedIn.
- **[tkinter](https://docs.python.org/3/library/tkinter.html)**: Proporciona una interfaz gráfica para facilitar la interacción con el bot.
- **[pytest](https://docs.pytest.org/)** y **[unittest](https://docs.python.org/3/library/unittest.html)**: Para pruebas unitarias.
- **[LM Studio](https://lmstudio.ai/)**: Genera mensajes personalizados para contactar reclutadores.

## Características

- **Autenticación con LinkedIn**: Usa `python3-linkedin` para obtener un token de acceso.
- **Obtención de perfil de usuario**: Recupera información del usuario autenticado.
- **Conexiones y mensajería**: Envía mensajes personalizados a reclutadores en LinkedIn.
- **Búsqueda de empleos**: Encuentra ofertas de trabajo en base a palabras clave y ubicación.
- **Aplicación a empleos**: Envia solicitudes automáticamente a empleos compatibles con "Easy Apply".
- **Manejo de errores y reintentos**: Implementa un mecanismo de reintentos para garantizar estabilidad.

## Configuración

### Requisitos

1. **Crear una aplicación en LinkedIn Developer Portal** ([Enlace](https://www.linkedin.com/developers/))
   - Obtener `client_id` y `client_secret`.
   - Configurar `redirect_uri` (ejemplo: `http://localhost:8000/callback`).
2. **Configurar `config.json`**

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
   pip install requests python3-linkedin pytest
   ```

4. **Ejecutar la aplicación**
   ```bash
   python client_interface.py
   ```

## Uso

### Autenticación

El bot usa `python3-linkedin` para autenticar usuarios y obtener un token de acceso. Si el token ya está guardado, se reutiliza automáticamente.

### Contactar Reclutadores

1. **Buscar conexiones**: Obtiene la lista de conexiones actuales.
2. **Enviar mensajes**: Utiliza LM Studio para generar mensajes personalizados y los envía a reclutadores.

### Buscar y Aplicar a Empleos

- **Buscar empleos:** Usa la API REST de LinkedIn para encontrar empleos.
  ```python
  bot.search_jobs(["Desarrollador Python", "Full Stack"], location="Argentina", easy_apply_only=True)
  ```
- **Aplicar a empleos:**
  ```python
  bot.apply_to_job("job_id")
  ```
  **Nota:** Estos endpoints pueden requerir permisos adicionales de LinkedIn.

## Docker

Para correr el bot en un contenedor Docker:

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

3. **Ejecutar el bot con Docker**
   ```bash
   docker-compose up --build bot
   ```

## Notas Adicionales

- **Token de acceso:** Si el token expira, deberá generarse nuevamente.
- **Restricciones de LinkedIn:** La API de LinkedIn puede requerir aprobaciones especiales para ciertas funcionalidades.
- **Seguridad:** No compartas tu `client_secret` ni tokens de acceso.

---

Para más información, revisa la [documentación de LinkedIn API](https://docs.microsoft.com/en-us/linkedin/).
