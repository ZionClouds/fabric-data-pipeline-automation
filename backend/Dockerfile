# Use Python 3.11 slim image (Debian 12/bookworm)
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps + ODBC headers (no apt-key)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg2 apt-transport-https \
    unixodbc unixodbc-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repo via keyring and install msodbcsql18 + mssql-tools18
RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
      | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg; \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
      > /etc/apt/sources.list.d/mssql-release.list; \
    apt-get update; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 mssql-tools18; \
    rm -rf /var/lib/apt/lists/*

# Add Microsoft tools to PATH
ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose app port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default command (FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
