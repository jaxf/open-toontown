"""Foundation tests, not a claim of live multiplayer or iOS device coverage."""
import ast
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from ios.stage_game import PHASES, game_files, stage
from otp.login.TokenStore import TokenStore
from server.config import configuration, private_address
from server.run import commands, supervise
from toontown.mobile.Session import Session
from toontown.mobile.TouchInput import TouchInput, stick_keys

ROOT = Path(__file__).resolve().parents[1]


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'accounts.sqlite3'
        self.store = TokenStore(self.path)

    def test_only_issued_tokens_work_and_default_is_player(self):
        for invalid in ('dev', '', 'SYSTEM_ADMIN', 'a' * 43, None, 'a' * 10000):
            self.assertIsNone(self.store.lookup(invalid))
        token = self.store.issue('friend')
        self.assertEqual(self.store.lookup(token),
                         dict(databaseId='friend', accessLevel='NO_ACCESS', accountId=0))

    def test_raw_token_is_not_stored(self):
        token = self.store.issue('friend')
        data = self.path.read_bytes()
        self.assertNotIn(token.encode(), data)
        self.assertIn(hashlib.sha256(token.encode()).hexdigest().encode(), data)
        if os.name == 'posix':
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_expiry_and_revocation(self):
        with patch('otp.login.TokenStore.time.time', return_value=100):
            token = self.store.issue('friend', days=1)
        with patch('otp.login.TokenStore.time.time', return_value=86500):
            self.assertIsNone(self.store.lookup(token))
        token = self.store.issue('friend')
        self.store.revoke('friend')
        self.assertIsNone(self.store.lookup(token))

    def test_tokens_rotate_without_losing_toons(self):
        first = self.store.issue('friend')
        self.assertTrue(self.store.bind_account('friend', 100000123))
        self.store.revoke('friend')
        second = self.store.issue('friend')
        self.assertIsNone(self.store.lookup(first))
        self.assertEqual(self.store.lookup(second)['accountId'], 100000123)

    def test_account_mapping_is_unique_and_cannot_be_rebound(self):
        self.store.issue('one'); self.store.issue('two')
        self.assertTrue(self.store.bind_account('one', 100000001))
        self.assertTrue(self.store.bind_account('one', 100000001))
        self.assertFalse(self.store.bind_account('one', 100000002))
        self.assertFalse(self.store.bind_account('two', 100000001))
        self.assertFalse(self.store.bind_account('missing', 100000002))
        for invalid in (0, -1, True, 400000000):
            self.assertFalse(self.store.bind_account('two', invalid))

    def test_issue_does_not_change_existing_privileges(self):
        self.store.issue('friend')
        with self.assertRaises(ValueError):
            self.store.issue('friend', access='SYSTEM_ADMIN')

    def test_validation_and_db_permissions(self):
        for name in ('../friend', 'x\nwant-dev #t', '', 'x' * 65):
            with self.assertRaises(ValueError):
                self.store.issue(name)
        for days in (0, 366):
            with self.assertRaises(ValueError):
                self.store.issue('friend', days=days)
        if os.name == 'posix':
            self.path.chmod(0o644)
            with self.assertRaises(ValueError):
                TokenStore(self.path)

    def test_real_invite_adapter_blocks_duplicate_account_creation(self):
        # Load the production classes without the unavailable custom OTP engine.
        source = ast.parse((ROOT / 'otp/login/AstronLoginManagerUD.py').read_text())
        classes = [n for n in source.body if isinstance(n, ast.ClassDef)
                   and n.name in ('AccountDB', 'InviteAccountDB')]
        config = type('Config', (), {'GetString': lambda _, key, default: str(self.path)})()
        scope = {'config': config}
        exec(compile(ast.Module(body=classes, type_ignores=[]), 'auth-adapter', 'exec'), scope)
        adapter = scope['InviteAccountDB'](None)
        token = self.store.issue('friend')
        responses = []
        adapter.lookup(token, responses.append)
        adapter.lookup(token, responses.append)
        self.assertTrue(responses[0]['success'])
        self.assertFalse(responses[1]['success'])
        adapter.release('friend')
        adapter.lookup(token, responses.append)
        adapter.storeAccountId('friend', 100000001, responses.append)
        adapter.release('friend')
        adapter.lookup(token, responses.append)
        self.assertEqual(responses[-1]['accountId'], 100000001)

    def test_dedicated_mode_never_falls_back_to_developer_auth(self):
        source = ast.parse((ROOT / 'otp/login/AstronLoginManagerUD.py').read_text())
        cls = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'AstronLoginManagerUD')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'announceGenerate')
        settings = {}
        namespace = {
            'config': SimpleNamespace(GetString=lambda key, default: settings.get(key, default),
                                      GetBool=lambda key, default: settings.get(key, default)),
            'NameGenerator': lambda: None,
            'DistributedObjectGlobalUD': SimpleNamespace(announceGenerate=lambda self: None),
            'InviteAccountDB': lambda self: 'invite',
            'DeveloperAccountDB': lambda self: 'developer',
        }
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'backend-selection', 'exec'), namespace)
        manager = SimpleNamespace()
        namespace['announceGenerate'](manager)
        self.assertEqual(manager.accountDb, 'developer')  # Existing local launch unchanged.
        settings['dedicated-server'] = True
        with self.assertRaises(ValueError):
            namespace['announceGenerate'](manager)
        settings['accountdb-type'] = 'invite'
        namespace['announceGenerate'](manager)
        self.assertEqual(manager.accountDb, 'invite')
        settings['accountdb-type'] = 'typo'
        with self.assertRaises(ValueError):
            namespace['announceGenerate'](manager)


