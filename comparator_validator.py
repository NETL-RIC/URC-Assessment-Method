from argparse import ArgumentParser, ArgumentTypeError
import os
import pandas as pd

colorEnabled=int(os.environ.get('REE_CV_USE_COLOR','1'))!=0

if colorEnabled:
    # https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal

    # NOTE: may have to check if we are on a classic DOS prompt.
    # if we are, we shoudl switch to DOS codes instead of VT-ANSI codes

    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
else:
    #disabled
    class bcolors:
        HEADER = ''
        OKBLUE = ''
        OKCYAN = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''
        BOLD = ''
        UNDERLINE = ''
        
def print_tagged(tag,msg,details=(),color=''):

    print(f'{color}{tag}:{bcolors.ENDC}',msg)

    for d in details:
        print(f'{bcolors.BOLD}----{bcolors.ENDC}',d)

def print_err(err_msg,details=()):
    print_tagged('ERR',err_msg,details,bcolors.FAIL)

def print_warn(warn_msg,details=()):
    print_tagged('WARN',warn_msg,details,bcolors.WARNING)

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
        print(f'Record counts match both sources have {len(new_df)} records')
        recCount = len(new_df)
    # Check headers
    c_headers = set(canonical_df.columns)
    n_headers = set(new_df.columns)

    if c_headers != n_headers:
        missing = c_headers.difference(n_headers)
        extra = n_headers.difference(c_headers)

        mismatch = len(missing)>0
        if mismatch:
            print_err('Columns do not match',[
                f'Missing headers: {", ".join(missing)}',
                f'Extra headers: {", ".join(extra)}',
            ])
        else:
            print_warn(f'Extra headers: {", ".join(extra)}')
    else:
        print('All fields accounted for')

    if mismatch:
        print('Stopping analysis here due to previous mismatches')
        return
    else:
        print('Checking individual Columns...')
        for c in c_headers:
            # brute force testing to verify block below
            # for i in range(len(canonical_df[c])):
            #     if canonical_df[c][i]!=new_df[c][i]:
            #         print(c,' mismatch in ',i)
                    
            # Generate a list of True/False for each index
            # if not all true, then report which indices had a mismatch
            hits = canonical_df[c]==new_df[c]
            if not all(hits):
                print(f'---- {c} mismatches')
                print('--------',[i for i in range(len(hits)) if hits[i]])
                mismatch=True
        if not mismatch:
            print(bcolors.BOLD+bcolors.OKGREEN+'All values in equivalent columns appear to be equal'+bcolors.ENDC)


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
        print(bcolors.BOLD+'Comparing tabular data'+bcolors.ENDC)
        compareCsvs(args.canonical,args.novel)
    else:
        print('Comparing attributes of spatial records')
        compareGisAttributes(args.canonical,args.novel)

    print(bcolors.OKCYAN+'Analysis complete'+bcolors.ENDC)
