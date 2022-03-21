import argparse
import importlib
from io import BytesIO
import logging
import sys

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

import BaseConstants

def parseELF(fname, **kwargs):
    f = ELFFile(open(fname, 'rb'))
    sections = list(f.iter_sections())
    tables = [ s for s in sections if isinstance(s, SymbolTableSection) ]
    symbols = { sym.name: sym.entry for table in tables for sym in table.iter_symbols() }

    blobs, offsets = [], []
    for s in BaseConstants.kAppAOTSymbols:
        s = symbols[s]
        section = next(S for S in sections if 0 <= s.st_value - S['sh_addr'] < S.data_size)
        blob = section.data()[(s.st_value - section['sh_addr']):][:s.st_size]
        assert len(blob) == s.st_size
        blobs.append(blob), offsets.append(s.st_value)

    loadLibraries(blobs[0])

    vm = Snapshot(blobs[0], offsets[0], blobs[1], offsets[1])
    isolate = Snapshot(blobs[2], offsets[2], blobs[3], offsets[3], vm)

    return isolate

def loadLibraries(blob):
    stream = BytesIO(blob)
    stream.seek(20)
    version = stream.read(32).decode('UTF-8')
    
    SUPPORTED_SNAPSHOT = {
        "v2_10": "8ee4ef7a67df9845fba331734198a953",
        "v2_12": "5b97292b25f0a715613b7a28e0734f77"
    }

    WIP_SNAPSHOT = {
        "v2_13": "e4a09dbf2bb120fe4674e0576617a0dc"
    }

    for key,value in SUPPORTED_SNAPSHOT.items():
        if version in key:
            snapshotModule = importlib.import_module('{}.Snapshot'.format(key))
            resolverModule = importlib.import_module('{}.Resolver'.format(key))
            classIdModule = importlib.import_module('{}.ClassId'.format(key))
            
    for key,value in WIP_SNAPSHOT.items():
        raise Exception('Still Work in Progress for Dart SDK ' + key)
    
    if version not in SUPPORTED_SNAPSHOT.values() and version not in WIP_SNAPSHOT.values():
        raise Exception('Unsupported Dart SDK Version: ' + version)
    
    global Snapshot
    Snapshot = getattr(snapshotModule, 'Snapshot')
    global DartClass
    DartClass = getattr(resolverModule, 'DartClass')

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
parser.add_argument('-v', '--verbose', action='store_true', help='verbose')

args = parser.parse_args()
if args.verbose:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
isolate = parseELF(args.file)
dump(isolate, args.output)