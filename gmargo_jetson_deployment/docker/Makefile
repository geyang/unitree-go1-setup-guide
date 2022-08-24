default: build release
build:
	docker build -t jetson-model-deployment .
clean-build:
	docker build -t jetson-model-deployment . --no-cache=true
run:
	#docker run jetson-model-deployment
	docker run -it \
	    --env="DISPLAY" \
	    --env="QT_X11_NO_MITSHM=1" \
	    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	    --env="XAUTHORITY=${XAUTH}" \
	    --volume="${XAUTH}:${XAUTH}" \
	    --volume="/scratch/gmargo/jetson-model-deployment/:/home/isaac/jetson-model-deployment" \
	    --privileged \
	    --runtime=nvidia \
	    --net=host \
	    --workdir="/home/isaac/jetson-model-deployment" \
	    episodeyang/jetson-legged-deployment bash
	    #/home/isaac/legged_gym_dev/docker/entrypoint.sh
release:
	docker tag jetson-model-deployment improbableailab/jetson-model-deployment
	docker push improbableailab/jetson-model-deployment

build-amd:
	docker build -t jetson-model-deployment-amd -f DockerfileAMD .
clean-build-amd:
	docker build -t jetson-model-deployment-amd -f DockerfileAMD . --no-cache=true
run-amd:
	#docker run jetson-model-deployment
	docker run -it \
	    --env="DISPLAY" \
	    --env="QT_X11_NO_MITSHM=1" \
	    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
	    --env="XAUTHORITY=${XAUTH}" \
	    --volume="${XAUTH}:${XAUTH}" \
	    --volume="/scratch/gmargo/jetson-model-deployment/:/home/isaac/jetson-model-deployment" \
	    --privileged \
	    --runtime=nvidia \
	    --net=host \
	    --workdir="/home/isaac/jetson-model-deployment" \
	    jetson-model-deployment-amd /home/isaac/legged_gym_dev/docker/entrypoint.sh

