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


if __name__ == '__main__':
    unittest.main()
