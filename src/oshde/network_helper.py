def find_network(docker_client, rule):
    for network in docker_client.networks.list():
        if rule(network):
            return network
    return None
