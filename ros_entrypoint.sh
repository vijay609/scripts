#!/bin/bash
set -e

# setup ros environment
source "/opt/ros/kinetic/setup.bash"

export PATH=$PATH:/src/ardupilot/Tools/autotest
export PATH=/usr/lib/ccache:$PATH

#source /usr/share/gazebo/setup.sh
#export GAZEBO_MODEL_PATH=/px4src/ardupilot_gazebo/models:${GAZEBO_MODEL_PATH}
#export GAZEBO_RESOURCE_PATH=/px4src/ardupilot_gazebo/worlds:${GAZEBO_RESOURCE_PATH}

exec "$@"

