FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
# Render and similar hosts inject $PORT; default to 8501 locally.
CMD ["sh", "-c", "streamlit run app/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
