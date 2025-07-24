# Use Python slim base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (nginx, wkhtmltopdf for PDF generation)
RUN apt-get update && apt-get install -y \
    nginx \
    wkhtmltopdf \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy and set permissions for start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose Cloud Run port
EXPOSE 8080

# Start both FastAPI (Uvicorn) and Streamlit via NGINX
CMD ["./start.sh"]
