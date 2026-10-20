"""Real Panda VFS/model loading with a stale native-startup working directory."""
import os
from pathlib import Path
import tempfile
import unittest

from panda3d.core import (Filename, Loader, LoaderOptions, NodePath,
                         VirtualFileSystem, get_model_path, loadPrcFileData, unloadPrcFile)
from toontown.mobile.Client import configure_embedded_paths, BundledModelPathError


class EmbeddedAssetTests(unittest.TestCase):
    def setUp(self):
        self.old_os = Path.cwd()
        self.vfs = VirtualFileSystem.get_global_ptr()
        self.old_vfs = self.vfs.get_cwd()
        self.paths = get_model_path()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, self.old_os)
        self.addCleanup(self.vfs.chdir, self.old_vfs)
        self.root = Path(self.temp.name) / 'App With Spaces' / 'Game'
        self.models = self.root / 'resources/phase_3/models/gui'
        self.models.mkdir(parents=True)
        (self.root / 'engine-models').mkdir()
        for model in ('loading-background', 'progress-background', 'toon_council'):
            NodePath(model).write_bam_file(Filename.from_os_specific(str(self.models / (model + '.bam'))))
        self.page = loadPrcFileData('embedded-assets-test', 'model-path resources\ndefault-model-extension .bam')
        self.addCleanup(unloadPrcFile, self.page)
        self.vfs.chdir(Filename.from_os_specific(self.temp.name))
        os.chdir(self.root)
        self.loader = Loader('embedded-assets-test')
        self.options = LoaderOptions()
        self.options.set_flags(LoaderOptions.LF_search | LoaderOptions.LF_no_cache)

    def tearDown(self):
        self.paths.clear()

    def test_os_chdir_alone_fails_then_embedded_paths_load_models(self):
        model = Filename('phase_3/models/gui/progress-background')
        self.assertIsNone(self.loader.load_sync(model, self.options))
        configure_embedded_paths(self.root)
        for name in ('loading-background', 'progress-background', 'toon_council'):
            self.assertIsNotNone(self.loader.load_sync(Filename('phase_3/models/gui/' + name), self.options))
        self.assertEqual(self.vfs.get_cwd(), Filename.from_os_specific(str(self.root)))
        count = self.paths.get_num_directories()
        configure_embedded_paths(self.root)
        self.assertEqual(count, self.paths.get_num_directories())
        os.chdir(self.temp.name)
        self.assertIsNotNone(self.loader.load_sync(model, self.options))

    def test_missing_startup_asset_is_detected_before_launcher(self):
        (self.models / 'progress-background.bam').unlink()
        with self.assertRaises(BundledModelPathError):
            configure_embedded_paths(self.root)


if __name__ == '__main__':
    unittest.main()
