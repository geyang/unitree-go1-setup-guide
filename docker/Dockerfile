# syntax=docker/dockerfile:experimental
# To pull this image, create an account and login according to
# this SO post:
#    https://stackoverflow.com/a/70970425
FROM nvcr.io/nvidia/l4t-pytorch:r32.6.1-pth1.9-py3
# FROM nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth1.13-py3

# ENV http_proxy="http://192.168.123.161:3128"
# ENV https_proxy="http://192.168.123.161:3128"
# ENV ftp_proxy="http://192.168.123.161:3128"

# install package
ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt update -y
RUN apt install -y --no-install-recommends \
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
        libgstreamer-plugins-*1.0-*

# Install ROS
ENV ROS_DISTRO melodic
RUN apt-get install -y gnupg
RUN curl -sSL 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xC1CF6E31E6BADE8868B172B4F42ED6FBAB17C654' | sudo apt-key add -
# RUN apt-key adv --keyserver-options http-proxy=$http_proxy --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
RUN echo "deb http://packages.ros.org/ros/ubuntu bionic main" > /etc/apt/sources.list.d/ros-latest.list
RUN apt update -y
RUN apt install -y --no-install-recommends \
    ros-melodic-ros-core=1.4.1-0* \
    ros-melodic-rgbd-launch \
    ros-melodic-ddynamic-reconfigure \
    ros-melodic-realsense2-camera \
    ros-melodic-catkin \
    python3-catkin-pkg-modules \
    python-catkin-tools

RUN apt update -y
RUN apt install -y python3.8 python3.8-dev
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
# RUN rm /usr/bin/python3
# Has to upgrade pip, otherwise it won't work
RUN curl https://bootstrap.pypa.io/get-pip.py | python -

# bootstrap rosdep
RUN pip install rospkg wstool vcstools catkin_pkg rosdep
#RUN rm /etc/ros/rosdep/sources.list.d/20-default.list
RUN rosdep init
RUN rosdep update
RUN pip install --user git+https://github.com/catkin/catkin_tools.git

RUN apt-get install -y freeglut3-dev libudev-dev libgl1-mesa-dev libudev1 libudev-dev libgtk2.0-dev pkg-config

# Install LCM
RUN apt install -y make gcc-8 g++-8
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-7 700 --slave /usr/bin/g++ g++ /usr/bin/g++-7
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-8 800 --slave /usr/bin/g++ g++ /usr/bin/g++-8
# ENV CPPFLAGS="$(pkg-config --cflags python3)"
RUN cd /root && git clone https://github.com/lcm-proj/lcm.git && cd lcm && mkdir build && cd build && cmake .. && make -j && make install
#RUN ls /root/lcm/lcm-python
RUN cd /root/lcm/lcm-python && pip install -e .

# turn off caching
ENV PIP_NO_CACHE_DIR=1


RUN apt clean
RUN rm -rf /var/lib/apt/lists/*
