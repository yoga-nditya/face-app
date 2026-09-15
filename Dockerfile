FROM mirror.gcr.io/library/python:3.11.2-slim

# Dependensi build untuk dlib/opencv (dibutuhkan jika wheel prebuilt tidak tersedia)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    libopenblas-dev liblapack-dev \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY scripts/ scripts/

# images/ dan data/ sebaiknya di-mount sebagai volume, bukan dibake ke image,
# supaya administrator dapat menambah/mengubah foto tanpa rebuild image Docker.
RUN mkdir -p images data/face_index

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
