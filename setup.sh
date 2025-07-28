#!/bin/bash

echo "Bootstrapping Erebus Latency Test on $(hostname)..."

# Step 1: Update and install essentials
apt update && apt install -y python3-pip git

# Step 2: Clone the test repo
git clone https://github.com/v0id-user/script-test-latncy.git /root/latency-test

# Step 3: Install Python dependencies
pip3 install websockets rich nest_asyncio

# Step 4: Run the test
cd /root/latency-test
python3 main.py
