#!/bin/bash

docker run --rm --name oshde-orchestrator \
-v /var/run/docker.sock:/var/run/docker.sock \
-v `pwd`:/dynvirtualhosts \
-e OSHDE_DYNVIRTUALHOSTS_HOST=`pwd` \
-e OSHDE_DELETE_MODE=$1 \
hub.nicnl.com/oshde/orchestrator/orchestrator:haproxy
