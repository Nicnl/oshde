# coding=utf-8

import os

orchestrator_prefix = os.getenv('OSHDE_ORCHESTRATOR_PREFIX', 'oshde-')
orchestrator_name = os.getenv('OSHDE_ORCHESTRATOR_NAME', orchestrator_prefix + 'orchestrator')
kill_everything = bool(os.getenv('OSHDE_KILL_EVERYTHING', 'true'))
