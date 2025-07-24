# Use Python base image
FROM python:3.10-slim

# Install wkhtmltopdf, Nginx, and dependencies
RUN apt-get update && apt-get install -y wkhtmltopdf nginx && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Copy Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose Cloud Run's single port
EXPOSE 8080

# Start FastAPI, Streamlit, and Nginx
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000 & \
    streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501 & \
    nginx -g "daemon off;"

