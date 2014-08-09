""" DF compressed text file manipulation """

import argparse, struct, sys, zlib
class ArgParser:
    def __init__(self):
        self.arg_parser = argparse.ArgumentParser()
        self.arg_parser.add_argument('filename',
            help='Filename to read from (defaults to stdin)',
            nargs='?',
            default=None,
        )
        self.arg_parser.add_argument('--index',
            help='Use data/index-style encryption',
            action='store_true',
        )
    def parse_args(self):
        return self.arg_parser.parse_args()

class ParserError(Exception): pass
class ParserDecodeError(Exception): pass

class Parser:
    def decode(self, in_file, index=False):
        if in_file is None:
            in_file = sys.stdin
        elif isinstance(in_file, str):
            in_file = open(in_file)
        in_text = in_file.read()
        decompressed = ''
        chunk_id = 1
        while in_text:
            try:
                chunk_length = struct.unpack('<L', in_text[:4])[0]
            except struct.error:
                raise ParserDecodeError('Could not determine chunk length')
            end = chunk_length + 4
            try:
                decompressed += zlib.decompress(in_text[4:end])
            except zlib.error:
                raise ParserDecodeError('Could not decompress chunk %i' % chunk_id)
            in_text = in_text[end:]
            chunk_id += 1
        try:
            record_count, decompressed = \
                    struct.unpack('<L', decompressed[:4])[0], decompressed[4:]
        except struct.error:
            raise ParserDecodeError('Could not determine record count')
        records = []
        for record_id in range(record_count):
            record_length, record_length_2 = \
                    struct.unpack('<LH', decompressed[:6])
            decompressed = decompressed[6:]
            if record_length != record_length_2:
                raise ParserDecodeError('Record lengths do not match')
            record, decompressed = decompressed[:record_length], decompressed[record_length:]
            records.append(record)
        return '\n'.join(records) + '\n\n'
    
