#Update the system
echo "Setting up album player - Updating the system (1/6)"
sudo apt-get update && sudo apt-get -y upgrade

#Install pip and setup python venv
echo "Setting up album player - Installing pip and git (2/6)"
sudo apt-get install -y python3-pip git

#enable SPI
echo "Setting up album player - Enabling spi (3/6)"
sudo dtparam spi=on

#Install PifiConnector to manage wifi connection
#Setup directory, grab from github, create venv
echo "Setting up album player - Installing PifiConnector (4/6)"
cd ~
git clone https://github.com/dyonak/PifiConnector
cd ~/PifiConnector
python3 -m venv wifivenv
source wifivenv/bin/activate
pip install flask requests

#Create and enable the service
echo "Setting up album player - Creating and enabling PifiConnector service (5/6)"
sed -i -e "s/USERNAME/$USER/g" wificonnect.service
sudo cp wificonnect.service /etc/systemd/system
sudo systemctl enable wificonnect.service
sudo systemctl daemon-reload
sudo systemctl start wificonnect.service

#install docker
echo "Setting up album player - Installing docker (6/6)"
mkdir ~/docker && cd ~/docker
curl -fsSL https://get.docker.com -o get-docker.sh
chmod +x get-docker.sh
./get-docker.sh
sudo usermod -aG docker $USER

echo "Album player setup complete. In order for the user group changes to take effect you need to exit and reconnect to a new session."
echo "After reconnecting you can run the following command to start the album player:"
echo "docker run -d --restart always --privileged --net=host dyonak/albumplayer:latest"
##### WILL NEED TO exit SSH session and reconnect for this to take effect
#After reconnecting run
#docker run -d --restart always --privileged --net=host dyonak/albumplayer:latest