FROM python:3.11-slim

# Instalar FFmpeg y otras dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando para ejecutar la app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]