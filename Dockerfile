FROM python:3.10-bullseye

# Install dependencies
RUN apt-get update -y && apt-get install -y wget xvfb unzip jq

# Install Google Chrome dependencies
RUN apt-get install -y libxss1 libappindicator1 libgconf-2-4 \
    fonts-liberation libasound2 libnspr4 libnss3 libx11-xcb1 libxtst6 lsb-release xdg-utils \
    libgbm1 libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcb-dri3-0


# Fetch the latest version numbers and URLs for Chrome and ChromeDriver
# RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json > /tmp/versions.json

#RUN CHROME_URL=$(jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
   # wget -q --continue -O /tmp/chrome-linux64.zip $CHROME_URL && \
   #  unzip /tmp/chrome-linux64.zip -d /opt/chrome

# RUN chmod +x /opt/chrome/chrome-linux64/chrome

# Download and install Google Chrome 128.0.6613.113-1 120.0.6099.129-1 128.0.6613.84-1
#ENV CHROME_VERSION=120.0.6099.129-1
#RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb && \
   # apt-get update && \
    #apt-get install -y ./google-chrome-stable_${CHROME_VERSION}_amd64.deb

# Move Chrome to the desired directory
#RUN mkdir -p /opt/chrome/chrome-linux64 && \
   # cp -r /usr/bin/google-chrome /opt/chrome/chrome-linux64/chrome && \
    #chmod +x /opt/chrome/chrome-linux64/chrome

# Download and install Chrome
ENV CHROME_VERSION=120.0.6099.2
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip -O /tmp/chrome-linux64.zip && \
    unzip /tmp/chrome-linux64.zip -d /opt/chrome && \
    chmod +x /opt/chrome/chrome-linux64/chrome

# Set up Chrome environment variables
ENV CHROME_DIR=/opt/chrome/chrome-linux64
ENV PATH=$CHROME_DIR:$PATH

# Download and install ChromeDriver
ENV CHROMEDRIVER_VERSION=120.0.6099.2
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip -O /tmp/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/chromedriver && \
    chmod +x /opt/chromedriver/chromedriver-linux64/chromedriver

# Set up ChromeDriver environment variables
ENV CHROMEDRIVER_DIR=/opt/chromedriver/chromedriver-linux64
ENV PATH=$CHROMEDRIVER_DIR:$PATH

# Clean up
RUN rm /tmp/chromedriver-linux64.zip

WORKDIR /app
COPY . /app

# Gerekli Python bağımlılıklarının kurulumu
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the script
CMD ["python", "app.py"]
