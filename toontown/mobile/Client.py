"""Launch the actual game against a remote private district, without servers.

`embedded=True` is the Python-side entry point for the UIKit host, which
must configure a working iOS graphics pipe BEFORE calling start(), and call
step() on its display link. Graphics are supplied by the native iOS target.
"""
import os
from pathlib import Path


class BundledModelPathError(OSError):
    """A required startup model cannot be resolved inside the app bundle."""


def configure_embedded_paths(bundle_root):
    """Keep Panda's independent VFS cwd aligned with the native app payload."""
    from panda3d.core import Filename, VirtualFileSystem, get_model_path
    bundle_root = Path(bundle_root).resolve()
    vfs = VirtualFileSystem.get_global_ptr()
    # Native static initialization can create the VFS before UIKit/Python
    # changes the OS cwd. os.chdir alone never updates this cached location.
    vfs.chdir(Filename.fromOsSpecific(str(bundle_root)))
    paths = get_model_path()
    existing = {paths.get_directory(i) for i in range(paths.get_num_directories())}
    # Absolute roots also keep model and texture lookup independent of later
    # OS cwd changes. Prepending leaves desktop-configured fallback paths intact.
    for relative in ('engine-models', '.', 'resources'):
        path = Filename.fromOsSpecific(str((bundle_root / relative).resolve()))
        if path not in existing:
            paths.prepend_directory(path)
    for model in ('loading-background', 'progress-background', 'toon_council'):
        filename = Filename('phase_3/models/gui/' + model + '.bam')
        if not vfs.resolve_filename(filename, paths.get_value()) or not vfs.exists(filename):
            raise BundledModelPathError('Required bundled startup model is unavailable')


def prepare(session, bundle_root, user_data, embedded=False, platform_config=None):
    """Load platform configuration before native pipe registration/ShowBase.

    Resolve the content directory before importing core: Panda derives MAIN_DIR
    during its first import. The native host also sets cwd before Python starts.
    """
    bundle_root = Path(bundle_root).resolve()
    user_data = Path(user_data).resolve()
    if platform_config is not None:
        platform_config = Path(platform_config).resolve()
    if embedded and (platform_config is None or not Path(platform_config).is_file()):
        raise ValueError('Embedded startup requires the native host graphics/audio PRC file')
    if bundle_root == user_data or bundle_root in user_data.parents:
        raise ValueError('Client data must live outside the read-only app bundle')
    for item in ('etc/Configrc.prc', 'etc/otp.dc', 'etc/toon.dc', 'resources/phase_3'):
        if not (bundle_root / item).exists():
            raise ValueError('Missing bundled game resource: ' + item)
    user_data.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ['TOONTOWN_USER_DATA'] = str(user_data)
    # Relative DNA, models and Python file references still resolve in the bundle.
    os.chdir(str(bundle_root))
    from panda3d.core import Filename, loadPrcFile, loadPrcFileData
    loadPrcFile(Filename.fromOsSpecific(str(bundle_root / 'etc/Configrc.prc')))
    if platform_config is not None:
        loadPrcFile(Filename.fromOsSpecific(str(Path(platform_config).resolve())))
    loadPrcFileData('private-client', session.prc(embedded))
    if embedded:
        configure_embedded_paths(bundle_root)


def start(session, bundle_root, user_data, embedded=False, platform_config=None):
    prepare(session, bundle_root, user_data, embedded, platform_config)
    from toontown.launcher.QuickLauncher import QuickLauncher

    class RemoteLauncher(QuickLauncher):
        def getGameServer(self):
            return session.endpoint

        def getPlayToken(self):
            # Kept in process memory for reconnect, never environment or logs.
            return session.token

        def getTestServerFlag(self):
            return False

        def mainLoop(self):
            if not embedded:
                super().mainLoop()

    return RemoteLauncher()


def step():
    """Must be called only on the engine/UI thread by the native host."""
    from direct.task.TaskManagerGlobal import taskMgr
    taskMgr.step()


def background(touch_router):
    """Release held inputs before iOS suspends frame delivery; never fake keepalive."""
    touch_router.set_enabled(False)
    from direct.showbase.MessengerGlobal import messenger
    messenger.send('PandaPaused')


def foreground(touch_router):
    from direct.showbase.MessengerGlobal import messenger
    messenger.send('PandaRestarted')
    touch_router.set_enabled(True)
