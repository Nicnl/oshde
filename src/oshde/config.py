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

dynvirtualhosts_path = os.getenv('OSHDE_DYNVIRTUALHOSTS_PATH', '/dynvirtualhosts').rstrip('/')

# Nom du fichier de conf pour: expositions de ports, montages de volumes, variables d'environnement
dynvirtualhosts_config_file_name = os.getenv('OSHDE_DYNVIRTUALHOSTS_CONFIG_FILE_NAME', '.oshde.yml')

traefik_port = int(os.getenv('OSHDE_TRAEFIK_PORT', '80'))
