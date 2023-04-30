#!/bin/bash
export $(cat .env | xargs)
echo ".env loaded"