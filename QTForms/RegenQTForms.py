#!/usr/bin/python

'''Regenerate UI components from Qt UI forms.'''

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import glob
from datetime import datetime
from distutils.dir_util import copy_tree

if __name__ == "__main__":
    pyuic = 'pyuic5'

    # ensure that we are in the script directory
    trgDir = os.path.dirname(__file__)
    if len(trgDir) == 0:
        trgDir = "./"
    os.chdir(trgDir)
    vals = []
    dest = "../ree_pe_score/ui_qt/_autoforms/"
    for p in glob.iglob('*.ui'):
        modName = "ui_" + os.path.splitext(p)[0].lower()
        target = dest + modName + ".py"
        vals.append("'" + modName + "'")
        print(p + "-->" + target)
        os.system(pyuic + " -o " + target + " " + p)

    # print("Copying resources to components.ui package")
    # copy_tree('./resources','../resources')

    with open(dest + '__init__.py', 'w') as initFile:
        print('Updating "__init__.py"')
        initFile.write('# autogenerated for REE PE Score on ' + str(datetime.now()) + '\n\n')
        initFile.write('"""Auto-generated files created by the QT tools suite. Do not edit directly."""\n\n')
        initFile.write('__all__ = [' + ',\n           '.join(vals) + ']\n')

    print("Done.")
