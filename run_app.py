import subprocess
import threading

def run_api():
    subprocess.run(["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"])

def run_streamlit():
    subprocess.run(["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"])

# Run API in a thread, Streamlit in main thread
threading.Thread(target=run_api).start()
run_streamlit()