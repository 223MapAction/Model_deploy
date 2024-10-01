# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Create the /app directory
RUN mkdir -p /app

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip 
RUN pip install redis
RUN pip install -r requirements.txt

# Install uvicorn with WebSocket support
RUN pip install "uvicorn[standard]"

# Make port 8001 available to the world outside this container
EXPOSE 8001

# Define environment variable
ENV PYTHONUNBUFFERED 1

# Run app.main:app when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
