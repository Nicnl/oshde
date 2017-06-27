# coding=utf-8

import time
import random
import docker.errors
import re
import six
from docker.models.images import Image
from docker.utils.json_stream import json_stream
from oshde import color_helper
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

def build_and_print(docker_client, print_name, print_color, **kwargs):
    resp = docker_client.api.build(**kwargs)

    if isinstance(resp, six.string_types):
        return docker_client.images.get(resp)

    last_event = None
    for chunk in json_stream(resp):
        if 'error' in chunk:
            raise docker.errors.BuildError(chunk['error'])
        if 'stream' in chunk:
            for line in chunk['stream'].split('\n'):
                if len(line.rstrip()) > 0:
                    print('%s[%s]%s %s' % (print_color, print_name, color_helper.reset, line.rstrip()), flush=True)

            match = re.search(
                r'(Successfully built |sha256:)([0-9a-f]+)',
                chunk['stream']
            )
            if match:
                image_id = match.group(2)
                return docker_client.images.get(image_id)
        last_event = chunk

    raise docker.errors.BuildError(last_event or 'Unknown')

# Fixme: Virer cette fonction quand https://github.com/docker/docker-py/pull/1545 aura été mergé
def run_detach_and_remove(docker_client, image, command=None, stdout=True, stderr=False, remove=False, **kwargs):
        if isinstance(image, Image):
            image = image.id

        detach = kwargs.pop("detach", False)

        if kwargs.get('network') and kwargs.get('network_mode'):
            raise RuntimeError('The options "network" and "network_mode" can not be used together.')

        try:
            container = docker_client.containers.create(image=image, command=command, detach=detach, **kwargs)
        except docker.errors.ImageNotFound:
            docker_client.containers.client.images.pull(image)
            container = docker_client.containers.create(image=image, command=command, detach=detach, **kwargs)

        container.start()

        if detach:
            return container

        exit_status = container.wait()
        if exit_status != 0:
            stdout = False
            stderr = True
        out = container.logs(stdout=stdout, stderr=stderr)
        if remove:
            container.remove()
        if exit_status != 0:
            raise docker.errors.ContainerError(container, exit_status, command, image, out)
        return out
