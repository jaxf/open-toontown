"""Validate Acorn DNA with OpenLevelEditor, or load it with the custom engine.

python tools/validate_acorn_dna.py --editor /path/to/OpenLevelEditor
python tools/validate_acorn_dna.py --native
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--editor',type=Path)
    mode.add_argument('--native',action='store_true')
    args=parser.parse_args()
    if args.editor:
        editor=args.editor.resolve()
        if not (editor/'toontown/compiler/libpandadna').is_dir():
            parser.error('Expected the imgui branch of OpenLevelEditor')
        # Separate interpreter keeps the editor and game packages from colliding.
        program='''
import builtins, sys
from pathlib import Path
from toontown.compiler.libpandadna.dna.base.DNAStorage import DNAStorage
from toontown.compiler.libpandadna.dna.components.DNARoot import DNARoot
from toontown.compiler.libpandadna.dna.parser.tokens import *
from ply import lex
lex.lex(optimize=0)
builtins.DNAError=ValueError
for path in sorted(Path(sys.argv[1]).glob('*.dna')):
    root=DNARoot(dnaStore=DNAStorage())
    with path.open() as source:
        root.read(source)
    print('OpenLevelEditor parsed:',path.name)
'''
        subprocess.run([sys.executable,'-c',program,str(ROOT/'assets/acorn/dna')],
                       cwd=editor,check=True)
        return
    os.chdir(ROOT)
    sys.path.insert(0,str(ROOT))
    from panda3d.core import loadPrcFileData, NodePath
    loadPrcFileData('', 'window-type none\naudio-library-name null\n'
                        'model-path .\nmodel-path resources\ndefault-model-extension .bam')
    from panda3d.toontown import DNAStorage, loadDNAFile
    from direct.showbase.ShowBase import ShowBase
    from toontown.expansion.AcornDNA import STORAGE, LAYOUTS
    app=ShowBase()
    for zone,path in LAYOUTS.items():
        storage=DNAStorage()
        loadDNAFile(storage,STORAGE)
        scene=NodePath(loadDNAFile(storage,path))
        assert not scene.isEmpty(),path
        assert len(scene.findAllMatches('**/linktunnel*'))==2,path
        print('Native DNA loaded:',zone,path)
        scene.removeNode()
    app.destroy()


if __name__=='__main__':
    main()
