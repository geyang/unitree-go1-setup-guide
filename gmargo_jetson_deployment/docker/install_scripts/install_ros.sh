#!/bin/bash

set -euxo pipefail

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654

echo "deb http://packages.ros.org/ros/ubuntu bionic main" > /etc/apt/sources.list.d/ros-latest.list

apt-get update && apt-get install -y --no-install-recommends \
    ros-melodic-ros-core=1.4.1-0* \
    ros-melodic-rgbd-launch \
    ros-melodic-ddynamic-reconfigure \
    ros-melodic-realsense2-camera \
    ros-melodic-catkin \
    python3-catkin-pkg-modules \
    python-catkin-tools && rm -rf /var/lib/apt/lists/*

#pip3 install rosdep rospkg rosinstall_generator rosinstall wstool vcstools catkin_pkg


pip3 install rospkg wstool vcstools catkin_pkg rosdep && rm /etc/ros/rosdep/sources.list.d/20-default.list && rosdep init && rosdep update
pip3 install --user git+https://github.com/catkin/catkin_tools.git


#
#source /opt/ros/melodic/setup.bash
#mkdir -p catkin_ws/src
#cd catkin_ws/src
#git clone -b melodic https://github.com/ros-perception/vision_opencv.git
#cd ..
#catkin config -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPYTHON_INCLUDE_DIR=/usr/include/python3.6m -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.6m.so
#catkin config --install
#catkin build