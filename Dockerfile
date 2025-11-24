FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev build-essential && rm -rf /var/lib/apt/lists/*

# Configurar OpenSSL para permitir legacy renegotiation (necesario para citaprevia)
RUN echo '[openssl_init]\n\
ssl_conf = ssl_sect\n\
\n\
[ssl_sect]\n\
system_default = system_default_sect\n\
\n\
[system_default_sect]\n\
Options = UnsafeLegacyRenegotiation\n\
CipherString = DEFAULT@SECLEVEL=0' > /etc/ssl/openssl_legacy.cnf

# Establecer variable de entorno para usar la configuración
ENV OPENSSL_CONF=/etc/ssl/openssl_legacy.cnf

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
