"""Lifecycle/policy regressions; no claim of native device gameplay."""
import builtins
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

from toontown.mobile import EmbeddedRuntime as embedded


class EmbeddedRuntimeTests(unittest.TestCase):
    def runtime(self):
        with patch.object(embedded.Client, 'prepare'), patch.object(embedded.importlib, 'import_module'):
            return embedded.Runtime('/bundle/Game', '/data', '/bundle/Device.prc',
                                    '100.80.1.2', 'a' * 43)

    def test_configuration_precedes_required_imports_and_missing_ode_blocks_start(self):
        events = []
        def dependency(name):
            events.append(name)
            if name == 'panda3d.ode':
                raise ImportError('missing ODE')
        with patch.object(embedded.Client, 'prepare', side_effect=lambda *args: events.append('config')), \
             patch.object(embedded.Client, 'start') as start, \
             patch.object(embedded.importlib, 'import_module', side_effect=dependency):
            with self.assertRaises(ImportError):
                embedded.Runtime('/bundle', '/data', '/config', '100.80.1.2', 'a' * 43)
        self.assertEqual(events[0], 'config')
        self.assertIn('panda3d.toontown', events)
        start.assert_not_called()

    def test_pause_resume_are_idempotent_and_pause_stops_frames(self):
        runtime = self.runtime()
        messenger = Mock()
        core = SimpleNamespace(PGItem=SimpleNamespace(get_focus_item=lambda: None))
        with patch.object(embedded.Client, 'start'), patch.object(embedded.Client, 'step') as step, \
             patch.dict('sys.modules', {'panda3d.core': core,
                 'direct.showbase.MessengerGlobal': SimpleNamespace(messenger=messenger)}):
            runtime.start()
            runtime.frame()
            runtime.pause()
            runtime.pause()
            runtime.frame()
            self.assertEqual(step.call_count, 1)
            runtime.resume()
            runtime.resume()
            runtime.frame()
            self.assertEqual(step.call_count, 2)
        self.assertEqual([call.args[0] for call in messenger.send.call_args_list],
                         ['PandaPaused', 'PandaRestarted'])

    def test_overlay_disabled_without_avatar_when_controls_disabled_or_gui_focused(self):
        manager = SimpleNamespace(isEnabled=True, currentControlsName='walk')
        avatar = SimpleNamespace(avatarControlsEnabled=True, controlManager=manager)
        base = SimpleNamespace(localAvatar=avatar)
        self.assertFalse(embedded.movement_allowed(None))
        self.assertTrue(embedded.movement_allowed(base))
        self.assertFalse(embedded.movement_allowed(base, object()))
        avatar.avatarControlsEnabled = False
        self.assertFalse(embedded.movement_allowed(base))
        avatar.avatarControlsEnabled = True
        manager.isEnabled = False
        self.assertFalse(embedded.movement_allowed(base))
        manager.isEnabled = True
        manager.currentControlsName = 'battle'
        self.assertFalse(embedded.movement_allowed(base))

    def test_failed_start_still_destroys_partial_showbase_and_cannot_restart(self):
        runtime = self.runtime()
        base = Mock()
        with patch.object(builtins, 'base', base, create=True), \
             patch.object(embedded.Client, 'start', side_effect=RuntimeError('startup failed')):
            with self.assertRaises(RuntimeError):
                runtime.start()
            with self.assertRaisesRegex(RuntimeError, 'cannot be restarted'):
                runtime.start()
            runtime.close()
            runtime.close()
            base.cr.shutdown.assert_called_once_with()
            base.destroy.assert_called_once_with()
            self.assertIsNone(runtime._session)
            with self.assertRaises(RuntimeError):
                runtime.start()

    def test_network_shutdown_failure_still_destroys_window_and_closes_runtime(self):
        runtime = self.runtime()
        base = Mock()
        base.cr.shutdown.side_effect = RuntimeError('network teardown failed')
        with patch.object(builtins, 'base', base, create=True):
            with self.assertRaisesRegex(RuntimeError, 'network teardown failed'):
                runtime.close()
            base.destroy.assert_called_once_with()
            self.assertIsNone(runtime._session)
            runtime.close()
            base.cr.shutdown.assert_called_once_with()

    def test_repeated_start_is_rejected(self):
        runtime = self.runtime()
        with patch.object(embedded.Client, 'start') as start:
            runtime.start()
            with self.assertRaises(RuntimeError):
                runtime.start()
            start.assert_called_once()

    def test_wrong_thread_cannot_advance_game(self):
        runtime = self.runtime()
        errors = []
        def other_thread():
            try:
                runtime.frame()
            except RuntimeError as error:
                errors.append(str(error))
        with patch.object(embedded.Client, 'step') as step:
            thread = threading.Thread(target=other_thread)
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(errors), 1)
            step.assert_not_called()


if __name__ == '__main__':
    unittest.main()
