#!/bin/sh

CONTAINER_NAME=jupyterServer
IMAGE_NAME=continuumio/anaconda3:5.0.1

BIND_MOUNTS="-v /src:/src:rw -v /data:/data:rw"

CONTAINER_ID=`docker ps -aqf name="^/${CONTAINER_NAME}"`

if [ -z "${CONTAINER_ID}" ]; then
    JUPYTER_CMD="/opt/conda/bin/conda install jupyter -y --quiet && /opt/conda/bin/jupyter notebook --notebook-dir=/src/ipynb --ip='*' --port=8888 --no-browser --allow-root"
    # create a new container via docker run that starts the jupyter server by default
    CMD="docker run -it -p 8888:8888 \
            ${BIND_MOUNTS} \
            --name=${CONTAINER_NAME} \
            ${IMAGE_NAME} \
            /bin/bash -c \"${JUPYTER_CMD}\""
    echo "Creating a new container.."
    echo ${CMD}
    eval ${CMD}

elif [ -z `docker ps -qf id=${CONTAINER_ID}` ]; then
    echo "Found ${CONTAINER_NAME}....Starting......"
    docker start ${CONTAINER_ID}

    ## TODO : Find out why running attach creates a new jupyter server in the same container
    #docker attach ${CONTAINER_ID}
else
    echo "Found ${CONTAINER_NAME}... Attaching....."
    docker exec -it ${CONTAINER_ID} bash
fi