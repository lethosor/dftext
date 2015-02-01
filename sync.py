#! /usr/bin/env python
import argparse, os, sys
import dftext

verbose = True
parser = dftext.Parser()
files = []

class SyncError(Exception): pass

def output_wrapper(f):
    def inner(text):
        f.write(text)
        f.flush()
    return inner

pout = output_wrapper(sys.stdout)
perr = output_wrapper(sys.stderr)

def init():
    for f in os.listdir('.'):
        # Avoid decompressed files
        if f.endswith('.txt'):
            continue
        try:
            parser.decode_file(f)
            sync(f)
        except dftext.ParserError:
            pass
        except SyncError as e:
            if verbose:
                pout('\n')
            perr('File %s: Sync failed: %s\n' % (f, e))

def sync(path):
    if path.endswith('.txt'):
        path = path.rstrip('.txt')
    txt_path = path + '.txt'
    if not os.path.isfile(path):
        raise SyncError('Compressed file not found')
    if os.path.exists(txt_path) and not os.path.isfile(txt_path):
        raise SyncError('Decompressed file (%s) is not a file' % txt_path)
    # Determine whether the compressed or decompressed file is more up-to-date
    compressed_newer = (os.path.getmtime(path) >
            (os.path.getmtime(txt_path) if os.path.exists(txt_path) else -1))
    if verbose:
        pout('%s file %s... ' % ('Decompressing' if compressed_newer else 'Compressing',
                path if compressed_newer else txt_path))
    if compressed_newer:
        old_size = os.stat(path).st_size
    else:
        old_size = os.stat(txt_path).st_size
    pout('Done [%i -> ? bytes]\n' % (old_size))

if __name__ == '__main__':
    init()
