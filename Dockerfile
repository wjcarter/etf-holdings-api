FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    gnupg \
    unzip \
    && apt-get clean

# Install geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-linux64.tar.gz \
    && tar -xzf geckodriver-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-linux64.tar.gz

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port and run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
