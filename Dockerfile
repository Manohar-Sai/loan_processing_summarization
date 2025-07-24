FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    wkhtmltopdf \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy NGINX config
COPY nginx.conf /etc/nginx/nginx.conf

# Make the start script executable inside the container
RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["bash", "start.sh"]
