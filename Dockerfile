FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    firefox-esr \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver manually
RUN GECKODRIVER_VERSION=0.36.0 && \
    wget -q "https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz" && \
    tar -xzf "geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz" -C /usr/local/bin && \
    rm "geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz"

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
