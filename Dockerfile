# ──────────────────────────────────────────────────────────
# Stage 1: Build React application
# ──────────────────────────────────────────────────────────
FROM node:18-alpine AS frontend_build

# Set working directory for frontend
WORKDIR /frontend

# Copy package files and install
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of your frontend code and build
COPY frontend/ ./
RUN npm run build
# After this step, the compiled static files will be in /frontend/dist

# ──────────────────────────────────────────────────────────
# Stage 2: Final image with FastAPI + built frontend
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS final

# Create and set working directory for backend
WORKDIR /app

# Copy backend requirements, install them
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code into /app
COPY backend/ /app

# Copy the React build output from the first stage to /app/frontend-dist
COPY --from=frontend_build /frontend/dist ./frontend-dist

# Expose port 80
EXPOSE 80

# By default, run Uvicorn on port 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
