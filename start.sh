#!/bin/bash
set -e

echo "Starting Streamlit Loan Eligibility App..."

# Run Streamlit on 0.0.0.0:8080 (Cloud Run default port)
exec streamlit run streamlit_app.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
