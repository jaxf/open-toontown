"""Desktop/mobile settings regressions; not full native game launch coverage."""
import ast
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from panda3d.core import ConfigVariableBool, ConfigVariableInt, loadPrcFileData, unloadPrcFile
from otp.otpbase.ClientPaths import client_path
from otp.settings.Settings import Settings
from toontown.mobile.Session import Session
from toontown.mobile.TouchInput import TouchInput
from toontown.mobile.NativeControls import NativeControls, create

ROOT = Path(__file__).resolve().parents[1]


class EngineStartupBoundary(Exception):
    pass


class PlatformDefaultsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.previous_cwd)
        self.env = patch.dict(os.environ)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop('TOONTOWN_USER_DATA', None)
        self.pages = []
        self.addCleanup(self.clear_pages)

    def clear_pages(self):
        for page in reversed(self.pages):
            unloadPrcFile(page)

    def page(self, name, data):
        page = loadPrcFileData(name, data)
        self.pages.append(page)
        return page

    def configure_actual_toonbase(self):
        # Run the production initializer through its settings stage, stopping
        # exactly at native engine startup (custom OTP is not in stock Panda).
        tree = ast.parse((ROOT / 'toontown/toonbase/ToonBase.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ToonBase')
        init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        def engine_start(_):
            raise EngineStartupBoundary()
        settings_pages = {}
        def apply(name, data):
            settings_pages[name] = data
            return self.page(name, data)
        namespace = dict(Settings=Settings, ConfigVariableBool=ConfigVariableBool,
                         ConfigVariableInt=ConfigVariableInt, loadPrcFileData=apply,
                         OTPBase=SimpleNamespace(OTPBase=SimpleNamespace(__init__=engine_start)))
        exec(compile(ast.Module(body=[init], type_ignores=[]), 'ToonBase-settings', 'exec'), namespace)
        with self.assertRaises(EngineStartupBoundary):
            namespace['__init__'](SimpleNamespace())
        return settings_pages

    def save_options(self):
        settings = Settings()
        for key, value in {'resolution': [1280, 720], 'windowed-mode': False,
                           'music': False, 'sfx': True}.items():
            settings.updateSetting(key, value)
        settings.writeSettings()

    def test_desktop_keeps_existing_settings_and_window_preferences(self):
        self.save_options()
        self.assertEqual(Path(client_path('useropt.json')), Path('useropt.json'))
        loaded = Settings()
        loaded.readSettings()
        self.assertEqual(loaded.getSetting('resolution'), [1280, 720])
        pages = self.configure_actual_toonbase()
        self.assertIn('win-size 1280 720', pages.values())
        self.assertIn('fullscreen True', pages.values())
        self.assertIn('audio-music-active False', pages.values())
        self.assertFalse(ConfigVariableBool('mobile-client', False).value)

    def test_mobile_preserves_native_window_but_keeps_audio_preferences(self):
        self.save_options()
        self.page('native-host', Session('100.80.1.2', 'a' * 43).prc(embedded=True))
        pages = self.configure_actual_toonbase()
        self.assertFalse(any(value.startswith(('win-size ', 'fullscreen ')) for value in pages.values()))
        self.assertIn('audio-music-active False', pages.values())
        self.assertIn('audio-sfx-active True', pages.values())

    def test_mobile_sandbox_does_not_replace_desktop_settings(self):
        self.save_options()
        original = Path('useropt.json').read_bytes()
        sandbox = Path(self.temp.name) / 'mobile-data'
        with patch.dict(os.environ, {'TOONTOWN_USER_DATA': str(sandbox)}):
            mobile = Settings()
            mobile.updateSetting('music', True)
            mobile.writeSettings()
            self.assertTrue((sandbox / 'useropt.json').is_file())
        self.assertEqual(Path('useropt.json').read_bytes(), original)

    def test_remote_desktop_session_does_not_enable_embedded_mode(self):
        config = Session('100.80.1.2', 'a' * 43).prc(embedded=False)
        self.assertNotIn('mobile-client', config)
        self.assertNotIn('toontown-auto-run', config)

    def test_movement_and_jump_can_be_held_and_released_independently(self):
        import builtins
        from direct.showbase.InputStateGlobal import inputState
        from direct.showbase.MessengerGlobal import messenger
        with patch.object(builtins, 'messenger', messenger, create=True):
            walk = inputState.watch('platform-walk', 'arrow_up', 'arrow_up-up')
            jump = inputState.watch('platform-jump', 'control', 'control-up')
            router = TouchInput(messenger.send, lambda: 0)
            try:
                native = NativeControls(router)
                native.set_enabled(True)
                native.move_stick(0, 1)
                native.jump(True)
                self.assertTrue(inputState.isSet('platform-walk'))
                self.assertTrue(inputState.isSet('platform-jump'))
                native.jump(False)
                self.assertTrue(inputState.isSet('platform-walk'))
                self.assertFalse(inputState.isSet('platform-jump'))
                native.close()
                self.assertFalse(inputState.isSet('platform-walk'))
            finally:
                router.cancel_all()
                walk.release()
                jump.release()

    def test_native_adapter_starts_disabled_and_requires_fresh_touch_after_pause(self):
        events = []
        native = NativeControls(TouchInput(lambda key, args: events.append((key, args)), lambda: 7))
        native.move_stick(0, 1)
        native.jump(True)
        self.assertEqual(events, [])
        native.set_enabled(True)
        native.move_stick(-1, 1)
        native.jump(True)
        native.set_enabled(False)
        downs = [key for key, args in events if not key.startswith('time-') and not key.endswith('-up')]
        ups = [key[:-3] for key, args in events if not key.startswith('time-') and key.endswith('-up')]
        self.assertEqual(set(downs), {'arrow_left', 'arrow_up', 'control'})
        self.assertCountEqual(downs, ups)
        count = len(events)
        native.jump(True)
        native.set_enabled(True)
        self.assertEqual(len(events), count)
        native.close()
        native.close()
        self.assertEqual(len(events), count)

    def test_native_adapter_rejects_nonfinite_stick_without_changing_held_input(self):
        router = TouchInput(lambda *args: None, lambda: 0)
        native = NativeControls(router)
        native.set_enabled(True)
        native.move_stick(0, 1)
        for bad in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                native.move_stick(bad, 0)
        self.assertEqual(router.contacts, {'uikit-stick': frozenset({'arrow_up'})})
        native.close()
        self.assertEqual(router.contacts, {})

    def test_native_factory_cannot_attach_to_desktop_client(self):
        self.page('desktop-test', 'mobile-client #f')
        with self.assertRaisesRegex(RuntimeError, 'embedded mobile client'):
            create()


if __name__ == '__main__':
    unittest.main()
