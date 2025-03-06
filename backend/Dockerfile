# Dockerfile.backend
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies (use a requirements.txt or pipenv as appropriate)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE 8000

# Command to run the app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
