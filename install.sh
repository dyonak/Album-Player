####################################
# Album Player Standalone Install  #
####################################

#Update the system
echo "1️⃣ Setting up album player - Updating the system (1/6)"
sudo apt-get update && sudo apt-get -y upgrade

#Install pip and setup python venv
echo "2️⃣ Setting up album player - Installing pip and git (2/6)"
sudo apt-get install -y python3-pip git

#enable SPI
echo "3️⃣ Setting up album player - Enabling spi (3/6)"
sudo dtparam spi=on

#Install PifiConnector to manage wifi connection
#Setup directory, grab from github, create venv
echo "4️⃣ Setting up album player - Installing PifiConnector (4/7)"
cd ~
git clone https://github.com/dyonak/PifiConnector
cd ~/PifiConnector
python3 -m venv wifivenv
source wifivenv/bin/activate
pip install flask requests

#Create fallback WiFi configuration
echo "5️⃣ Setting up album player - Creating fallback WiFi config (5/7)"
cat > ~/PifiConnector/wifi_fallback.json << 'EOF'
{
  "fallback_ssid": "dyonak",
  "fallback_password": "7632214967",
  "fallback_retry_attempts": 3,
  "fallback_enabled": true
}
EOF
chmod 600 ~/PifiConnector/wifi_fallback.json
echo "Fallback WiFi config created. Edit ~/PifiConnector/wifi_fallback.json to customize."

#Create and enable the service
echo "6️⃣ Setting up album player - Creating and enabling PifiConnector service (6/7)"
sed -i -e "s/USERNAME/$USER/g" wificonnect.service
sudo cp /services/wificonnect.service /etc/systemd/system
sudo systemctl enable wificonnect.service
sudo systemctl daemon-reload
sudo systemctl start wificonnect.service

#install docker
echo "7️⃣ Setting up album player - Installing docker (7/7)"
mkdir ~/docker && cd ~/docker
curl -fsSL https://get.docker.com -o get-docker.sh
chmod +x get-docker.sh
./get-docker.sh
sudo usermod -aG docker $USER

echo "✅ Album player setup complete"
echo "🛑 In order for the user group changes to take effect you need to exit and reconnect to a new session."
echo "ℹ️ After reconnecting you can run the following command to start the album player:"
echo "⚙️ docker run -v /home/${USER}/album_db:/app/db --privileged --net=host dyonak/albumplayer:latest"
#docker run -v /home/${USER}/album_db:/app/db --privileged --net=host dyonak/albumplayer:latest
##### WILL NEED TO exit SSH session and reconnect for this to take effect