# coding=utf-8

import docker
import yaml
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

            # Fichier de conf: port HTTP à transférer à Traefik
            if 'http_port' not in oshde_conf:
                print('http_port should be in configuration file! Aborting...')
                print('')
                continue
            oshde_conf_http_port = int(oshde_conf['http_port']) # Fixme: Vérifier type

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

                    if mount_host_path.startswith('./'):  # Fixme: Voir si y'a pas plus propre, ex: os.path.???
                        mount_host_path = mount_host_path.lstrip('./')

                        # Ici on n'utilise pas os.path car on deal avec un chemin du type d'OS de l'hôte != docker
                        # Fixme: voir comment faire autrement=
                        mount_host_path = os.path.join(config.dynvirtualhosts_host, domain_dir, mount_host_path)

                    oshde_conf_volumes[mount_host_path] = {
                        'bind': mount_container_path,
                        'mode': mode
                    }

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
        stream=False
    )
    print('')

    containers_to_run.append({
        'docker_image_tag': docker_image_tag,
        'name': config.prefix + dockerized_domain_dir,
        'color': color,
        'volumes': oshde_conf_volumes,
        'environment': oshde_conf_environment,
        'traefik_domain': domain_dir,
        'http_port': oshde_conf_http_port
    })

print('# Starting containers...')

for container_to_run in containers_to_run:
    # Lancement des containers fraîchement buildés
    container = cth.run_detach_and_remove(client, container_to_run['docker_image_tag'],
        auto_remove=True,
        remove=True,
        name=container_to_run['name'],
        detach=True,
        network=config.network,
        volumes=container_to_run['volumes'],
        environment=container_to_run['environment']
    )

    # Démrrage des threads de collecte des logs
    logs_gatherer = ContainerLogsGatherer(client, container.id, logs_queue, container_to_run['color'])
    logs_gatherer.start()

print('# Generating configuration and starting traefik...')

# Génération de la configuration Traefik
traefik_conf = []
with open('traefik.toml') as file:
    for line in [line.rstrip() for line in file.readlines()]:
        if line == '# OSHDE-BACKENDS':
            for container_to_run in containers_to_run:
                traefik_conf.append('  [backends.%s_back]' % container_to_run['name'])
                traefik_conf.append('    [backends.%s_back.servers.server1]' % container_to_run['name'])
                traefik_conf.append('      url = "http://%s:%d"' % (container_to_run['name'], container_to_run['http_port']))
                traefik_conf.append('')
        elif line == '# OSHDE-FRONTENDS':
            for container_to_run in containers_to_run:
                traefik_conf.append('  [frontends.%s_front]' % container_to_run['name'])
                traefik_conf.append('    backend = "%s_back"' % container_to_run['name'])
                traefik_conf.append('    passHostHeader = true')
                traefik_conf.append('    [frontends.%s_front.routes.%s]' % (container_to_run['name'], container_to_run['name']))
                traefik_conf.append('      rule = "Host:%s"' % container_to_run['traefik_domain'])
                traefik_conf.append('')
        else:
            traefik_conf.append(line)

traefik_path = os.path.join(config.dynvirtualhosts_path, config.prefix + 'traefik')
if not os.path.exists(traefik_path):
    os.makedirs(traefik_path)

traefik_toml_path = os.path.join(traefik_path, 'traefik.toml')
with open(traefik_toml_path, 'w') as traefik_toml:
    traefik_toml.write('\n'.join(traefik_conf))

# Démarrage de Traefik
traefik_container = cth.run_detach_and_remove(client, 'traefik',
    auto_remove=True,
    remove=True,
    name=config.prefix + 'traefik',
    detach=True,
    network=config.network,
    volumes={
        os.path.join(config.dynvirtualhosts_host, config.prefix + 'traefik', 'traefik.toml'): {
            'bind': '/etc/traefik/traefik.toml',
            'mode': 'ro'
        }
    },
    ports={
        '80/tcp': 80  # Fixme: utiliser variable d'environnement
    }
)

print('# Displaying queued logs...')
print('')

while True:
    print(logs_queue.get(block=True, timeout=None))
