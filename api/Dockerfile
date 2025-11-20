FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV NLE_DATA_DIR=/data
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends docker.io ca-certificates curl \
 && python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt \
 && rm -rf /var/lib/apt/lists/*
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
