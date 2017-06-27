# coding=utf-8
import oshde.config as config
import oshde.container_helper as cth
import oshde.network_helper as nth
import time

def check_networks(docker_client):
    existing_network = nth.find_network(docker_client, lambda network:
        network.name == config.network
    )

    if existing_network is None:
        print('The network %s doesn\'t exists!' % config.network)
    else:
        print('The network %s already exists!' % existing_network.name)
        if config.network_policy == 'STOP':
            print('  => The network policy asked to stop...')
            exit(1)
        elif config.network_policy == 'RECREATE':
            print('  => The network policy asked to recreate...')
            print('  => Deleting existing network...')
            existing_network.remove()

            while nth.find_network(docker_client, lambda network: network.id == existing_network.id) is not None:
                time.sleep(0.05)
            print('  => Network removed!')

            existing_network = None
        elif config.network_policy == 'REUSE':
            print('  => The network policy asked to reuse...')
        else:
            print('  => The network policy \'%s\' is unknown!' % config.network_policy)
            exit(1)


    if existing_network is None:
        print('  => Creating network...')
        docker_client.networks.create(config.network,
            driver='bridge',
            internal=False,
            enable_ipv6=False
        )
        print('  => Network created!')

def check_kill(docker_client):
    if config.kill_policy:
        print('Existing containers should be killed...')
        cth.kill_containers(docker_client, lambda container:
            container.name != config.orchestrator_name and  # On ne kill pas l'orchestrateur (nous-même)
            container.name.startswith(config.prefix)  # Mais que ceux ayant le préfixe
        )
