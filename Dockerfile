# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies in a single RUN command to leverage caching
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libffi-dev \
        libssl-dev \
        libexpat1 \
        libgdal-dev \
        libproj-dev \
        libspatialindex-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --retries 10 --timeout 120 --resume-retries 10 -r requirements.txt

# Install additional Python packages
RUN pip install --retries 10 --timeout 120 --resume-retries 10 redis "uvicorn[standard]"

# Copy the rest of the application code
COPY . .
# Create the local_uploads directory and set permissions
RUN mkdir -p local_uploads && chmod 777 local_uploads

# Expose the necessary port
EXPOSE 8001

# Define the default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]