class ConfigurationTests(unittest.TestCase):
    def test_loopback_private_and_vpn_addresses_only(self):
        for host in ('127.0.0.1', '10.1.2.3', '192.168.2.1', '172.16.2.1', '100.80.1.2'):
            self.assertEqual(private_address(host), host)
        for host in ('0.0.0.0', '8.8.8.8', '::', '::1', '169.254.1.2', '224.0.0.1', 'localhost'):
            with self.assertRaises(ValueError):
                private_address(host)

    def test_roles_auth_and_persistent_paths(self):
        astron, prc = configuration('/opt/game', '/var/lib/game', '100.80.1.2')
        self.assertEqual(astron['messagedirector']['bind'], '127.0.0.1:7199')
        roles = {r['type']: r for r in astron['roles']}
        self.assertEqual(roles['clientagent']['bind'], '100.80.1.2:7198')
        self.assertEqual(roles['eventlogger']['bind'], '127.0.0.1:7197')
        self.assertEqual(roles['database']['backend']['directory'], '/var/lib/game/astrondb')
        self.assertIn('accountdb-type invite', prc)
        self.assertIn('default-access-level NO_ACCESS', prc)
        self.assertIn('spellbook-config-file /var/lib/game/world/spellbook.json', prc)
        self.assertEqual(astron['general']['dc_files'], ['/opt/game/etc/otp.dc', '/opt/game/etc/toon.dc'])
        self.assertEqual([o['id'] for o in astron['uberdogs'] if o['anonymous']], [4670])

    def test_config_injection_is_rejected(self):
        for district in ('Hi\naccountdb-type developer', 'Hi#comment', ''):
            with self.assertRaises(ValueError):
                configuration('/opt/game', '/var/lib/game', district=district)
        with self.assertRaises(ValueError):
            configuration('/opt/game', '/var/lib/a\nunsafe')

    def test_server_runs_only_three_server_processes(self):
        result = commands(Path('/bin/astrond'), Path('/state/astrond.yml'), Path('/state/server.prc'))
        self.assertEqual([r[0] for r in result], ['astron', 'uberdog', 'district'])
        self.assertTrue(all('Quick' not in ' '.join(r[1]) for r in result))
        self.assertEqual(result[1][1][-2:], ['etc/Configrc.prc', '/state/server.prc'])
        # The default config must not be reloaded after the dedicated overrides.
        ud = (ROOT / 'toontown/uberdog/UDStart.py').read_text()
        self.assertNotIn("loadPrcFile('etc/Configrc.prc')", ud)

    def test_supervisor_detects_child_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / 'logs').mkdir()
            child = [sys.executable, '-c', "print('READY', flush=True); raise SystemExit(7)"]
            with self.assertRaisesRegex(RuntimeError, 'exited with code 7'):
                supervise([('test', child, 'READY')], state, '127.0.0.1')

    def test_supervisor_cleans_up_running_dependencies_on_later_failure(self):
        import subprocess
        original = subprocess.Popen
        children = []
        def record(*args, **kwargs):
            process = original(*args, **kwargs)
            children.append(process)
            return process
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / 'logs').mkdir()
            running = [sys.executable, '-c', "import time; print('READY', flush=True); time.sleep(30)"]
            failing = [sys.executable, '-c', 'raise SystemExit(9)']
            with patch('server.run.subprocess.Popen', side_effect=record):
                with self.assertRaisesRegex(RuntimeError, 'exited with code 9'):
                    supervise([('first', running, 'READY'), ('second', failing, 'READY')],
                              state, '127.0.0.1')
            self.assertEqual(len(children), 2)
            self.assertTrue(all(p.poll() is not None for p in children))

    def test_systemd_writes_state_not_source_and_restarts(self):
        unit = (ROOT / 'deploy/systemd/open-toontown.service').read_text()
        for setting in ('User=toontown', 'Restart=on-failure', 'ProtectSystem=strict',
                        'ReadWritePaths=/var/lib/open-toontown', 'KillMode=control-group'):
            self.assertIn(setting, unit)


