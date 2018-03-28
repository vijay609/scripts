#!/bin/sh

CONTAINER_NAME=jupyterServer
IMAGE_NAME=continuumio/anaconda3:5.0.1

BIND_MOUNTS="-v /src:/src:rw -v /data:/data:rw -v /media/vijay/Data/Pictures:/media/vijay/Data/Pictures:rw"

CONTAINER_ID=`docker ps -aqf name="^/${CONTAINER_NAME}$"`

if [ -z "${CONTAINER_ID}" ]; then
    JUPYTER_CMD="/opt/conda/bin/conda install jupyter -y --quiet && /opt/conda/bin/jupyter notebook --notebook-dir=/src/ipynb --ip='*' --port=8888 --no-browser --allow-root"
    # create a new container via docker run that starts the jupyter server by default
    CMD="docker run -it -p 8888:8888 \
            ${BIND_MOUNTS} \
            --name=${CONTAINER_NAME} \
            ${IMAGE_NAME} \
            /bin/bash -c \"${JUPYTER_CMD}\""
    ## ${JUPYTER_CMD} will run everytime the container is started. In this case, once we create a container and open a session with the jupyter server
    ## the browser will establish a session. Now once the container is stopped the jupyter server quits. Now if we start the container again, it will
    ## start the jupyter server again and replace the stale connection with the session in the browser with a new one, if we dont close the browser tab
    echo "Creating a new container.."
    echo ${CMD}
    eval ${CMD}

elif [ -z `docker ps -qf id=${CONTAINER_ID}` ]; then
    echo "Found ${CONTAINER_NAME}.........."
    echo docker start ${CONTAINER_ID}
    docker start ${CONTAINER_ID}
    echo docker attach ${CONTAINER_ID}
    docker attach ${CONTAINER_ID}
else
    echo "Found ${CONTAINER_NAME}.........."
    echo docker exec -it ${CONTAINER_ID} /bin/bash
    docker exec -it ${CONTAINER_ID} /bin/bash
fi