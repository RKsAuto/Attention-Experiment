# Ubuntu rather than python:slim, because both mbrola and its voice data are
# packaged in ubuntu's multiverse. The earlier debian non-free attempt failed
# to build; these exact package names are known to install on ubuntu 24.04.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# multiverse is not enabled out of the box, so point apt at it first. The
# release codename comes from the image so a base bump does not break this.
RUN . /etc/os-release && \
    echo "deb http://archive.ubuntu.com/ubuntu ${VERSION_CODENAME} multiverse" \
        > /etc/apt/sources.list.d/multiverse.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip espeak-ng mbrola mbrola-us1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
# installing system wide is fine in a container, and saves carrying a venv
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend
CMD python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
