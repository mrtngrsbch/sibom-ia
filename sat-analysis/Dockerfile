# Dockerfile para sat-analysis FastAPI backend
# Optimizado para ARM64 (Apple Silicon) y AMD64

FROM python:3.13-slim-bookworm

# Instalar dependencias básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copiar requirements primero para caché de Docker
COPY requirements.txt .

# Instalar dependencias Python (rasterio se compila desde fuente si no hay wheel)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser api/ /app/api/
COPY --chown=appuser:appserver codigos_partidos_arba.json .
COPY --chown=appuser:appserver thresholds.yaml .

# Crear directorios de datos
RUN mkdir -p /app/data/web_output /app/logs && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OUTPUT_DIR=/app/data/web_output \
    PYTHONPATH=/app/src

# Exponer puerto FastAPI
EXPOSE 8001

# Health check (usar python en vez de curl para no depender de curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/health')" || exit 1

# Comando de inicio (1 worker para no tener problemas con multiprocessing)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
