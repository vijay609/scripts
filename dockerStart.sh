#!/bin/sh
die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -le 1 ] || die "1 argument required, $# provided"
container=$(docker ps -af "name=$1" --format "{{.Names}}")

xhost +local:$container
docker start $container

if [ -z "$2" ]
then
	docker exec -it $1 bash
else
	docker exec -it $1 $2 bash
fi


