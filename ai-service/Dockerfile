# Base ligera de Python
FROM python:3.11-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Variables de entorno: evita archivos .pyc y salida con buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalación del sistema: solo curl, limpia los índices para reducir la imagen
RUN apt-get update && \
  apt-get install -y --no-install-recommends curl && \
  rm -rf /var/lib/apt/lists/*

# Instala dependencias de Python primero para aprovechar la cache de Docker:contentReference[oaicite:1]{index=1}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . /app

# Da permisos de ejecución al script de arranque
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
# Expone el puerto donde escuchará la aplicación
EXPOSE 8001
# Define el punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
