# Used to install dependencies in fresh EC2 instances


sudo apt update

# Install docker
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt-cache policy docker-ce
sudo apt install docker-ce
sudo usermod -aG docker ${USER}

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install npm
sudo apt -y install nodejs
sudo apt -y install npm

# Install caliper-benchmarks
git clone https://github.com/hyperledger/caliper-benchmarks
(
    cd ~/caliper-benchmarks &&
    npm init -y &&
    npm install --only=prod @hyperledger/caliper-cli@0.5.0
    npx caliper bind --caliper-bind-sut ethereum:1.3
)

# Install pumba
wget https://github.com/alexei-led/pumba/releases/download/0.9.7/pumba_linux_amd64
chmod +x pumba_linux_amd64
sudo mv pumba_linux_amd64 /bin/pumba

# Install python
sudo apt install python3-pip
pip install PyYAML
pip install python-dotenv
