# coding=utf-8

import os

prefix = os.getenv('OSHDE_ORCHESTRATOR_PREFIX', 'oshde-')
orchestrator_name = os.getenv('OSHDE_ORCHESTRATOR_NAME', prefix + 'orchestrator')
network = os.getenv('OSHDE_NETWORK', prefix + 'network')

# Si des containers existent déjà: ne pas s'arrêter et les tuer
kill_policy = bool(os.getenv('OSHDE_KILL_POLICY', 'true'))

# STOP: Si le réseau existe déjà: s'arrêter
# RECREATE: Si le réseau existe déjà, le recréer
# REUSE: Si le réseau existe déjà, le réutiliser
network_policy = os.getenv('OSHDE_NETWORK_POLICY', 'REUSE')

dynvirtualhosts_path = os.getenv('OSHDE_DYNVIRTUALHOSTS_PATH', '/dynvirtualhosts').rstrip('/')
