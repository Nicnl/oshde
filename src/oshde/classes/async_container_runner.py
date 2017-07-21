# coding=utf-8

import oshde.color_helper as color_helper
import oshde.container_helper as cth
from threading import Thread


class AsyncContainerRunner(Thread):
    def __init__(self, docker_client, logs_queue, container_to_run, **kwargs):
        Thread.__init__(self)
        self.docker_client = docker_client
        self.logs_queue = logs_queue
        self.container_to_run = container_to_run
        self.kwargs = kwargs

    def run(self):
        container = cth.run_detach_and_remove(
            docker_client=self.docker_client,
            image=self.container_to_run['docker_image_tag'],
            command=None,
            stdout=True,
            stderr=False,
            **self.kwargs
        )

        for lines in container.logs(stdout=True, stderr=True, stream=True, timestamps=False, follow=True):
            for line in lines.decode('ascii').split('\n'):
                if len(line.strip()) > 0:
                    self.logs_queue.put('%s[%s]%s %s' % (self.container_to_run['color'], container.name, color_helper.reset, line.rstrip()))
