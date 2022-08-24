#!/bin/bash

rsync -r --info=progress2 ../jetson-model-deployment unitree@192.168.123.15:/scratch/gmargo/
#rsync -r src unitree@192.168.123.13:/scratch/gmargo/jetson-model-deployment
#rsync -r third_party unitree@192.168.123.13:/scratch/gmargo/jetson-model-deployment
