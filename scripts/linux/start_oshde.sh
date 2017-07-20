#!/bin/bash

function kill_orchestrator() {
    docker kill oshde-orchestrator > /dev/null 2> /dev/null
    docker rm oshde-orchestrator > /dev/null 2> /dev/null
}

function start_orchestrator() {
    docker run --rm --name oshde-orchestrator \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v `pwd`:/dynvirtualhosts \
    -e OSHDE_DYNVIRTUALHOSTS_HOST=`pwd` \
    -e OSHDE_DELETE_MODE=$1 \
    hub.nicnl.com/oshde/orchestrator/orchestrator:latest
}

function finish {
    echo '' && echo ''
    kill_orchestrator
    start_orchestrator 1
}
trap finish EXIT

kill_orchestrator
start_orchestrator 0
