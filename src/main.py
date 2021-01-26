import argparse
import sys

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

import Constants
from Snapshot import Snapshot

from Resolver import DartClass
from ClassId import *

def parseELF(fname, **kwargs):
    f = ELFFile(open(fname, 'rb'))
    sections = list(f.iter_sections())
    tables = [ s for s in sections if isinstance(s, SymbolTableSection) ]
    symbols = { sym.name: sym.entry for table in tables for sym in table.iter_symbols() }

    blobs, offsets = [], []
    for s in Constants.kAppAOTSymbols:
        s = symbols[s]
        section = next(S for S in sections if 0 <= s.st_value - S['sh_addr'] < S.data_size)
        blob = section.data()[(s.st_value - section['sh_addr']):][:s.st_size]
        assert len(blob) == s.st_size
        blobs.append(blob), offsets.append(s.st_value)

    vm = Snapshot(blobs[0], offsets[0], blobs[1], offsets[1])
    isolate = Snapshot(blobs[2], offsets[2], blobs[3], offsets[3], vm)

    return isolate

def dump(snapshot, output):
    f = open(output, 'w')
    f.write('  ___      _    _                   \n')
    f.write(' |   \\ ___| |__| |_ _ _  _ _ __  ___\n')
    f.write(' | |) / _ \\ / _` | \'_| || | \'  \\(_-<\n')
    f.write(' |___/\\___/_\\__,_|_|  \\_,_|_|_|_/__/\n')
    f.write('-------------------------------------\n\n')
    f.write('# SUMMARY\n\n')
    f.write(snapshot.getSummary())
    f.write('\n\n# CLASSES\n\n')
    for clazz in snapshot.classes.values():
        dartClass = DartClass(snapshot, clazz)
        f.write(str(dartClass))
        f.write('\n\n')
    f.close()

parser = argparse.ArgumentParser(description='Parse the libapp.so file in Flutter apps for Android.')
parser.add_argument('file', help='target Flutter binary')
parser.add_argument('output', help='output file')

args = parser.parse_args()
isolate = parseELF(args.file)
dump(isolate, args.output)