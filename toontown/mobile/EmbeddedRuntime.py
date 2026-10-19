"""Main-thread game lifecycle used by the native UIKit app host.

No local servers, replacement game loop, or reduced-content demo. Missing
native dependencies fail before launch instead of silently disabling features.
"""
import builtins
import importlib
import threading

from toontown.mobile import Client
from toontown.mobile.Session import Session


def movement_allowed(base, focused_item=None):
    """Conservative walking overlay policy; activity-specific controls follow."""
    if focused_item is not None:
        return False
    avatar = getattr(base, 'localAvatar', None)
    manager = getattr(avatar, 'controlManager', None)
    return bool(getattr(avatar, 'avatarControlsEnabled', False) and
                getattr(manager, 'isEnabled', False) and
                getattr(manager, 'currentControlsName', None) in ('walk', 'swim', 'ghost'))


class Runtime:
    def __init__(self, bundle_root, user_data, platform_config, host, token):
        self._owner = threading.get_ident()
        self._started = False
        self._launch_attempted = False
        self._paused = False
        self._closed = False
        self._launcher = None
        self._session = Session(host, token)
        self._paths = (bundle_root, user_data, platform_config)
        Client.prepare(self._session, bundle_root, user_data, True, platform_config)
        modules = {}
        for name in ('panda3d.core', 'panda3d.direct', 'panda3d.physics',
                     'panda3d.otp', 'panda3d.toontown', 'panda3d.ode', 'pytz', 'ssl'):
            modules[name] = importlib.import_module(name)
        # The module itself can import successfully even when optional native
        # APIs were omitted at build time. The game unconditionally uses HTTP.
        if not hasattr(modules['panda3d.core'], 'HTTPClient'):
            raise ImportError('The embedded engine requires the HTTPClient API')

    def _check_thread(self):
        if threading.get_ident() != self._owner:
            raise RuntimeError('Embedded runtime called from a different thread')

    def start(self):
        self._check_thread()
        if self._closed or self._launch_attempted:
            raise RuntimeError('Embedded game cannot be restarted in this process')
        self._launch_attempted = True
        bundle, data, config = self._paths
        self._launcher = Client.start(self._session, bundle, data, True, config)
        self._started = True

    def frame(self):
        self._check_thread()
        if self._closed or not self._started or self._paused:
            return False
        Client.step()
        from panda3d.core import PGItem
        return movement_allowed(getattr(builtins, 'base', None), PGItem.get_focus_item())

    def pause(self):
        self._check_thread()
        if self._closed or not self._started or self._paused:
            return
        self._paused = True
        from direct.showbase.MessengerGlobal import messenger
        messenger.send('PandaPaused')

    def resume(self):
        self._check_thread()
        if self._closed or not self._started or not self._paused:
            return
        from direct.showbase.MessengerGlobal import messenger
        messenger.send('PandaRestarted')
        self._paused = False

    def close(self):
        self._check_thread()
        if self._closed:
            return
        self._closed = True
        self._started = False
        self._session = None
        self._launcher = None
        # Also clean up ShowBase if startup raised after opening its window.
        base = getattr(builtins, 'base', None)
        if base is not None:
            # ShowBase.destroy stops rendering/tasks but does not own the
            # game's connection repository. Stop its socket/reader as well.
            try:
                repository = getattr(base, 'cr', None)
                if repository is not None:
                    repository.shutdown()
            finally:
                base.destroy()