class MobileTests(unittest.TestCase):
    def test_session_does_not_expose_token(self):
        token = 'T' * 43
        session = Session('100.80.1.2', token)
        self.assertNotIn(token, repr(session))
        self.assertNotIn(token, session.prc())
        self.assertEqual(session.endpoint, '100.80.1.2:7198')
        self.assertIn('server-failover\n', session.prc())
        self.assertIn('mobile-client #t', session.prc(embedded=True))

    def test_session_rejects_public_or_invalid_inputs(self):
        for host, token, port in [('8.8.8.8', 'a' * 43, 7198),
                                  ('127.0.0.1', 'dev', 7198),
                                  ('127.0.0.1', 'a' * 43, 0),
                                  ('127.0.0.1\nfoo', 'a' * 43, 7198)]:
            with self.assertRaises(ValueError):
                Session(host, token, port)

    def test_client_data_is_outside_bundle(self):
        from otp.settings.Settings import Settings
        from otp.otpbase.ClientPaths import client_path
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'TOONTOWN_USER_DATA': directory}):
            settings = Settings()
            settings.updateSetting('music', False)
            settings.writeSettings()
            loaded = Settings(); loaded.readSettings()
            self.assertFalse(loaded.getSetting('music'))
            self.assertTrue(Path(directory, 'useropt.json').exists())
            self.assertEqual(client_path('logs', 'game.log'), str(Path(directory, 'logs/game.log')))

    def test_touch_holds_are_reference_counted(self):
        events = []
        touch = TouchInput(lambda *args: events.append(args), lambda: 12.5)
        touch.update(1, {'arrow_up'})
        touch.update(2, {'arrow_up', 'control'})
        touch.end(1)
        self.assertNotIn(('arrow_up-up', []), events)
        touch.end(2)
        self.assertEqual(events.count(('arrow_up', [])), 1)
        self.assertEqual(events.count(('arrow_up-up', [])), 1)
        self.assertIn(('time-control-up', [12.5]), events)

    def test_stick_diagonal_release_and_non_finite(self):
        self.assertEqual(stick_keys(0.6, 0.7), {'arrow_up', 'arrow_right'})
        self.assertEqual(stick_keys(0.1, -0.2), set())
        with self.assertRaises(ValueError):
            stick_keys(float('nan'), 0)

    def test_background_releases_everything_and_never_replays_stale_keys(self):
        events = []
        touch = TouchInput(lambda name, args: events.append(name), lambda: 0)
        touch.update(1, {'arrow_up', 'space'})
        touch.set_enabled(False)
        touch.update(2, {'control'})
        self.assertEqual(touch.contacts, {})
        self.assertNotIn('control', events)
        self.assertIn('space-up', events)
        touch.set_enabled(True)
        self.assertEqual(events.count('arrow_up'), 1)

    def test_invalid_key_is_rejected(self):
        touch = TouchInput(lambda *args: None, lambda: 0)
        with self.assertRaises(ValueError):
            touch.update(1, {'unknown'})

    def test_touch_events_drive_real_panda_input_state(self):
        import builtins
        from direct.showbase.InputStateGlobal import inputState
        from direct.showbase.MessengerGlobal import messenger
        with patch.object(builtins, 'messenger', messenger, create=True):
            token = inputState.watch('mobile-test-forward', 'arrow_up', 'arrow_up-up', inputSource='mobile-test')
            touch = TouchInput(messenger.send, lambda: 0)
            try:
                touch.update(1, {'arrow_up'})
                self.assertTrue(inputState.isSet('mobile-test-forward'))
                touch.cancel_all()
                self.assertFalse(inputState.isSet('mobile-test-forward'))
            finally:
                touch.cancel_all()
                token.release()

    def test_prc_remote_overrides_clear_local_defaults(self):
        from panda3d.core import loadPrcFileData, unloadPrcFile, ConfigVariableString, ConfigVariableBool
        default = loadPrcFileData('test-default', 'server-failover 80 443\nfake-playtoken dev')
        page = loadPrcFileData('test-remote', Session('100.80.1.2', 'a' * 43).prc(True))
        try:
            self.assertEqual(ConfigVariableString('server-failover').value, '')
            self.assertEqual(ConfigVariableString('fake-playtoken').value, '')
            self.assertTrue(ConfigVariableBool('mobile-client').value)
        finally:
            unloadPrcFile(page); unloadPrcFile(default)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'game'
        for folder in ('otp', 'toontown', 'assets', 'resources', 'etc', 'local'):
            (self.root / folder).mkdir(parents=True)
        for phase in PHASES:
            path = self.root / 'resources' / ('phase_' + phase)
            path.mkdir()
            (path / 'model.bam').write_bytes(b'fixture')
        for name in ('Configrc.prc', 'otp.dc', 'toon.dc'):
            (self.root / 'etc' / name).write_text('fixture')
        (self.root / 'toontown/client.py').write_text('pass')
        (self.root / 'assets/hq.png').write_bytes(b'fixture')
        (self.root / 'local/secret.txt').write_text('do-not-package')

    def test_full_content_and_hashes_without_private_data(self):
        out = Path(self.temp.name) / 'content.zip'
        count = stage(self.root, out)
        with zipfile.ZipFile(out) as archive:
            manifest = json.loads(archive.read('content-manifest.json'))
            self.assertEqual(len(manifest['files']), count)
            for path, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read('game/' + path)).hexdigest(), digest)
            self.assertNotIn('local/secret.txt', manifest['files'])
            self.assertIn('assets/hq.png', manifest['files'])
            for phase in PHASES:
                self.assertIn('resources/phase_' + phase + '/model.bam', manifest['files'])

    def test_will_not_overwrite_archive(self):
        out = Path(self.temp.name) / 'content.zip'
        stage(self.root, out)
        with self.assertRaises(FileExistsError):
            stage(self.root, out)

    def test_missing_phase_or_external_symlink_fails_closed(self):
        (self.root / 'resources/phase_13/model.bam').unlink()
        with self.assertRaises(ValueError):
            game_files(self.root)
        (self.root / 'resources/phase_13/model.bam').write_bytes(b'fixture')
        (self.root / 'assets/external').symlink_to(self.root / 'local/secret.txt')
        with self.assertRaises(ValueError):
            game_files(self.root)

    def test_output_cannot_be_included_in_its_own_bundle(self):
        with self.assertRaises(ValueError):
            stage(self.root, self.root / 'assets/bad.zip')


if __name__ == '__main__':
    unittest.main()
