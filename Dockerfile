FROM python:3.11-slim

# Set environment variables to ensure output is sent to logs
ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY static/ ./static/

EXPOSE 8080

# Use the shell form to allow the $PORT variable to be read
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}