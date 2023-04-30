#!/bin/bash

# set cwd to current location
cd "${0%/*}" 

./stop.sh
echo "Waiting 30s for containers to stop"
sleep 30
./resume.sh
