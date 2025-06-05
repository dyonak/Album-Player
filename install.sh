#Update the system
sudo apt-get update && sudo apt-get -y upgrade

#Install pip and setup python venv
sudo apt-get install -y python3-pip git
python3 -m pip install --upgrade pip

#enable SPI
sudo dtparam spi=on

#Install PifiConnector to manage wifi connection
#Setup directory, grab from github, create venv
cd ~
git clone https://github.com/dyonak/PifiConnector
cd ~/PifiConnector
python -m venv wifivenv
pip install flask requests

#Create and enable the service
sed -i -e "s/USERNAME/$USER/g" wificonnect.service
sudo cp wificonnect.service /etc/systemd/system
sudo systemctl enable wificonnect.service
sudo systemctl daemon-reload
sudo systemctl start wificonnect.service

#install docker
mkdir ~/docker && cd ~/docker
curl -fsSL https://get.docker.com -o get-docker.sh
chmod +x get-docker.sh
sudo usermod -aG docker %{USER}
##### WILL NEED TO exit SSH session and reconnect for this to take effect
#After reconnecting run
#docker run -d --restart always --privileged --net=host dyonak/albumplayer:latest