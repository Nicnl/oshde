# coding=utf-8

import time
import random
import docker.errors
from .classes.async_container_killer import AsyncContainerKiller

def async_kill(docker_client, container_id):
    async_killer = AsyncContainerKiller(docker_client, container_id)
    async_killer.start()

def container_exists(docker_client, container_id):
    try:
        docker_client.containers.get(container_id)
        return True
    except docker.errors.NotFound:
        return False

def kill_containers(docker_client, should_kill_rule):
    killed_containers = []

    print('  Searching for containers...')
    for container in docker_client.containers.list():
        if not should_kill_rule(container):
            continue

        # Attention, le .kill() n'envoie que le signal mais n'attends pas la fin réelle du container
        async_kill(docker_client, container.id)
        killed_containers.append(container)

    # Du coup on attends nous-même comme des gros sagouins
    total_killed_containers = len(killed_containers)

    while len(killed_containers) > 0:
        container = random.choice(killed_containers)
        if not container_exists(docker_client, container.id):
            killed_containers.remove(container)
            print('    Killed %s' % container.name)
        else:
            time.sleep(0.02)

    if total_killed_containers == 0:
        print('  => No containers found!')
    else:
        print('  => All %d containers have been successfully killed!' % total_killed_containers)
