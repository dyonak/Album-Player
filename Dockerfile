FROM python:3.11.11-slim-bookworm

#Install container dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential python3-dev libxml2-dev libffi-dev
RUN apt-get install -y gcc g++ libxml2 libxslt-dev libusb-dev libpcsclite-dev wget
RUN apt-get install -y --upgrade python3-setuptools
RUN apt-get install --fix-broken

# Set the working directory in the container
WORKDIR /app

RUN wget https://github.com/nfc-tools/libnfc/releases/download/libnfc-1.8.0/libnfc-1.8.0.tar.bz2
RUN tar -xf libnfc-1.8.0.tar.bz2
RUN ./libnfc-1.8.0/configure --prefix=/usr --sysconfdir=/etc
RUN make
RUN make install
COPY libnfc.conf /etc/nfc/

# Copy the current directory contents into the container at /app
COPY requirements.txt /app

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ADD . /app
VOLUME /db

# Encrypted Spotify API Credentials
# IMPORTANT: Replace these with your encrypted credentials
# Run: python3 dev_tools/encrypt_credentials.py to generate these values
ENV ENCRYPTION_KEY=".encryption_key"
ENV ENCRYPTED_SPOTIFY_ID="gAAAAABo9wK8K8ZmXQTFn3G8m3TG-qzkYMpn4tbUbWQI8gP5OKfspHjxNOVQFCfZylSGGBGHRJkeSUYEmeMKmwtngWYSRciYR7_qdFo_z5XqzlcIEMQIjda_TbVoAe-w9ml9IXWUxJOG"
ENV ENCRYPTED_SPOTIFY_SECRET="gAAAAABo9wK8SOnP6rTCyEa0Q7LIwke3iffQZarfSFxkg4krci5ohB5UvwGUEgrrZBYGdt_kBS3PJYST-MjndSgZfErtjcDyYHJkTbKRUewENl62MSlreRchxI7NSe6oceH4-M8kZIgV"

#Add executable perms for the run.sh script
RUN chmod +x run.sh

# Run app.py when the container launches
CMD ["./run.sh"]
#Run command
#/home/album/album_db 
#docker run -v /home/${USER}/album_db:/app/db --privileged --net=host dyonak/albumplayer:latest