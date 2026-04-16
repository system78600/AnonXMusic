FROM nikolaik/python-nodejs:python3.11-nodejs20-bullseye

# Install ffmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app/
WORKDIR /app/

# Install Python deps
RUN pip3 install --no-cache-dir -U -r requirements.txt

# Start bot
CMD ["bash", "start"]
