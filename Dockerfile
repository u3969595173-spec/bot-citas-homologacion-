FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto para health check
EXPOSE 10000

# Comando para ejecutar el bot
CMD ["python", "main.py"]
