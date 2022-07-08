# Deployment

## ToDos

- [ ] get the docker image to work (currently does not run)
  - test if the bare-bone docker image runs. 
  - build within the jetson
- [ ] run the python lcm example, while running the legged sdk example, and print out the message data
- [ ] add the legged SDK here
- [ ] add the jetson deployment example here. The deployment repo contain the docker image for deployment, and the python script that runs the LCM publisher with the neural controller.

Need to get everything to run today.

## Guide

In one terminal:

```bash
ssh unitree@192.168.123.15
cd /scratch/gmargo/unitree_legged_sdk
./start_unitree_[sdk or controller].sh
```

In another terminal:
```bash
ssh unitree@192.168.123.15
cd /scratch/gmargo/jetson-model-deployment/docker
make run
```
[now you are in the docker container]
```bash
cd jetson_deploy/scripts
python deploy_policy.py  [* currently error occurs here]
```
[you will be prompted to press enter for the robot to (1) stand up and (2) start the control]
