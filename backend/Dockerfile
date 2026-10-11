FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV ENVIRONMENT=production
EXPOSE 8000
# One worker: batch jobs run in-process and the rate limiter is per-process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
