# coding=utf-8

import docker
import oshde.main_mechanic as mmc

client = docker.from_env()

mmc.check_kill(client)
print('')

mmc.check_networks(client)
print('')

#for tag in container.image.tags:
#    image_name, image_version = tag.split(':')
#    print('image_name: ' + image_name)
#    print('image_version: ' + image_version)

#print(client.containers.run("ubuntu", "echo hello world"))
