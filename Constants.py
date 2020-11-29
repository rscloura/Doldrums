kMagicOffset = 0
kMagicSize = 4
kLengthOffset = kMagicOffset + kMagicSize
kLengthSize = 8
kKindOffset = kLengthOffset + kLengthSize
kKindSize = 8
kHeaderSize = kKindOffset + kKindSize
hashSize = 32

kMaxObjectAlignment = 16

kObjectAlignmentLog2 = 4

kTypedDataCidRemainderInternal = 0

kCachedDescriptorCount = 32
kCachedICDataArrayCount = 4
kNumStubEntries = 97