# LinkedIn Job Search Bot

Este bot automatiza la búsqueda de empleo en LinkedIn con ayuda de inteligencia artificial, permitiendo contactar reclutadores y aplicar a trabajos de manera automatizada.

## ¿Por Qué Usamos Estas Tecnologías?

- **requests**: Para realizar solicitudes HTTP a la API de LinkedIn y a LM Studio de manera sencilla.
- **tkinter**: Proporciona una **interfaz gráfica** (GUI) nativa de Python que permite a los usuarios interactuar con el bot sin necesidad de usar la línea de comandos.
- **pytest y unittest**: Para **probar** cada componente del bot y asegurarnos de que funcione correctamente antes de su uso en producción.
- **LM Studio** (con modelo QWEN): Para **generar mensajes personalizados** usando IA. De esta forma, el bot puede redactar notas atractivas para reclutadores y personalizar tus aplicaciones a empleos.
- **Mecanismo de reintentos**: Si la API de LinkedIn falla temporalmente, el bot intenta la petición varias veces antes de rendirse.

## Características

- **Contacto con reclutadores**: Envía mensajes personalizados a reclutadores en LinkedIn.
- **Aplicación a empleos**: Busca y aplica automáticamente a trabajos con la opción "Easy Apply".
- **Integración con IA**: Usa LM Studio con el modelo QWEN para generar mensajes personalizados.
- **Interfaz gráfica**: Cuenta con una GUI para facilitar su uso.
- **Pruebas unitarias**: Incluye tests con `unittest` para validar el funcionamiento.
- **Manejo de errores y reintentos**: Se ha agregado un mecanismo para reintentar solicitudes fallidas a la API de LinkedIn.

## Requisitos

- Python 3.8+
- Credenciales de la API de LinkedIn
- LM Studio con el modelo QWEN
- `pytest` para ejecutar pruebas unitarias

## Configuración

### ¿Eres un desarrollador individual?

