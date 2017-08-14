# coding=utf-8

import docker
import time
import yaml
import oshde.main_mechanic as mmc
import oshde.container_helper as cth
import oshde.file_helper as flh
import oshde.config as config
import oshde.color_helper as color_helper
import os
from queue import Queue
from oshde.classes.async_container_runner import AsyncContainerRunner
from oshde.classes.async_container_checker import AsyncContainerChecker
import oshde.configuration_generator as cgen
import docker.models.containers

# Fixme: Virer cette ligne quand https://github.com/docker/docker-py/pull/1545 aura été mergé
docker.models.containers.RUN_HOST_CONFIG_KWARGS += ['auto_remove']

client = docker.from_env()

mmc.check_stop(client, kill=True)
print('')

mmc.check_networks(client)
print('')

if config.delete_mode:
    print('\033[32mEverything was deleted successfully!')
    exit(0)

logs_queue = Queue()

# Fixme: Pas très efficace, à remplacer par un itérateur type os.walk('.').next()[1]
containers_to_run = []
for domain_dir in flh.list_dirs(config.dynvirtualhosts_path):
    dockerfile_path = os.path.join(config.dynvirtualhosts_path, domain_dir, 'Dockerfile')
    if not os.path.isfile(dockerfile_path):
        continue

    color = color_helper.assign_color()
    dockerized_domain_dir = flh.dockerize_domain_dir(domain_dir)
    docker_image_tag = config.prefix + 'images/' + dockerized_domain_dir + ':localbuild'
    print('%s# Building \'%s\'%s' % (color, docker_image_tag, color_helper.reset))

    oshde_conf_path = os.path.join(config.dynvirtualhosts_path, domain_dir, config.dynvirtualhosts_config_file_name)
    if not os.path.isfile(oshde_conf_path):
        print('No %s config file! Aborting...' % config.dynvirtualhosts_config_file_name)
        print('')
        continue

    # Lecture du fichier de conf
    # Todo: Déplacer la lecture du fichier de conf vers un fichier externe
    with open(oshde_conf_path, 'r') as stream:
        try:
            oshde_conf = yaml.load(stream)

            # Fichier de conf: vérification de la version
            expected_version = '0.0.1'
            if oshde_conf['version'] != expected_version:  # Fixme: Vérifier type
                print('Expected configuration file version %s, got %s! Aborting...' % (expected_version, oshde_conf['version']))
                print('')
                continue

            # Todo: Faire un fichier de lecture de conf PAR version, pour scaler correctement lors des évolutions

            # Fichier de conf: port HTTP à transférer à HAProxy
            if 'http_port' not in oshde_conf:
                oshde_conf_http_port = None
            else:
                oshde_conf_http_port = int(oshde_conf['http_port'])  # Fixme: Vérifier type

            # Fichier de conf: ouvertures de ports à la mano
            oshde_manual_ports = {}
            if 'ports' in oshde_conf:
                for line in oshde_conf['ports']:  # Fixme: Vérifier types
                    port_opening_splited = line.split(':')
                    port_opening_protocol = 'tcp'

                    nb_ports = len(port_opening_splited)
                    if '/' in port_opening_splited[nb_ports-1]:
                        port_opening_splited[nb_ports-1], port_opening_protocol = port_opening_splited[nb_ports-1].split('/')

                    if port_opening_protocol not in ['tcp', 'udp']:
                        print('Wtf while port protocol! Aborting...')
                        print('')
                        continue

                    if len(port_opening_splited) == 1:
                        port_opening_host = int(port_opening_splited[0])
                        port_opening_container = int(port_opening_splited[0])
                    elif len(port_opening_splited) == 2:
                        port_opening_host = int(port_opening_splited[0])
                        port_opening_container = int(port_opening_splited[1])
                    else:
                        print('Wtf while ports! Aborting...')
                        print('')
                        continue

                    oshde_manual_ports['%d/%s' % (port_opening_container, port_opening_protocol)] = str(port_opening_host)



            # Fichier de conf: volumes à monter
            oshde_conf_volumes = {}
            if 'volumes' in oshde_conf:
                for line in oshde_conf['volumes']:  # Fixme: Vérifier types
                    splited_line = line.split(':')

                    mode = 'rw'
                    if len(splited_line) == 2:
                        mount_host_path, mount_container_path = splited_line
                    elif len(splited_line) == 3:
                        mount_host_path, mount_container_path, mode = splited_line  # Fixme: vérifier si mode est rw ou ro
                    else:
                        print('Wtf while reading volumes! Aborting...')
                        print('')
                        continue

                    if mount_host_path == '.':
                        mount_host_path = os.path.join(config.dynvirtualhosts_host, domain_dir)
                    elif mount_host_path.startswith('./'):  # Fixme: Voir si y'a pas plus propre, ex: os.path.???
                        mount_host_path = mount_host_path.lstrip('./')

                        # Ici on n'utilise pas os.path car on deal avec un chemin du type d'OS de l'hôte != docker
                        # Fixme: voir comment faire autrement=
                        mount_host_path = os.path.join(config.dynvirtualhosts_host, domain_dir, mount_host_path)

                    oshde_conf_volumes[mount_host_path] = {
                        'bind': mount_container_path,
                        'mode': mode
                    }

            extra_hosts = []
            if 'extra_hosts' in oshde_conf:  # Fixme: Vérifier types
                for extra_host in oshde_conf['extra_hosts']:
                    extra_hosts += [extra_host]

            url_strip_prefix = None
            if 'url_strip_prefix' in oshde_conf:  # Fixme: Vérifier types
                url_strip_prefix = '/' + oshde_conf['url_strip_prefix'].lstrip('/').rstrip('/') + '/'

            url_add_prefix = None
            if 'url_add_prefix' in oshde_conf:  # Fixme: Vérifier types
                url_add_prefix = '/' + oshde_conf['url_add_prefix'].lstrip('/').rstrip('/') + '/'

            # Fichier de conf: variables d'environnement
            oshde_conf_environment = {}
            if 'environment' in oshde_conf:
                for line in oshde_conf['environment']:  # Fixme: Vérifier types
                    environment_name, environment_value = line.split('=', 2)  # Fixme: Checker si '=' bien présent
                    oshde_conf_environment[environment_name] = environment_value

        except yaml.YAMLError as exc:
            print('Error when reading config file! Aborting...')
            print('')
            continue


    # Build des containers
    image = cth.build_and_print(client, dockerized_domain_dir, color,
        path=os.path.join(config.dynvirtualhosts_path, domain_dir),
        tag=docker_image_tag,
        nocache=False,
        pull=True,
        stream=False,
        rm=True
    )
    print('')

    containers_to_run.append({
        'docker_image_tag': docker_image_tag,
        'name': config.prefix + dockerized_domain_dir,
        'color': color,
        'volumes': oshde_conf_volumes,
        'environment': oshde_conf_environment,
        'haproxy_domain': domain_dir,
        'extra_hosts': extra_hosts,
        'url_strip_prefix': url_strip_prefix,
        'url_add_prefix': url_add_prefix,
        'http_port': oshde_conf_http_port,
        'ports': oshde_manual_ports
    })

