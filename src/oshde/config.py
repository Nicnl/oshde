# coding=utf-8

import os

prefix = os.getenv('OSHDE_ORCHESTRATOR_PREFIX', 'oshde-')
orchestrator_name = os.getenv('OSHDE_ORCHESTRATOR_NAME', prefix + 'orchestrator')
network = os.getenv('OSHDE_NETWORK', prefix + 'network')

# Si des containers existent déjà: ne pas s'arrêter et les tuer
kill_policy = os.getenv('OSHDE_KILL_POLICY', '1') == '1'

# STOP: Si le réseau existe déjà: s'arrêter
# RECREATE: Si le réseau existe déjà, le recréer
# REUSE: Si le réseau existe déjà, le réutiliser
network_policy = os.getenv('OSHDE_NETWORK_POLICY', 'REUSE')

# Pour tout supprimer et nettoyer
delete_mode = os.getenv('OSHDE_DELETE_MODE', '0') == '1'

dynvirtualhosts_host = '/'
if not delete_mode:
    dynvirtualhosts_host += os.getenv('OSHDE_DYNVIRTUALHOSTS_HOST').rstrip('/').rstrip('\\').replace(':', '').replace('\\', '/').lstrip('/')

    # Workaround:
    #   Docker for Windows v17.12 (win46) changed the mounted host drives location
    #     - Before :          /C/Users/me/Desktop/...
    #     - After  : /host_mnt/c/Users/me/Desktop/...

    if os.getenv('OSHDE_WINDOWS_WORKAROUND', '0') == '1':
        dynvirtualhosts_host = dynvirtualhosts_host[0] + dynvirtualhosts_host[1].lower() + dynvirtualhosts_host[2:]
        dynvirtualhosts_host = '/host_mnt' + dynvirtualhosts_host

dynvirtualhosts_path = os.getenv('OSHDE_DYNVIRTUALHOSTS_PATH', '/dynvirtualhosts').rstrip('/')

# Nom du fichier de conf pour: expositions de ports, montages de volumes, variables d'environnement
dynvirtualhosts_config_file_name = os.getenv('OSHDE_DYNVIRTUALHOSTS_CONFIG_FILE_NAME', '.oshde.yml')
dynvirtualhosts_local_config_file_name = os.getenv('OSHDE_DYNVIRTUALHOSTS_CONFIG_FILE_NAME', '.oshde.local.yml')

haproxy_port = int(os.getenv('OSHDE_HAPROXY_PORT', '80'))
