# Used to install dependencies in fresh EC2 instances

sudo apt update

# Install npm
sudo apt-get -y install nodejs
sudo apt-get -y install npm

git clone -b v5 --single-branch https://github.com/ndsg-eth1/caliper.git
(
    cd ~/caliper &&
    npm i &&
    npm run repoclean -- --yes &&
    npm run bootstrap
)

# Install caliper-benchmarks
git clone https://github.com/hyperledger/caliper-benchmarks
(
    cd ~/caliper-benchmarks &&
    npm init -y &&
    npm install --only=prod @hyperledger/caliper-cli@0.5.0 &&
    node /home/ubuntu/caliper/packages/caliper-cli/caliper.js bind --caliper-bind-sut ethereum:1.3
)
