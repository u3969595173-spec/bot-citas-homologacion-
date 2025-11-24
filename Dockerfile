FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# CRÍTICO: Configurar OpenSSL ANTES de todo para permitir legacy SSL
RUN printf 'openssl_conf = openssl_init\n\n[openssl_init]\nssl_conf = ssl_sect\n\n[ssl_sect]\nsystem_default = system_default_sect\n\n[system_default_sect]\nOptions = UnsafeLegacyRenegotiation\nCipherString = DEFAULT@SECLEVEL=0\n' > /etc/ssl/openssl_legacy.cnf && \
    update-ca-certificates

# Establecer variable de entorno GLOBAL para OpenSSL
ENV OPENSSL_CONF=/etc/ssl/openssl_legacy.cnf

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev build-essential && rm -rf /var/lib/apt/lists/*

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
