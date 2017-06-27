# coding=utf-8

from threading import Thread

class AsyncContainerKiller(Thread):
    def __init__(self, docker_client, container_id):
        Thread.__init__(self)
        self.docker_client = docker_client
        self.container_id = container_id

    def run(self):
        container = self.docker_client.containers.get(self.container_id)
        container.kill()
