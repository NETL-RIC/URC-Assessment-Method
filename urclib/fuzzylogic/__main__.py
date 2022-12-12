"""
Run misc Fuzzy Logic utilities from command line.
"""

import sys
from argparse import ArgumentParser
from io import StringIO


from .embedgen import generate_embeddable


def check_mode(mode):
    """ Check for correct mode value. Presently just checks for 'generate'.

    Args:
        mode (str): The mode dlg_label to evaluate.

    Returns:
        bool: `True` if `mode` is an acceptable dlg_label; `False` otherwise.
    """

    return len(sys.argv) > 1 and sys.argv[1] == mode


def get_args():
    """Process and retrieve command-line arguments.

    Returns:
        Namespace: found command-line arguments.
    """

    prsr = ArgumentParser(description='Fuzzy logic utilities')
    prsr.add_argument('util', type=str, choices=['generate'], help="Utility to run.")
    prsr.add_argument('-i', '--infile', type=str, required=check_mode('generate'), help='The input project file')
    prsr.add_argument('-o', '--outfile', type=str, default=None, help='The optional output file')
    prsr.add_argument('-f', '--flimport', type=str, default='fuzzylogic', help='The fuzzylogic import path to us')

    return prsr.parse_args()


# main
args = get_args()

if args.util == 'generate':

    if args.outfile is None:
        buff = StringIO()
    else:
        buff = open(args.outfile, 'w')

    generate_embeddable(buff, args.infile, args.flimport)
    if isinstance(buff, StringIO):
        print(buff.getvalue())
    buff.close()

print("Done.")
