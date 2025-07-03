FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    firefox-esr \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver manually (fixed)
RUN curl -L -f -o geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz \
    && tar -xzf geckodriver.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver.tar.gz

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
