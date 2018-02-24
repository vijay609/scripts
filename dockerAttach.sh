#!/bin/sh
die () {
    echo >&2 "$@"
    exit 1
}

docker exec -it $1 /src/scripts/$2 bash

