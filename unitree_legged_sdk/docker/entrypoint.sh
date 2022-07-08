#!/bin/bash
mkdir build
cd build && cmake ../ && make

eval "bash"

exec "$@"
