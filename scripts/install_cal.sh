# Used to install dependencies in fresh EC2 instances

sudo apt update

# Install npm
sudo apt-get -y install nodejs
sudo apt-get -y install npm

git clone --single-branch https://github.com/hyperledger/caliper.git
(
    cd ~/caliper &&
    git checkout 8cef10ccce9d75397152b2d37af2ea40699cd645 &&
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
