# coding=utf-8

import oshde.container_helper as cth
import oshde.config as config
import docker

client = docker.from_env()

if config.kill_everything:
    print('Existing containers should be killed...')
    cth.kill_containers(client, lambda name:
        name != config.orchestrator_name and  # On ne kill pas l'orchestrateur (nous-même)
        name.startswith(config.orchestrator_prefix)  # Mais que ceux ayant le préfixe
    )

print('end ok')
exit(50)

#for tag in container.image.tags:
#    image_name, image_version = tag.split(':')
#    print('image_name: ' + image_name)
#    print('image_version: ' + image_version)

#print(client.containers.run("ubuntu", "echo hello world"))
