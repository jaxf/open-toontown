"""Payload integrity tests; no host test substitutes for device execution."""
import plistlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ios.package_ipa import audit_payload, check_device, relocate_binary, relocate_extension


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / 'Example.app'
        self.extensions = self.app / 'python/lib/python3.13/lib-dynload'
        self.extensions.mkdir(parents=True)
        (self.app / 'Frameworks').mkdir()

    def test_extension_markers_round_trip_and_preserve_binary(self):
        source = self.extensions / '_ssl.cpython-313-iphoneos.so'
        source.write_bytes(b'device-binary')
        binary = relocate_extension(self.app, source, self.extensions)
        self.assertEqual(binary.read_bytes(), b'device-binary')
        marker = source.with_suffix('.fwork')
        self.assertEqual(self.app / marker.read_text().strip(), binary)
        self.assertEqual((binary.parent / (binary.name + '.origin')).read_text().strip(),
                         marker.relative_to(self.app).as_posix())
        with (binary.parent / 'Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        self.assertEqual(info['CFBundlePackageType'], 'FMWK')
        self.assertEqual(info['CFBundleExecutable'], binary.name)
        self.assertFalse(source.exists())

    def test_module_name_collision_is_rejected(self):
        first = self.extensions / '_ssl.cpython-313-iphoneos.so'
        first.write_bytes(b'one')
        relocate_extension(self.app, first, self.extensions)
        second = self.extensions / '_ssl.abi3.so'
        second.write_bytes(b'two')
        with self.assertRaises(FileExistsError):
            relocate_extension(self.app, second, self.extensions)
        self.assertTrue(second.is_file())

    def test_same_cpu_simulator_binary_is_rejected(self):
        with patch('ios.package_ipa.run', side_effect=['', ' platform IOSSIMULATOR\n']):
            with self.assertRaisesRegex(ValueError, 'Not an iPhoneOS'):
                check_device(Path('arm64-simulator'))

    def test_macos_library_cannot_leak_into_device_app(self):
        dependencies = 'app:\n\t/opt/homebrew/lib/libssl.dylib (compatibility version 1.0.0)\n'
        with patch('ios.package_ipa.check_device'), patch('ios.package_ipa.run', return_value=dependencies):
            with self.assertRaisesRegex(ValueError, 'Unexpected native dependency'):
                relocate_binary(self.app, self.app / 'OpenToontown')

    def test_missing_payload_fails_before_archive_creation(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete app'):
            audit_payload(self.app)


if __name__ == '__main__':
    unittest.main()
