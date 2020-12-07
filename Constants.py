kMagicOffset = 0
kMagicSize = 4
kLengthOffset = kMagicOffset + kMagicSize
kLengthSize = 8
kKindOffset = kLengthOffset + kLengthSize
kKindSize = 8
kHeaderSize = kKindOffset + kKindSize
hashSize = 32

kMaxObjectAlignment = 16

kObjectAlignment = 16
kObjectAlignmentLog2 = 4
kWordSizeLog2 = 3
kWordSize = 8

kTypedDataCidRemainderInternal = 0
kTypedDataCidRemainderView = 1
kTypedDataCidRemainderExternal = 2

kCachedDescriptorCount = 32
kCachedICDataArrayCount = 4
kNumStubEntries = 97

kTopLevelCidOffset = 65536

kMonomorphicEntryOffsetAOT = 0
kPolymorphicEntryOffsetAOT = 0

kNativeEntryData = 4
kTaggedObject = 0
kImmediate = 1
kNativeFunction = 2

kNullabilityBitSize = 2
kNullabilityBitMask = 3

kAppAOTSymbols = [
    '_kDartVmSnapshotData',
    '_kDartVmSnapshotInstructions',
    '_kDartIsolateSnapshotData',
    '_kDartIsolateSnapshotInstructions'
]