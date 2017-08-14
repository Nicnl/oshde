# coding=utf-8
from docker.errors import NotFound
from threading import Thread
import time

import oshde.color_helper as color_helper


class AsyncContainerChecker(Thread):
    def __init__(self, docker_client, logs_queue, containers_to_check):
        Thread.__init__(self)
        self.docker_client = docker_client
        self.logs_queue = logs_queue
        self.containers_to_check = containers_to_check
        self.should_stop = False

    def ask_stop(self):
        self.should_stop = True

    def run(self):
        containers = {}
        containers_colors = {}

        for container_data in self.containers_to_check:
            while True:
                try:
                    container_name = container_data['haproxy_domain']
                    containers[container_name] = self.docker_client.containers.get(container_name)
                    containers_colors[container_name] = container_data['color']
                    break
                except NotFound:
                    time.sleep(0.2)

        while not self.should_stop:
            removed_containers = []

            for name, container in containers.items():
                try:
                    container.reload()
                except NotFound:
                    removed_containers.append(name)
                    self.logs_queue.put('%s############ CONTAINER \'%s\' HAS TERMINATED ############%s' % (containers_colors[name], name, color_helper.reset))

            for container_name in removed_containers:
                del containers[container_name]

            time.sleep(1)
