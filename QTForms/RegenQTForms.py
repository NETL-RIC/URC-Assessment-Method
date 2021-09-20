#!/usr/bin/python

'''Regenerate UI components from Qt UI forms.'''

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import glob
from datetime import datetime
from argparse import ArgumentParser
from shutil import copyfile
from tempfile import TemporaryDirectory

if __name__ == "__main__":
    prsr = ArgumentParser("Regenerate Qt base forms")
    prsr.add_argument('-u', '--uic', type=str, default='pyuic5', help='Path to executable for pyuic5')
    prsr.add_argument('-f', '--force', action='store_true', help='overwrite all autogenerated files')

    args = prsr.parse_args()

    # ensure that we are in the script directory
    trgDir = os.path.dirname(__file__)
    if len(trgDir) == 0:
        trgDir = "./"
    os.chdir(trgDir)

    autodirs = set()
    dest = "../ree_pe_score/ui_qt/"
    # set aside a temporary directory for saving.
    # this way we can compare results and avoid updating things that don't
    # need updating.
    with TemporaryDirectory() as td:

        for p in glob.iglob('**/*.ui', recursive=True):
            trgDir = os.path.join(dest, os.path.dirname(p), '_autoforms')

            modName = "ui_" + os.path.splitext(os.path.basename(p))[0].lower() + ".py"
            tmp_trg = os.path.join(td, modName)
            target = os.path.join(trgDir, modName)

            if not args.force:
                print('Evaluating ' + p + '...', end='')
            os.system(' '.join([args.uic, "-o", tmp_trg, p]))

            update = True
            if not args.force and os.path.exists(target):
                SKIP = 7
                # SKIP header comments which are roughly 7 lines
                with open(target, 'r') as oldFile:
                    oldText = oldFile.readlines()[SKIP:]
                with open(tmp_trg, 'r') as newFile:
                    newText = newFile.readlines()[SKIP:]
                update = oldText != newText

            if update:
                autodirs.add(os.path.abspath(trgDir))
                print(' ' + p + "-->" + target)
                copyfile(tmp_trg, target)
            else:
                print(' No update needed.')

    # print("Copying resources to components.ui package")
    # copy_tree('./resources','../resources')

    currDir = os.path.abspath(os.path.curdir)
    for d in autodirs:
        initPath = os.path.join(d, '__init__.py')

        with open(initPath, 'w') as initFile:
            print(f'Updating "{initPath}"')
            initFile.write('# autogenerated for OGA Tool on ' + str(datetime.now()) + '\n\n')
            initFile.write('"""Auto-generated files created by the QT tools suite. Do not edit directly."""\n\n')
            os.chdir(d)
            fileList = [f"'{os.path.splitext(u)[0]}'" for u in glob.iglob("ui_*.py")]
            initFile.write('__all__ = [' + ',\n           '.join(fileList) + ']\n')
            os.chdir(currDir)
    print("Done.")
