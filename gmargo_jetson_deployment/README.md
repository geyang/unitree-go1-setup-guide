# docker-starter
Dockerfile and code for default_dockerfile_name (replace this with your project name!).

Users can either build the docker image from this repository or pull it from dockerhub.

**Option A.** _Pulling from dockerhub_

```docker pull default_dockerfile_name:latest```

**Option B.** _Building from dockerfile_

First, pull this repo

Then run

```
cd docker
python3 docker_build.py
```

## Running the image

Once you `docker_build.py` finishes successfully, you have the `default_dockerfile_name:latest` image built locally. Launch this image as a container & enter the container with

```
./run_image.bash
```

A few helper scripts in `scripts` will run the code.

[Describe some helper scripts here]
```
./[my_scriptname].sh
```

