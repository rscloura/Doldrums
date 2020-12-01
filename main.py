import sys

from Snapshot import Snapshot
 
print('rloura\'s Flutter disassembler')
print('------------------------------\n')

f = open(sys.argv[1], 'rb')
vm = Snapshot(f.read())
f.close()
print(vm.getSummary())