Si eres un desarrollador individual y actualmente trabajas para otra empresa, puedes **registrar tu aplicación** en [LinkedIn Developer Portal](https://www.linkedin.com/developers/) **sin** necesidad de asociarla a la página de tu empleador. Tienes dos opciones:

1. **Usar una "Default Company Page" para individuos**. En algunos casos, LinkedIn ofrece una página predeterminada para desarrolladores individuales que no tienen una página de empresa. Selecciona esa "default page" cuando configures la aplicación.
2. **Crear tu propia "Company Page" personal** (aunque sea para un proyecto o marca personal). Luego, asocia esa página en la sección de "LinkedIn Page" al crear tu app.

Si no ves ninguna "default page" y no quieres vincular tu app con la empresa actual en la que trabajas, lo más simple es **crear una nueva LinkedIn Page** para tu proyecto personal (puede ser un nombre distinto a tu empresa actual).

---

### Pasos de Configuración

1. **Instalar dependencias**
   ```bash
   pip install requests tkinter pytest
   ```
2. **Configurar LinkedIn API**
   - Crear una aplicación en [LinkedIn Developer Portal](https://www.linkedin.com/developers/).
   - Obtener `client_id` y `client_secret`.
   - Editar `config.json` con las credenciales.
3. **Configurar LM Studio**

   - Descargar e instalar [LM Studio](https://lmstudio.ai/).
   - Asegurar que el servidor API está corriendo en `http://localhost:1234/v1`.

4. **Instalar dependencias**
   ```bash
   pip install requests tkinter pytest
   ```
5. **Configurar LinkedIn API**
   - Crear una aplicación en [LinkedIn Developer Portal](https://www.linkedin.com/developers/).
   - Obtener `client_id` y `client_secret`.
   - Editar `config.json` con las credenciales.
6. **Configurar LM Studio**
   - Descargar e instalar [LM Studio](https://lmstudio.ai/).
   - Asegurar que el servidor API está corriendo en `http://localhost:1234/v1`.

## Uso

### Ejecutar la aplicación

```bash
python client_interface.py
```

Esto abrirá una ventana de interfaz gráfica para configurar y ejecutar el bot.

### Contactar reclutadores

1. Click en "Buscar Reclutadores" para obtener una lista de conexiones relevantes.
2. Revisar el mensaje y personalizarlo si es necesario.
3. Click en "Iniciar Contacto" para enviar mensajes.

### Aplicar a trabajos

1. Ingresar palabras clave y ubicación.
2. Click en "Buscar Trabajos" para obtener ofertas.
3. Click en "Iniciar Aplicación" para postularse automáticamente.

## Implementación con LM Studio

LM Studio se utiliza para generar mensajes personalizados con el modelo QWEN:

1. Se usa el endpoint de LM Studio (`http://localhost:1234/v1/chat/completions`) para generar mensajes de contacto con reclutadores.
2. Se generan notas personalizadas utilizando el contexto del reclutador y las habilidades del usuario.
3. Se utiliza un modelo basado en `GPT-like` para adaptar respuestas y cubrir distintos escenarios.

Ejemplo de solicitud a LM Studio:

```python
import requests

def generate_message(prompt):
    response = requests.post("http://localhost:1234/v1/chat/completions", json={
        "model": "qwen",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    })
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
```

## Manejo de Errores y Reintentos

Si la API de LinkedIn no responde o ocurre un error temporal, el bot reintentará la solicitud hasta **3 veces** con un backoff exponencial. Esto evita que un fallo puntual detenga la ejecución completa.

## Pruebas

Para comprobar que todo funciona:

1. **Ejecutar pruebas unitarias**:
   ```bash
   pytest tests/
   ```
2. **Prueba manual**: Ejecutar el bot y probar opciones:
   ```bash
   python client_interface.py
   ```
   - Autenticar con LinkedIn
   - Probar la generación de mensajes con LM Studio
   - Intentar contactar reclutadores y/o aplicar a empleos

## Integración con Docker (Compose)

Opcionalmente, puedes **containerizar** este proyecto con Docker y Docker Compose:

- Crea un **Dockerfile** para instalar las dependencias y copiar el código:

  ```dockerfile
  FROM python:3.9-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  # Si quieres exponer puertos (por ejemplo, un servidor web)
  # EXPOSE 8000
  ENTRYPOINT ["python", "client_interface.py"]
  ```

- Crea un **docker-compose.yml** con dos servicios, por ejemplo:

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

Con esto, puedes:

- **Levantar la aplicación**:

  ```bash
  docker-compose up --build bot
  ```

  Nota: La GUI de `tkinter` dentro de un contenedor Docker requiere configuraciones extra si quieres verla en tu máquina local (por ejemplo, configurar X11 forwarding o usar un contenedor que permita escritorio remoto).

- **Ejecutar pruebas** dentro del contenedor:
  ```bash
  docker-compose run --rm test
  ```

### Caveats

- **GUI en Docker**: `tkinter` está pensado para un entorno con interfaz gráfica. Si corres Docker en un servidor remoto, necesitarás usar técnicas como **X forwarding** o **VNC** para ver la interfaz.
- **LM Studio**: La ejecución de LM Studio con Docker Compose implicaría agregar otro servicio que corra LM Studio (con GPU o CPU según el caso). Típicamente, se ejecuta LM Studio por separado.
- **Variables de entorno**: Para credenciales (API keys), configura variables de entorno en tu `docker-compose.yml` o usa un archivo `.env`.
- **Despliegue real**: Para un CI/CD completo, se recomienda usar herramientas como **GitHub Actions**, **GitLab CI**, o **Jenkins**, donde puedes integrar los pasos `docker-compose build`, `docker-compose run test`, y luego `docker-compose push`.

## Notas Importantes

- Usar con responsabilidad y respetar las políticas de LinkedIn.
- Revisar los mensajes antes de enviarlos.
- Ajustar los tiempos de espera para evitar bloqueos por parte de LinkedIn.
- Asegurarse de que LM Studio está en ejecución y con el modelo QWEN cargado.

## Personalización

- **Plantillas de mensajes**: Se pueden editar en `LM_Studio_Templates.md`.
- **Filtros de búsqueda**: Ajustables en `config.json`.

## Solución de Problemas

- **Problemas de autenticación**: Verificar credenciales en `config.json`.
- **Errores de conexión**: Asegurar que LM Studio está activo.
- **Límites de tasa**: Aumentar el tiempo de espera entre operaciones para evitar bloqueos.
