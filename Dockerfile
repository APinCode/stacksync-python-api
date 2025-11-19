# Multi stage build

# Stage 1: build nsjail from source
FROM python:3.12-slim AS nsjail-builder

# Build dependencies for nsjail
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        pkg-config \
        libprotobuf-dev \
        protobuf-compiler \
        libnl-route-3-dev \
        libcap-dev \
        libseccomp-dev \
        flex \
        bison \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
RUN git clone https://github.com/google/nsjail.git /tmp/nsjail && \
    make -C /tmp/nsjail && \
    cp /tmp/nsjail/nsjail /usr/local/bin/nsjail

# Stage 2: Final App image
FROM python:3.12-slim

# Runtime dependencies for nsjail (no compilers here)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        libprotobuf-dev \
        libnl-route-3-200 \
        libcap2 \
        libseccomp2 && \
    rm -rf /var/lib/apt/lists/*

# Copy nsjail binary
COPY --from=nsjail-builder /usr/local/bin/nsjail /usr/local/bin/nsjail

# Create app and sandbox directories
RUN mkdir -p /app /sandbox

# Make /app the current working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and nsjail config
COPY app.py executor.py /app/
COPY nsjail.cfg /etc/nsjail.cfg

# Create a non-root user and give permissions
# RUN useradd -m appuser && chown -R appuser /app /sandbox
# USER appuser

ENV PYTHONUNBUFFERED=1

# Expose port 8080
EXPOSE 8080

# Start the app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
