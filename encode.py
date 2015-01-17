#! /usr/bin/env python
import sys
import dftext
args = dftext.ArgParser().parse_args()
try:
    sys.stdout.write(dftext.Parser().encode_file(args.filename, index=args.index, level=args.level))
except Exception as e:
    if args.debug:
        raise
    sys.stderr.write(str(e) + '\n')
