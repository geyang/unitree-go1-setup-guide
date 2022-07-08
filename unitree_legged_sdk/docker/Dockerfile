FROM ubuntu:18.04

RUN apt-get update && apt-get install -y git

# install cmake

RUN apt-get install -y gcc-8 g++-8 make
RUN apt-get install -y cmake libopenmpi-dev python3-dev zlib1g-dev
RUN apt-get update && apt-get install -y build-essential
RUN apt-get install -y libglib2.0-dev

# install lcm

RUN mkdir /scratch && mkdir /scratch/unitree
RUN cd /scratch/unitree && git clone https://github.com/lcm-proj/lcm.git && cd lcm && mkdir build && cd build && cmake .. && make -j && make install

# install boost

RUN apt-get install -y libboost-all-dev


# development tools

RUN apt-get install -y vim htop tmux
