#!/bin/sh
## $1 = <optional path to zedContainerSetup.sh inside the container>

CONTAINER_NAME=zedDevEnvironment
IMAGE_NAME=nvidia/cudagl:9.1-devel-ubuntu16.04

ZED_CONTAINER_SETUP_SCRIPT=$1
if [ -z ${ZED_CONTAINER_SETUP_SCRIPT} ];then
    ZED_CONTAINER_SETUP_SCRIPT="/src/scripts/zedContainerSetup.sh"
fi

BIND_MOUNTS="-v /tmp/.X11-unix:/tmp/.X11-unix:ro -v /src:/src:rw -v /data:/data:rw"

CONTAINER_ID=`docker ps -aqf name="^/${CONTAINER_NAME}$"`

if [ -z "${CONTAINER_ID}" ]; then
    ## At the time of container creation we run the zedContainerSetup.sh script that installs 
    ## the zed sdk and other dependencies like opencv
    CMD="nvidia-docker run -itd --privileged \
        -e DISPLAY=unix${DISPLAY} \
         ${BIND_MOUNTS} \
         --name=${CONTAINER_NAME} \
         ${IMAGE_NAME} \
         /bin/bash "
    echo "Creating a new container.."
    echo ${CMD}
    xhost +
    eval ${CMD}

    ## Container created in detached mode... now run the setup script
    CONTAINER_ID=`docker ps -aqf name="^/${CONTAINER_NAME}$"`
    docker exec -it ${CONTAINER_ID} /bin/bash -c "cd /tmp \
            && cp /src/scripts/zedContainerSetup.sh . \
            && chmod +x zedContainerSetup.sh \
            && ./zedContainerSetup.sh "

elif [ -z `docker ps -qf id=${CONTAINER_ID}` ]; then
    echo "Found ${CONTAINER_NAME}....Starting......"
    xhost +local:${CONTAINER_ID}
    docker start ${CONTAINER_ID}
    docker attach ${CONTAINER_ID}
else
    echo "Found ${CONTAINER_NAME}... Attaching....."
    docker exec -it ${CONTAINER_ID} bash
fi
