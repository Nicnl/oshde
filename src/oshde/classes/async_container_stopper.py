# coding=utf-8

from threading import Thread


class AsyncContainerStopper(Thread):
    def __init__(self, docker_client, container_id, kill=False):
        Thread.__init__(self)
        self.docker_client = docker_client
        self.container_id = container_id
        self.kill = kill

    def run(self):
        container = self.docker_client.containers.get(self.container_id)

        if self.kill:
            container.kill()
        else:
            container.stop(timeout=30)  # Todo: Déplacer ce timeout vers la config
