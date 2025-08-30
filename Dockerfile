FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY model/ ./model/

# Make the startup script executable
RUN chmod +x start.sh

# Expose the port that will be set by the environment variable
EXPOSE $PORT

# Use the startup script
CMD ["./start.sh"]
