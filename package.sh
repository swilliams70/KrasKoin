#!/bin/bash

echo "Building packages..."

pyinstaller --onefile --windowed --name "kk_server" kk_server.py
echo "kk_server built"

pyinstaller --onefile --windowed --name "kk_miner" kk_miner.py
echo "kk_miner built"

echo "Building packages all complete"
