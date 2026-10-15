"""Run the local Mac development stack with ordered startup and owned cleanup."""
import fcntl
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def port_open(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.3):
            return True
    except OSError:
        return False


def main():
    local = ROOT / 'local'
    local.mkdir(exist_ok=True)
    lock = (local / 'start-all.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('The all-in-one launcher is already running.', flush=True)
        return 1
    if port_open(7199) or port_open(7198):
        print('A local server is already running. Stop the old Astron, UberDOG and AI\n'
              'windows before launching the full stack here.', flush=True)
        return 1

    logs = local / 'launcher-logs' / time.strftime('%Y%m%d-%H%M%S')
    logs.mkdir(parents=True, exist_ok=True)
    print('Starting Open Toontown. Ctrl+C stops everything started here.\n'
          'Logs: ' + str(logs), flush=True)
    env = dict(os.environ, PYTHONUNBUFFERED='1', PYTHONFAULTHANDLER='1')
    # Make the existing shell launchers use this same Python installation.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    children = []

    def start(name, script):
        path = logs / (name + '.log')
        output = path.open('wb')
        try:
            process = subprocess.Popen(['sh', str(HERE / script)], cwd=str(HERE),
                                       env=env, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        except Exception:
            output.close()
            raise
        children.append((name, process, output, path))
        print('Starting ' + name + '...', flush=True)
        return process, path

    def check_servers():
        for name, process, _, path in children:
            if process.poll() is not None:
                raise RuntimeError(name + ' exited (code ' + str(process.returncode) + ').\n' +
                                   '\n'.join(path.read_text(errors='replace').splitlines()[-25:]))

    def wait_ready(name, path, marker=None, port=None):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            check_servers()
            if (port is not None and port_open(port)) or (
                    marker is not None and marker in path.read_text(errors='replace')):
                print(name + ' ready.', flush=True)
                return
            time.sleep(0.25)
        raise RuntimeError(name + ' did not become ready within 3 minutes. See ' + str(path))

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        _, path = start('Astron', 'start-astron-server.sh')
        wait_ready('Astron', path, port=7199)
        _, path = start('UberDOG', 'start-uberdog-server.sh')
        wait_ready('UberDOG', path, marker='UberDOG server is ready.')
        _, path = start('AI District', 'start-ai-server.sh')
        wait_ready('AI District', path, marker='ToontownAIRepository: Done.')
        game, game_log = start('Game Client', 'start-game.sh')
        print('Game opening. Closing the game will stop this local server stack.', flush=True)
        while game.poll() is None:
            # The client can exit normally; server exits are unexpected.
            for name, process, _, path in children[:-1]:
                if process.poll() is not None:
                    raise RuntimeError(name + ' stopped. See ' + str(path))
            time.sleep(0.25)
        if game.returncode:
            lines = game_log.read_text(errors='replace').splitlines()
            print('\nGame exited with code %s. Full log: %s' %
                  (game.returncode, game_log), flush=True)
            stages = [line for line in lines if '[Expansion DNA]' in line]
            if stages:
                print('\n'.join(stages), flush=True)
            fatal = next((i for i, line in enumerate(lines)
                          if 'Fatal Python error:' in line), None)
            # Keep the faulting Python frame instead of cutting it off the tail.
            if fatal is not None:
                print('\n'.join(lines[fatal:fatal + 160]), flush=True)
            else:
                print('\n'.join(lines[-100:]), flush=True)
        return game.returncode
    except KeyboardInterrupt:
        print('\nStopping Open Toontown...', flush=True)
        return 0
    except (OSError, RuntimeError) as exc:
        print('\nLaunch stopped: ' + str(exc), flush=True)
        return 1
    finally:
        # Only stop process groups created by this launcher, never other sessions.
        for _, process, _, _ in reversed(children):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for _, process, output, _ in reversed(children):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            output.close()
        lock.close()
        print('Local stack stopped. Logs saved in ' + str(logs), flush=True)


if __name__ == '__main__':
    sys.exit(main())
