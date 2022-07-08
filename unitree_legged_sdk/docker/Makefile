default: build release
build:
	docker build -t unitree-sdk .
clean-build:
	docker build -t unitree-sdk . --no-cache=True
run:
	docker run -it \
		--env="DISPLAY" \
	    --env="QT_X11_NO_MITSHM=1" \
	    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	    --env="XAUTHORITY=${XAUTH}" \
	    --volume="${XAUTH}:${XAUTH}" \
	    --volume="${PWD}/../:/unitree_legged_sdk" \
	    --privileged \
	    --net=host \
	    --workdir="/unitree_legged_sdk" \
	    unitree-sdk /unitree_legged_sdk/docker/entrypoint.sh
