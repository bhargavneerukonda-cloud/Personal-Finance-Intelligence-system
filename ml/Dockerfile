FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY . .

RUN mkdir -p models data/raw data/processed

EXPOSE 8001

CMD ["uvicorn", "src.serving.server:app", "--host", "0.0.0.0", "--port", "8001"]
