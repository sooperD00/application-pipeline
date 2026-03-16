# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Output: /build/dist/


# Stage 2: Python API + built frontend
FROM python:3.12-slim
WORKDIR /app

# System deps for python-docx / lxml (your docx_builder needs this)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ .

# Built frontend → /app/static/ (FastAPI will serve this)
COPY --from=frontend-build /build/dist ./static

# start.sh runs migrations then starts uvicorn
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
