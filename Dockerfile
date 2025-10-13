FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    build-essential \
    cmake \
    libgl1 \
    libsm6 libxext6 libxrender-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000