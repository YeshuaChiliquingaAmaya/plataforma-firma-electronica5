# Usar una imagen oficial de Python como base
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# --- ¡CAMBIO AQUÍ! ---
# Instalar curl para que el healthcheck de Docker Compose funcione
RUN apt-get update && apt-get install -y curl

# Copiar el archivo de requerimientos primero
COPY ./requirements.txt /app/requirements.txt

# Instalar las dependencias de Python
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copiar todo el código de la aplicación (main.py y la carpeta app/)
COPY . /app

# Exponer el puerto
EXPOSE 8000

# Comando para correr la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]