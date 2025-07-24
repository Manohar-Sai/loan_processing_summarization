# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app


RUN apt-get update && apt-get install -y wkhtmltopdf && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Specify the command to run the app
# Expose ports for FastAPI and Streamlit
EXPOSE 8501

# Start both FastAPI and Streamlit in parallel using bash
CMD uvicorn app:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
