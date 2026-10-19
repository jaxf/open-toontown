"""Supervise one private Astron + UberDOG + AI stack; no game client is started.

If any child exits, tear down only owned children and fail, so systemd can
restart the entire dependency chain. Readiness is bounded and checked in order.
"""
import argparse
import importlib
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid
from server.config import write_configuration

ROOT = Path(__file__).resolve().parents[1]


def port_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def preflight(astron):
    if sys.platform != 'linux':
        raise RuntimeError('Dedicated runner targets Linux; use the existing local launchers on Mac')
    if not astron.is_file() or not os.access(str(astron), os.X_OK):
        raise RuntimeError('Provide an executable Linux Astron build with --astron')
    for module in ('panda3d.core', 'panda3d.direct', 'panda3d.ode', 'panda3d.physics',
                   'panda3d.otp', 'panda3d.toontown', 'pytz'):
        importlib.import_module(module)
    for path in ('resources/phase_3', 'resources/phase_4', 'etc/otp.dc', 'etc/toon.dc'):
        if not (ROOT / path).exists():
            raise RuntimeError('Missing required game content: ' + path)


def supervise(commands, state, bind):
    children = []
    logs = state / 'logs'
    def check():
        for name, process, _, _ in children:
            if process.poll() is not None:
                raise RuntimeError('%s exited with code %s; inspect its log' % (name, process.returncode))

    def stop(signum, frame):
        raise KeyboardInterrupt

    old_handlers = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for name, command, marker in commands:
            # A fresh file avoids a previous run's readiness markers.
            log_path = logs / (name + '-' + time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8] + '.log')
            output = log_path.open('ab')
            try:
                process = subprocess.Popen(command, cwd=str(ROOT), stdout=output,
                    stderr=subprocess.STDOUT, start_new_session=True,
                    env=dict(os.environ, PYTHONUNBUFFERED='1', PYTHONFAULTHANDLER='1',
                             PYTHONDONTWRITEBYTECODE='1'))
            except BaseException:
                output.close()
                raise
            children.append((name, process, output, log_path))
            deadline = time.monotonic() + 180
            while True:
                check()
                if marker is None:
                    ready = port_open('127.0.0.1', 7199) and port_open(bind, 7198)
                else:
                    with log_path.open('rb') as log:
                        log.seek(max(0, log_path.stat().st_size - 131072))
                        ready = marker.encode() in log.read()
                if ready:
                    print(name + ' ready', flush=True)
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(name + ' did not become ready within 180 seconds')
                time.sleep(0.25)
        print('Private district ready; clients may connect. This is not an internet-public service.', flush=True)
        while True:
            check()
            time.sleep(1)
    except KeyboardInterrupt:
        return 0
    finally:
        for _, process, _, _ in reversed(children):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for _, process, output, _ in reversed(children):
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            output.close()
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


def commands(astron, astron_config, prc):
    common = ['etc/Configrc.prc', str(prc)]
    return [
        ('astron', [str(astron), '--loglevel', 'info', str(astron_config)], None),
        ('uberdog', [sys.executable, '-m', 'toontown.uberdog.UDStart'] + common,
         'UberDOG server is ready.'),
        ('district', [sys.executable, '-m', 'toontown.ai.AIStart'] + common,
         'ToontownAIRepository: Done.'),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--astron', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--district', default='Toon Valley')
    parser.add_argument('--check', action='store_true', help='Check dependencies/config only; start nothing')
    args = parser.parse_args()
    astron, state = args.astron.resolve(), args.state.resolve()
    # Configuration validation happens even for the non-mutating check.
    from server.config import configuration
    configuration(ROOT, state, args.bind, args.district)
    preflight(astron)
    if args.check:
        print('Dependencies present; not a live server or an iOS compatibility test.')
        return 0
    import fcntl
    os.umask(0o077)
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / 'server.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if port_open('127.0.0.1', 7199) or port_open(args.bind, 7198):
            raise RuntimeError('A server already owns the configured ports; refusing to duplicate it')
        astron_config, prc = write_configuration(ROOT, state, args.bind, args.district)
        return supervise(commands(astron, astron_config, prc), state, args.bind)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ImportError, RuntimeError, ValueError) as exc:
        print('Dedicated server stopped: ' + str(exc), file=sys.stderr)
        sys.exit(1)
