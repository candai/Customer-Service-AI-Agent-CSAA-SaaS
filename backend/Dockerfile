# backend/Dockerfile
# local dev Dockerfile for Luron backend
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y redis-server

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose ports for Daphne and Redis
EXPOSE 8000
EXPOSE 6379

# Crun one create a shell script to run both Daphne and Redis
# We use a script because CMD can only ommand directly
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Run the entrypoint script
CMD ["/usr/local/bin/entrypoint.sh"]
