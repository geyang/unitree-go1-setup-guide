#!/bin/bash

#rsync -r -v --stats --progress unitree@10.42.0.2:/scratch/gmargo/jetson-model-deployment/logs/logs.tar.gz logs
#tar -xzvf logs/logs.tar.gz -C logs/
scp -r unitree@10.42.0.2:/scratch/gmargo/jetson-model-deployment/logs/20220610* logs
#ssh unitree@10.42.0.2 "rm -f /scratch/gmargo/jetson-model-deployment/logs/logs.tar.gz"
#rsync -r src unitree@192.168.123.13:/scratch/gmargo/jetson-model-deployment
#rsync -r third_party unitree@192.168.123.13:/scratch/gmargo/jetson-model-deployment
