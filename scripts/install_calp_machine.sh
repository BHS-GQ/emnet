# Used to install dependencies in fresh EC2 instances


sudo apt update

# Install npm
sudo apt-get -y install nodejs
sudo apt-get -y install npm

# Install caliper-benchmarks
git clone https://github.com/hyperledger/caliper-benchmarks
(
    cd ~/caliper-benchmarks &&
    npm init -y &&
    npm install --only=prod @hyperledger/caliper-cli@0.4.2
    npx caliper bind --caliper-bind-sut ethereum:latest
)

# Install python
sudo apt-get -y install python3-pip
pip install PyYAML
pip install python-dotenv
