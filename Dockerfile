# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: Build frontend (React 19 + Vite)
# ============================================================================
FROM node:20-alpine AS frontend-build

WORKDIR /src

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# ============================================================================
# Stage 2: Production image
# ============================================================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# -- System dependencies ------------------------------------------------
# libgomp1  — OpenMP runtime required by TensorFlow
# nginx     — serves built frontend + proxies /api → uvicorn
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm /etc/nginx/sites-enabled/default

# -- Python dependencies ------------------------------------------------
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -- Application code ---------------------------------------------------
COPY backend/ .

# -- Built frontend -----------------------------------------------------
COPY --from=frontend-build /src/dist ./frontend/dist

# -- Nginx configuration ------------------------------------------------
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# -- Entrypoint ---------------------------------------------------------
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:80/health')"

ENTRYPOINT ["/entrypoint.sh"]
