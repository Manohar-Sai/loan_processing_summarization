# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Specify the command to run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

CMD ["streamlit", "run", "streamlit_appy.py"]
