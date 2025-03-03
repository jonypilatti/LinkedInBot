# Base image: Python 3.9 (slim for smaller size)
FROM python:3.9-slim

# Create a working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose any ports if necessary (for a web server, etc.)
# EXPOSE 8000

# Default command: run the client interface
ENTRYPOINT ["python", "client_interface.py"]
