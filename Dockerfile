# Use an official Python image
FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y git

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Set the default command
# CMD ["python", "main.py"]

