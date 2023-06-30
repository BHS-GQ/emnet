# Used to install dependencies in fresh EC2 instances


sudo apt update
sudo apt-get update

# Install docker
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt-cache policy docker-ce
sudo apt-get -y install docker-ce
sudo usermod -aG docker ${USER}

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install pumba
wget https://github.com/alexei-led/pumba/releases/download/0.9.7/pumba_linux_amd64
chmod +x pumba_linux_amd64
sudo mv pumba_linux_amd64 /bin/pumba

# Install python
sudo apt-get -y install python3-pip
pip install pip --upgrade
pip install PyYAML
pip install python-dotenv
pip install paramiko

# Open Remote API Endpoint
sudo mkdir -p /etc/systemd/system/docker.service.d/
{ echo "[Service]"; 
    echo "ExecStart=";
    echo "ExecStart=/usr/bin/dockerd -H fd:// -H tcp://0.0.0.0:2375";
} | sudo tee /etc/systemd/system/docker.service.d/open-remote.conf
sudo systemctl daemon-reload
sleep 1
sudo systemctl restart docker.service

docker image pull gvlim/quorumbhs:0.0.0
