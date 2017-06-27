# coding=utf-8

import oshde.color_helper as color_helper

from threading import Thread

class ContainerLogsGatherer(Thread):
    def __init__(self, docker_client, container_id, queue, color, encoding='ascii'):
        Thread.__init__(self)
        self.docker_client = docker_client
        self.container = self.docker_client.containers.get(container_id)
        self.color = color
        self.queue = queue
        self.encoding = encoding

    def run(self):
        for lines in self.container.logs(stdout=True, stderr=True, stream=True, timestamps=False, follow=True):
            for line in lines.decode(self.encoding).split('\n'):
                if len(line.strip()) > 0:
                    self.queue.put('%s[%s]%s %s' % (self.color, self.container.name, color_helper.reset, line.rstrip()))