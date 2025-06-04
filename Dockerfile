# Bruk en lettvekts Python-baseimage
FROM python:3.11-slim

# Installer nødvendige systemavhengigheter og Chromium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    libnss3 \
    libgconf-2-4 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libxss1 \
    libxshmfence1 \
    libgbm-dev \
    libgtk-3-0 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Sett opp arbeidskatalog
WORKDIR /app

# Kopier prosjektfiler
COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["sh", "-c", "echo 'Starter bolia.py...' && python /app/bolia.py"]
