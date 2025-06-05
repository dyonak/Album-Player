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

#Add executable perms for the run.sh script
RUN chmod +x run.sh

# Run app.py when the container launches
CMD ["./run.sh"]
#Run command
#/home/album/album_db 
#docker run -v /home/${USER}/album_db:/app/db --privileged --net=host dyonak/albumplayer:latest