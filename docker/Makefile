default: build release
build: 
	docker build --progress=plain -t jetson-legged-deployment . 
clean-build: 
	docker build -t jetson-legged-deployment . --no-cache=true
release:
	docker tag jetson-legged-deployment episodeyang/jetson-legged-deployment
	docker push episodeyang/jetson-legged-deployment
run:
	docker run -it \
            --env="DISPLAY" \
            --env="QT_X11_NO_MITSHM=1" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
            --env="XAUTHORITY=${XAUTH}" \
            --volume="${XAUTH}:${XAUTH}" \
            --volume="/home/unitree/mit/jetson-model-deployment/:/home/isaac/jetson-model-deployment" \
            --privileged \
            --runtime=nvidia \
            --net=host \
            --workdir="/home/isaac/jetson-model-deployment" \
            episodeyang/jetson-legged-deployment:latest python /home/isaac/jetson-model-deployment/src/scripts/deploy_no_isaac.py
