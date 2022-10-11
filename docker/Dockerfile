# syntax=docker/dockerfile:experimental
FROM nvcr.io/nvidia/l4t-pytorch:r32.6.1-pth1.9-py3

# ENV http_proxy="http://192.168.123.161:3128"
# ENV https_proxy="http://192.168.123.161:3128"
# ENV ftp_proxy="http://192.168.123.161:3128"

# install package
ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        vim \
        tree \
        curl \
        sudo \
        less \
        emacs \
        apt-utils \
        tzdata \
        git \
        tmux \
        bash-completion \
        command-not-found \
        libglib2.0-0 \
        gstreamer1.0-plugins-* \
        libgstreamer1.0-* \
        libgstreamer-plugins-*1.0-* \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#RUN apt update && apt install -y --no-install-recommends build-essential wget tree curl cmake sudo less emacs  \
#    apt-utils tzdata git tmux vim bash-completion command-not-found libglib2.0-0  \
#    gstreamer1.0-plugins-* libgstreamer1.0-* libgstreamer-plugins-*1.0-*

# Update PIP then turn off the caching.
RUN ln -s /usr/bin/pip3 /usr/bin/pip
RUN rm /usr/bin/python
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip install -U pip
ENV PIP_NO_CACHE_DIR=1

#COPY config/nvidia_icd.json /usr/share/vulkan/icd.d/

# Install LCM
RUN apt-get -y update && apt-get install -y make gcc-8 g++-8
RUN cd /root && git clone https://github.com/lcm-proj/lcm.git && cd lcm && mkdir build && cd build && cmake .. && make -j && make install
RUN ls /root/lcm/lcm-python
RUN cd /root/lcm/lcm-python && pip install -e .

# Install ROS
ENV ROS_DISTRO melodic
RUN apt-get install -y gnupg
RUN curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC1CF6E31E6BADE8868B172B4F42ED6FBAB17C654' | sudo apt-key add -
# RUN apt-key adv --keyserver-options http-proxy=$http_proxy --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
RUN echo "deb http://packages.ros.org/ros/ubuntu bionic main" > /etc/apt/sources.list.d/ros-latest.list

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    ros-melodic-ros-core=1.4.1-0* \
    ros-melodic-rgbd-launch \
    ros-melodic-ddynamic-reconfigure \
    ros-melodic-realsense2-camera \
    ros-melodic-catkin \
    python3-catkin-pkg-modules \
    python-catkin-tools && rm -rf /var/lib/apt/lists/*

# bootstrap rosdep
RUN pip install rospkg wstool vcstools catkin_pkg rosdep
#RUN rm /etc/ros/rosdep/sources.list.d/20-default.list
RUN rosdep init
RUN rosdep update
RUN pip install --user git+https://github.com/catkin/catkin_tools.git

RUN apt-get update
RUN apt-get install -y freeglut3-dev libudev-dev libgl1-mesa-dev libudev1 libudev-dev libgtk2.0-dev pkg-config