#!/bin/sh
## $1 = <path to the .svo file/recording>

CONTAINER_NAME=zedDevEnvironment

docker exec -it ${CONTAINER_NAME} /bin/bash -c "cd /usr/local/zed/tools \
    && ./ZED\ Explorer"