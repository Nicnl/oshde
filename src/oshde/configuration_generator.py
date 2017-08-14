import oshde.config as config

def generate_haproxy_configuration(containers_to_run):
    # Génération de la configuration HAProxy
    haproxy_conf = []
    with open('haproxy.cfg') as file:
        for line in [line.rstrip() for line in file.readlines()]:
            if line == '# OSHDE-HAPROXY-BACKENDS':
                for container_to_run in containers_to_run:
                    if container_to_run['http_port'] is None:
                        continue

                    haproxy_conf.append('backend %s' % container_to_run['name'])
                    haproxy_conf.append('   mode http')
                    haproxy_conf.append('   server www1 %s:%s check port %s' % (
                        container_to_run['haproxy_domain'],
                        container_to_run['http_port'],
                        container_to_run['http_port']
                    ))
                    haproxy_conf.append('')
            elif line == '# OSHDE-HAPROXY-FRONTENDS':
                haproxy_acl = []
                haproxy_uses = []
                hosts_deny = []

                for container_to_run in containers_to_run:
                    if container_to_run['http_port'] is None:
                        continue

                    acl_is_host = 'is_' + container_to_run['name']
                    hosts_deny.append('!' + acl_is_host)

                    haproxy_acl.append('   acl %s hdr(host) -i %s%s' % (
                        acl_is_host,
                        container_to_run['haproxy_domain'],
                        '' if config.haproxy_port == 80 else (':' + str(config.haproxy_port))
                    ))

                    haproxy_uses.append('   use_backend %s if %s' % (
                        container_to_run['name'],
                        acl_is_host
                    ))

                haproxy_conf.append('bind 0.0.0.0:%s' % str(config.haproxy_port))
                haproxy_conf.append('option http-server-close')
                haproxy_conf.append('')
                haproxy_conf += haproxy_acl
                haproxy_conf.append('')
                haproxy_conf.append('   http-request deny if %s' % ' '.join(hosts_deny))
                haproxy_conf.append('')
                haproxy_conf += haproxy_uses
            else:
                haproxy_conf.append(line)

    return haproxy_conf
