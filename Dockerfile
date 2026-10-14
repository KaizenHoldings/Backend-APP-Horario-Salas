# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Dependencias del sistema (para pyodbc y compilar wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime ODBC
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes instalados
COPY --from=builder /install /usr/local

# Copiar código fuente (sin venv ni __pycache__)
COPY . .

# Puerto que expone uvicorn
EXPOSE 8000

# Las variables sensibles (.env) se inyectan en tiempo de ejecución via docker-compose
# NO se copian aquí para no hornear secretos en la imagen
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
