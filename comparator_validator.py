from argparse import ArgumentParser, ArgumentTypeError
import os
import pandas as pd

def print_err(err_msg,details=()):

    print('ERR:',err_msg)

    for d in details:
        print('----',d)

def compareGisAttributes(cPath,nPath):
    ...

def compareCsvs(cPath,nPath):

    canonical_df = pd.read_csv(cPath)
    new_df = pd.read_csv(nPath)

    mismatch = False
    # check row count
    if len(canonical_df) != len(new_df):
        print_err('Record counts do not match',[
            f'Canonical record count: {len(canonical_df)}',
            f'New record count: {len(new_df)}'
        ])
        mismatch = True
    else:
        print(f'Record counts match both sources have {new_df.nrows()} records')

    # Check headers
    c_headers = set(canonical_df.columns)
    n_headers = set(new_df.columns)

    if c_headers != n_headers:
        print_err('Columns do not match',[
            f'Missing headers: {", ".join(c_headers.difference(n_headers))}',
            f'Extra headers: {", ".join(n_headers.difference(c_headers))}',
        ])
        mismatch = False
    else:
        print('All fields accounted for')

    if mismatch:
        print('Stopping analysis here due to previous mismatches')
        return
    else:
        print('...')


#######################################################
VALID_EXTS = ('.csv','.gdb','.sqlite','.sql')

def validateExtension(path):

    if os.path.splitext(path)[1].lower() not in VALID_EXTS:
        raise ArgumentTypeError("file must be one of the following: "+', '.join(VALID_EXTS))
    return path

if __name__ == '__main__':

    prsr = ArgumentParser(description="Tool for validating new results against canonical copy")

    prsr.add_argument('canonical',type=validateExtension,help="The source collection, assumed to be correct")
    prsr.add_argument('novel',type=validateExtension,help='the results to audit')

    args=prsr.parse_args()

    conExt = os.path.splitext(args.canonical)[1].lower()
    newExt = os.path.splitext(args.novel)[1].lower()

    if conExt=='.csv' and newExt=='.csv':
        print('Comparing tabular data')
        compareCsvs(args.canonical,args.novel)
    else:
        print('Comparing attributes of spatial records')
        compareGisAttributes(args.canonical,args.novel)

    print('Analysis complete')