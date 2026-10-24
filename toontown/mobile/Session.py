"""Explicit, client-only connection settings for private hosted play."""
from dataclasses import dataclass, field
import ipaddress
import re


@dataclass(frozen=True)
class Session:
    host: str
    token: str = field(repr=False)
    port: int = 7198

    def __post_init__(self):
        address = ipaddress.ip_address(self.host)
        networks = ('127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12',
                    '192.168.0.0/16', '100.64.0.0/10')
        if not any(address in ipaddress.ip_network(n) for n in networks):
            raise ValueError('This build requires an IPv4 private/VPN server, not public TCP')
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError('Invalid server port')
        if not isinstance(self.token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', self.token):
            raise ValueError('An issued invitation token is required (developer login is disabled)')

    @property
    def endpoint(self):
        return '%s:%s' % (self.host, self.port)

    def prc(self, embedded=False):
        # No credentials in PRC files, debug output, command lines or app assets.
        settings = [
            'game-server ' + self.endpoint, 'server-port ' + str(self.port),
            'server-failover', 'server-want-ssl #f', 'verify-ssl #t',
            'tt-specific-login #t', 'required-login playToken',
            'fake-playtoken', 'fake-blue', 'fake-DISLToken', 'fake-DISL-PlayerName',
            'log-private-info #f', 'want-dev #f', 'exec-chat #f',
        ]
        if embedded:
            # The native display host owns presentation/frame pacing. Preserve
            # its sync-video setting instead of overriding it after platform PRC.
            settings += ['toontown-auto-run #f', 'mobile-client #t',
                         'aspect-ratio 0']
        return '\n'.join(settings) + '\n'
