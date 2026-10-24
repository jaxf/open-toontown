"""Exercise loader lifetime before main, with a deliberately unready engine."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from ios.prepare_engine import defer_dna_loader


SOURCE = r'''
#include <cstdlib>
static bool engine_ready = false;
static int constructions = 0;
struct Loader {
  Loader() {
    if (!engine_ready) std::_Exit(23);
    ++constructions;
  }
  int load_sync(int model, int flags = 0) { return model + flags; }
};
static Loader loader;
int normal_model() { return loader.load_sync(7); }
int hood_model() { return loader.load_sync(11, 2); }
int place_model() { return loader.load_sync(19, 4); }
int main() {
  if (constructions != 0) return 1;
  engine_ready = true;
  if (normal_model() != 7 || hood_model() != 13 || place_model() != 23) return 2;
  return constructions == 1 ? 0 : 3;
}
'''


class EngineStartupTests(unittest.TestCase):
    def test_parser_loader_is_deferred_and_reused_for_all_model_types(self):
        compiler = shutil.which('c++')
        self.assertIsNotNone(compiler, 'C++ compiler required for startup regression')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dna = root / 'panda/src/dna'
            dna.mkdir(parents=True)
            sources = [dna / name for name in ('dnaParser.yxx', 'dnaParser.cxx.prebuilt')]
            for path in sources:
                path.write_text(SOURCE)

            def execute(path):
                binary = root / 'startup-test'
                subprocess.run([compiler, '-std=c++11', '-x', 'c++', str(path),
                                '-o', str(binary)], check=True, capture_output=True)
                return subprocess.run([str(binary)], capture_output=True).returncode

            self.assertEqual(execute(sources[0]), 23, 'Original eager loader must reproduce failure')
            defer_dna_loader(root)
            first = [path.read_text() for path in sources]
            defer_dna_loader(root)
            self.assertEqual(first, [path.read_text() for path in sources])
            for path in sources:
                self.assertEqual(execute(path), 0, path.name)


if __name__ == '__main__':
    unittest.main()
