FROM python:3.9-slim

# Definir el directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración y requerimientos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Configurar variables de entorno necesarias
ENV LINKEDIN_CLIENT_ID=""
ENV LINKEDIN_CLIENT_SECRET=""
ENV REDIRECT_URI="http://localhost:8000/callback"

# Definir el punto de entrada
ENTRYPOINT ["python", "client_interface.py"]