print('# Starting containers...')

async_container_checker = AsyncContainerChecker(client, logs_queue, containers_to_run)
async_container_checker.start()

for container_to_run in containers_to_run:
    # Lancement des containers fraîchement buildés

    async_container_runner = AsyncContainerRunner(docker_client=client, logs_queue=logs_queue, container_to_run=container_to_run,
        auto_remove=True,
        remove=True,
        name=container_to_run['haproxy_domain'],
        detach=True,
        network=config.network,
        volumes=container_to_run['volumes'],
        environment=container_to_run['environment'],
        ports=container_to_run['ports'],
        labels={
            'oshde': 'oshde' # Fixme: Déplacer ça vers fichier de configuration
        }
    )

    async_container_runner.start()

    time.sleep(0.25)
    print('%s  => %s%s' % (container_to_run['color'], container_to_run['haproxy_domain'], color_helper.reset))

print('# Generating configuration and starting haproxy...')

# Génération de la configuration HAProxy
haproxy_conf = cgen.generate_haproxy_configuration(containers_to_run)

haproxy_path = os.path.join(config.dynvirtualhosts_path, config.prefix + 'haproxy')
if not os.path.exists(haproxy_path):
    os.makedirs(haproxy_path)

haproxy_cfg_path = os.path.join(haproxy_path, 'haproxy.cfg')
with open(haproxy_cfg_path, 'w') as haproxy_cfg:
    haproxy_cfg.write('\n'.join(haproxy_conf))

# Démarrage de HAProxy
haproxy_container = cth.run_detach_and_remove(client, 'haproxy:alpine',
    auto_remove=True,
    remove=True,
    name=config.prefix + 'haproxy',
    detach=True,
    network=config.network,
    volumes={
        os.path.join(config.dynvirtualhosts_host, config.prefix + 'haproxy', 'haproxy.cfg'): {
            'bind': '/usr/local/etc/haproxy/haproxy.cfg',
            'mode': 'ro'
        }
    },
    ports={
        '80/tcp': config.haproxy_port
    },
    labels={
        'oshde': 'oshde'  # Fixme: Déplacer ça vers fichier de configuration
    }
)

print('# Displaying queued logs...')
print('')

try:
    while True:
        print(logs_queue.get(block=True, timeout=None))
except KeyboardInterrupt:
    async_container_checker.ask_stop()
    async_container_checker.join()
    mmc.check_stop(client, kill=False)
