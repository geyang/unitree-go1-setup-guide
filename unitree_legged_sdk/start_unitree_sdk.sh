#!/bin/bash

python /scratch/gmargo/jetson-model-deployment/jetson_deploy/utils/network_config_unitree.py
cd /scratch/gmargo/unitree_legged_sdk/build && ./lcm_position lowlevel