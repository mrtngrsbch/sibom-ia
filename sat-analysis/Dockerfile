# Dockerfile para sat-analysis en Railway
# Multi-stage build para optimizar tamaño de imagen

# Stage 1: Builder - compilar dependencias que necesitan compilación
FROM python:3.13-slim-bookworm AS builder

# Instalar dependencias de compilación para rasterio y otras librerías geoespaciales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements e instalar dependencias
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - imagen final más ligera
FROM python:3.13-slim-bookworm

# Instalar solo dependencias runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal3 \
    libproj25 \
    libgeos-c1v5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para Gradio
RUN useradd -m -u 1000 appuser

# Copiar entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME="0.0.0.0"

# Crear directorios de trabajo
WORKDIR /app
RUN mkdir -p /app/web_output /app/logs && \
    chown -R appuser:appuser /app

# Copiar código fuente
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser app.py /app/
COPY --chown=appuser:appuser codigos_partidos_arba.json /app/
COPY --chown=appuser:appuser thresholds.yaml /app/

# Cambiar a usuario no-root
USER appuser

# Exponer puerto que Railway espera
ENV GRADIO_SERVER_PORT=7860
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')"

# Comando de inicio
CMD ["python", "app.py"]
