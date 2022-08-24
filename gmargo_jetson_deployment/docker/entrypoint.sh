#!/bin/bash
set -e

# setup ros environment
#source "/root/catkin_ws/devel/setup.bash"

# cd /home/isaac/jetson-model-deployment/third_party/UnitreecameraSDK/build && cmake .. && make -j
source /opt/ros/melodic/setup.bash
export ROS_MASTER_URI=http://192.168.123.161:11311

cd /home/isaac/jetson-model-deployment && python3 -m pip install -e .

eval "bash"

exec "$@"
