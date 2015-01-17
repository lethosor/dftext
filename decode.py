#! /usr/bin/env python
import sys
import dftext
args = dftext.ArgParser().parse_args()
try:
    sys.stdout.write(dftext.Parser().decode_file(args.filename, index=args.index))
except Exception as e:
    if args.debug:
        raise
    sys.stderr.write(str(e) + '\n')
