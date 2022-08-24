#!/bin/bash

set -euxo pipefail

mkdir -p catkin_ws/src
cd catkin_ws/src
git clone -b melodic https://github.com/ros-perception/vision_opencv.git
cd ..
catkin config -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPYTHON_INCLUDE_DIR=/usr/include/python3.6m -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.6m.so
catkin config --install
catkin build