#! /usr/bin/env python
import argparse, os, sys, time
import dftext

verbose = True
parser = dftext.Parser()
files = []
mtimes = {}

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
        if not os.path.isfile(f):
            continue
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
        else:
            files.append(f)
            mtimes[f] = os.path.getmtime(f)
            mtimes[f + '.txt'] = os.path.getmtime(f + '.txt')

def sync(path):
    if path.endswith('.txt'):
        path = path[:-4]
    txt_path = path + '.txt'
    if not os.path.isfile(path):
        raise SyncError('Compressed file (%s) not found' % path)
    if os.path.exists(txt_path) and not os.path.isfile(txt_path):
        raise SyncError('Decompressed file (%s) is not a file' % txt_path)
    # Determine whether the compressed or decompressed file is more up-to-date
    compressed_newer = (os.path.getmtime(path) >=
            (os.path.getmtime(txt_path) if os.path.exists(txt_path) else -1))
    if verbose:
        pout('%s file %s... ' % ('Decompressing' if compressed_newer else 'Compressing',
                path if compressed_newer else txt_path))
    if compressed_newer:
        old_size = os.stat(path).st_size
        try:
            with open(txt_path, 'w') as f:
                f.write(parser.decode_file(path))
        except dftext.ParserError as e:
            raise SyncError('Could not decode file: %s' % e)
        new_size = os.stat(txt_path).st_size
        # Update compressed file timestamp
        with open(path, 'a'):
            os.utime(path, None)
    else:
        old_size = os.stat(txt_path).st_size
        try:
            with open(path, 'wb') as f:
                f.write(parser.encode_file(txt_path))
        except dftext.ParserError as e:
            raise SyncError('Could not encode file: %s' % e)
        new_size = os.stat(path).st_size
    mtimes[path] = os.path.getmtime(path)
    mtimes[txt_path] = os.path.getmtime(txt_path)
    pout('Done [%i -> %i bytes]\n' % (old_size, new_size))

def sync_changed():
    for f in mtimes:
        if mtimes[f] != os.path.getmtime(f):
            sync(f)

if __name__ == '__main__':
    init()
    try:
        while True:
            time.sleep(0.5)
            sync_changed()
    except KeyboardInterrupt:
        print('')
