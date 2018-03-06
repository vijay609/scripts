#!/bin/sh
## $1 = <path to the .svo file/recording>

CONTAINER_NAME=zedDevEnvironment

docker exec -it ${CONTAINER_NAME} /bin/bash -c "/src/zed-examples/svo\ recording/recording/build/ZED_SVO_Recording ${1}"