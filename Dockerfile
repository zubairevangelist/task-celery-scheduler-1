# Use an official Python image
FROM python:3.9

# Install system dependencies
# RUN apt-get update && apt-get install -y git

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

RUN apt-get update && apt-get install -y tmux && apt-get clean
# Install required packages
RUN apt-get update && apt-get install -y screen && rm -rf /var/lib/apt/lists/*


# Set the default command
CMD ["python", "main.py"]
# CMD ["tmux", "new-session", "-d", "-s", "scheduler", "uvicorn main:app --host 0.0.0.0 --port 8000 && tmux split-window -v 'tmux capture-pane -p -S -' && tmux attach-session -t scheduler"]
# CMD ["tmux", "new-session", "-d", "-s", "scheduler", "uvicorn main:app --host 0.0.0.0 --port 8000 && tail -f /dev/null"]
# Run FastAPI app with APScheduler in a screen session
# CMD ["/bin/sh", "-c", "screen -dmS scheduler uvicorn main:app --host 0.0.0.0 --port 8000"]