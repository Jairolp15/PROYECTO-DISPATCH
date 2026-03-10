FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias mínimas si fueran necesarias para compilar alguna librería de python
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Dar permisos de ejecución al script de inicio
RUN chmod +x start.sh

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando de inicio
CMD ["./start.sh"]
