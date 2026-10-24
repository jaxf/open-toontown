"""Generate isolated, private-network server configuration without editing dev files."""
import ipaddress
import json
from pathlib import Path
import re

VERSION = 'sv1.0.47.38'
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(n) for n in
                         ('127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12',
                          '192.168.0.0/16', '100.64.0.0/10'))


def private_address(value):
    address = ipaddress.ip_address(value)
    if not any(address in network for network in PRIVATE_NETWORKS):
        raise ValueError('Use a loopback/private IPv4 or VPN address, never a public/wildcard bind')
    return str(address)


def prc_path(value):
    path = Path(value).resolve()
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(path)):
        raise ValueError('Server paths must be absolute Unix paths without spaces/control characters')
    return path


def configuration(root, state, bind='127.0.0.1', district='Toon Valley'):
    root, state = prc_path(root), prc_path(state)
    bind = private_address(bind)
    if not re.fullmatch(r'[A-Za-z0-9 -]{1,40}', district):
        raise ValueError('District name must be 1–40 letters, digits, spaces or hyphens')
    objects = [('CentralLogger', 4688), ('AvatarFriendsManager', 4686),
               ('TTPlayerFriendsManager', 4687), ('TTSpeedchatRelay', 4712),
               ('DistributedDeliveryManager', 4683), ('TTCodeRedemptionMgr', 4695),
               ('AstronLoginManager', 4670)]
    astron = {
        'daemon': {'name': 'Open Toontown private server'},
        'general': {'eventlogger': '127.0.0.1:7197',
                    'dc_files': [str(root / 'etc/otp.dc'), str(root / 'etc/toon.dc')]},
        'messagedirector': {'bind': '127.0.0.1:7199'},
        'uberdogs': [dict(zip(('class', 'id', 'anonymous'), (name, oid, oid == 4670)))
                    for name, oid in objects],
        'roles': [
            {'type': 'clientagent', 'bind': bind + ':7198', 'version': VERSION,
             'client': {'relocate': True, 'add_interest': 'enabled', 'heartbeat_timeout': 60000},
             'channels': {'min': 1000000000, 'max': 1009999999}},
            {'type': 'stateserver', 'control': 4002},
            {'type': 'database', 'control': 4003,
             'generate': {'min': 100000000, 'max': 399999999},
             'backend': {'type': 'yaml', 'directory': str(state / 'astrondb')}},
            {'type': 'dbss', 'database': 4003,
             'ranges': [{'min': 100000000, 'max': 399999999}]},
            {'type': 'eventlogger', 'bind': '127.0.0.1:7197',
             'output': str(state / 'logs/events-%y%m%d_%H%M%S.log')},
        ],
    }
    prc = '\n'.join([
        'dedicated-server #t', 'accountdb-type invite',
        'accountdb-invite-file ' + str(state / 'accounts.sqlite3'),
        'default-access-level NO_ACCESS', 'want-dev #f', 'exec-chat #f',
        'log-private-info #f', 'verify-ssl #t', 'window-type none',
        'audio-library-name null', 'server-data-folder ' + str(state / 'world'),
        'spellbook-config-file ' + str(state / 'world/spellbook.json'),
        'district-name ' + district, 'air-connect 127.0.0.1:7199',
        'eventlog-host 127.0.0.1:7197', '',
    ])
    return astron, prc


def write_configuration(root, state, bind, district):
    astron, prc = configuration(root, state, bind, district)
    state = Path(state).resolve()
    for name in ('astrondb', 'world', 'logs'):
        (state / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    # JSON is a YAML subset supported by Astron's yaml-cpp parser.
    (state / 'astrond.yml').write_text(json.dumps(astron, indent=2) + '\n')
    (state / 'server.prc').write_text(prc)
    return state / 'astrond.yml', state / 'server.prc'
