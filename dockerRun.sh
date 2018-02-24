#!/bin/sh

# dockerRun.sh <dockerImage> <containerName>
xhost +

docker run -it --privileged \
    --env=LOCAL_USER_ID="$(id -u)" \
    -v /home/vbaiyya/src:/src:rw \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -e DISPLAY=unix$DISPLAY \
    -p 14556:14556/udp \
    --name=$2 $1 bash
