.EXPORT_ALL_VARIABLES:

VERSION=`<VERSION`

default: build release
build: 
	docker build --progress=plain -t jetson-legged-deployment:v$(VERSION) .
clean-build: 
	docker build -t jetson-legged-deployment:v$(VERSION) . --no-cache=true
release:
	docker tag jetson-legged-deployment:v$(VERSION) episodeyang/jetson-legged-deployment:v$(VERSION)
	docker tag jetson-legged-deployment:v$(VERSION) episodeyang/jetson-legged-deployment:latest
	docker push episodeyang/jetson-legged-deployment:v$(VERSION)
	docker push episodeyang/jetson-legged-deployment:latest
run:
	docker run -it \
            --env="DISPLAY" \
            --env="QT_X11_NO_MITSHM=1" \
            --env="PYTHONPATH=${PYTHONPATH}:/" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
            --env="XAUTHORITY=${XAUTH}" \
            --volume="${XAUTH}:${XAUTH}" \
            --volume="/home/unitree/mit/unitree-go1-setup-guide/jetson_deploy:/jetson_deploy" \
            --privileged \
            --runtime=nvidia \
            --net=host \
            --workdir="/" \
            episodeyang/jetson-legged-deployment:latest python /jetson_deploy/scripts/deploy_policy.py
