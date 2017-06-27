# coding=utf-8

import docker
import oshde.main_mechanic as mmc
import oshde.container_helper as cth
import oshde.file_helper as flh
import oshde.config as config
import oshde.color_helper as color_helper
import os
from queue import Queue
from oshde.classes.container_logs_gatherer import ContainerLogsGatherer

import docker.models.containers

# Fixme: Virer cette ligne quand https://github.com/docker/docker-py/pull/1545 aura été mergé
docker.models.containers.RUN_HOST_CONFIG_KWARGS += ['auto_remove']

client = docker.from_env()

mmc.check_kill(client)
print('')

mmc.check_networks(client)
print('')

logs_queue = Queue()

# Fixme: Pas très efficace, à remplacer par un itérateur type os.walk('.').next()[1]
for domain_dir in flh.list_dirs(config.dynvirtualhosts_path):
    color = color_helper.assign_color()
    dockerfile_path = os.path.join(config.dynvirtualhosts_path, domain_dir, 'Dockerfile')

    if not os.path.isfile(dockerfile_path):
        continue

    dockerized_domain_dir = flh.dockerize_domain_dir(domain_dir)
    docker_image_tag = config.prefix + 'images/' + dockerized_domain_dir + ':localbuild'

    print('%s# Building \'%s\'%s' % (color, docker_image_tag, color_helper.reset))
    image = cth.build_and_print(client, dockerized_domain_dir, color,
        path=os.path.join(config.dynvirtualhosts_path, domain_dir),
        tag=docker_image_tag,
        nocache=False,
        pull=True,
        stream=False
    )
    print('')

    container = cth.run_detach_and_remove(client, docker_image_tag,
        auto_remove=True,
        remove=True,
        name=config.prefix + dockerized_domain_dir,
        detach=True
    )

    logs_gatherer = ContainerLogsGatherer(client, container.id, logs_queue, color)
    logs_gatherer.start()

print('')
while True:
    print(logs_queue.get(block=True, timeout=None))
