FROM python:latest
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -U pip wheel
RUN pip install --no-cache-dir -Ur requirements.txt

COPY . .