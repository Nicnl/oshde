import oshde.config as config

def generate_haproxy_configuration(containers_to_run):
    # Génération de la configuration HAProxy
    haproxy_conf = []
    haproxy_set_paths = {}
    with open('haproxy.cfg') as file:
        for line in [line.rstrip() for line in file.readlines()]:
            if line == '# OSHDE-HAPROXY-FRONTENDS':
                haproxy_acl = []
                haproxy_uses = []
                hosts_deny = []

                for container_to_run in containers_to_run:
                    if container_to_run['http_port'] is None:
                        continue

                    path_beg_acl = None

                    acl_is_host = 'is_' + container_to_run['name']

                    extra_hosts = ''
                    for extra_host in container_to_run['extra_hosts']:
                        extra_hosts += ' -i %s' % extra_host

                    haproxy_acl.append('   acl %s hdr(host) -i %s%s%s' % (
                        acl_is_host,
                        container_to_run['haproxy_domain'],
                        '' if config.haproxy_port == 80 else (':' + str(config.haproxy_port)),
                        extra_hosts
                    ))

                    set_paths = []
                    if container_to_run['url_strip_prefix'] is not None:
                        path_beg_acl = 'beg_' + acl_is_host

                        haproxy_acl.append('   acl %s path_beg -i %s if %s' % (
                            path_beg_acl,
                            container_to_run['url_strip_prefix'],
                            acl_is_host
                        ))
                        if container_to_run['url_add_prefix'] is not None:
                            set_paths.append('http-request set-path %s%%[path,regsub(^%s,)]' % (
                                container_to_run['url_add_prefix'],
                                container_to_run['url_strip_prefix']
                            ))
                        else:
                            set_paths.append('http-request set-path /%%[path,regsub(^%s,)]' % (
                                container_to_run['url_strip_prefix']
                            ))

                    if container_to_run['url_add_prefix'] is not None:
                        if container_to_run['url_strip_prefix'] is None:
                            set_paths.append('http-request set-path %s' % (
                                container_to_run['url_add_prefix'] + '%[path,regsub(^/,)]'
                            ))

                    haproxy_set_paths[container_to_run['name']] = set_paths
                    hosts_deny.append('!%s' % (path_beg_acl if path_beg_acl is not None else acl_is_host))

                    haproxy_uses.append('   use_backend %s if %s%s' % (
                        container_to_run['name'],
                        acl_is_host,
                        '' if path_beg_acl is None else (' ' + path_beg_acl)
                    ))

                haproxy_conf.append('bind 0.0.0.0:%s' % str(config.haproxy_port))
                haproxy_conf.append('option http-server-close')
                haproxy_conf.append('')
                haproxy_conf += haproxy_acl
                haproxy_conf.append('')
                haproxy_conf.append('   http-request deny if %s' % ' '.join(hosts_deny))
                haproxy_conf.append('')
                haproxy_conf += haproxy_uses

            elif line == '# OSHDE-HAPROXY-BACKENDS':
                for container_to_run in containers_to_run:
                    if container_to_run['http_port'] is None:
                        continue

                    haproxy_conf.append('backend %s' % container_to_run['name'])
                    haproxy_conf.append('   mode http')

                    for set_path in haproxy_set_paths[container_to_run['name']]:
                        haproxy_conf.append('   %s' % set_path)

                    haproxy_conf.append('   server www1 %s:%s check port %s' % (
                        container_to_run['haproxy_domain'],
                        container_to_run['http_port'],
                        container_to_run['http_port']
                    ))
                    haproxy_conf.append('')

            else:
                haproxy_conf.append(line)

    return haproxy_conf
