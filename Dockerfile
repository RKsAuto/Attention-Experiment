FROM python:3.11-slim

# espeak-ng does the speaking. mbrola is a smoother sounding voice it can drive,
# but its voice data sits in debian's non-free section, which slim images leave
# switched off, so add that first. Codename is read from the image so this does
# not break when the base moves to the next debian release.
RUN . /etc/os-release && \
    echo "deb http://deb.debian.org/debian ${VERSION_CODENAME} main non-free" \
        > /etc/apt/sources.list.d/non-free.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends espeak-ng mbrola mbrola-us1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
