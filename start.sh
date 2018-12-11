#!/bin/bash

export PATH=/home/pi/miniconda3/bin:$PATH

while true
do
    source activate env && python3 app.py
    sleep 5
done