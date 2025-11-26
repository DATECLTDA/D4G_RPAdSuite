FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Cloud Run espera que escuches en el puerto 8080
EXPOSE 8080

# Configura variables de entorno para Cloud Run
ENV PORT=8080
ENV AUTH_SECRET=MiClaveUltraSecreta_MCP_2025_#f6d9kP!

CMD ["python", "server.py"]