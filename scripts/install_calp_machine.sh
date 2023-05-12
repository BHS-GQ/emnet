# Used to install dependencies in fresh EC2 instances

sudo apt update

# Install npm
sudo apt-get -y install nodejs
sudo apt-get -y install npm

# Install caliper-benchmarks
git clone https://github.com/hyperledger/caliper-benchmarks
git clone -b v5 --single-branch https://github.com/ndsg-eth1/caliper.git
(
    cd ~/caliper &&
    npm i &&
    npm run repoclean -- --yes &&
    npm run bootstrap
)
# Install python
sudo apt-get -y install python3-pip
pip install PyYAML
pip install python-dotenv
