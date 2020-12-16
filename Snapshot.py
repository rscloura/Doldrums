from io import BytesIO

import Cluster
import Constants

from ClassId import ClassId
from Kind import Kind
from Utils import *

class Snapshot:
	# snapshot = byte array of VM snapshot
	# magic = snapshot header (size: kHeaderSize)
	# size = snapshot's length in bytes (excluding the magic number)
	# kind = snapshot's kind (enum)
	# hash = version hash (32 byte string)
	# features = string array of features
 
	def __init__(self, data, dataOffset, instructions, instructionsOffset, base=None):
		# Initialize basic fields
		self.stream = BytesIO(data)
		self.classes = { } # A dictionary from an ID (see ClassDeserializer) to a deserialized class object
		self.references = ['INVALID'] # Reference count starts at 1
		self.nextRefIndex = 1
		self.unboxedFieldsMapAt = { }
		self.instructionsOffset = instructionsOffset

		self.parseHeader()
		self.fieldSetup() # Sets up deterministic information dependent on header entries
		# Add base objects or copy them over from the VM snapshot
		if base is not None:
			self.references = base.references
			self.nextRefIndex = base.nextRefIndex
		else:
			self.addBaseObjects()
		# Alloc stage
		self.clusters = [ self.readClusterAlloc() for _ in range(self.numClusters) ]
		# Fill stage
		for cluster in self.clusters:
			cluster.readFill(self)
		self.readRoots()

	def parseHeader(self):
		self.magic = int.from_bytes(self.stream.read(Constants.kMagicSize), 'little')
		self.size = int.from_bytes(self.stream.read(Constants.kLengthSize), 'little')
		self.kind = Kind(int.from_bytes(self.stream.read(Constants.kKindSize), 'little'))
		self.hash = self.stream.read(Constants.hashSize).decode('UTF-8')
		self.features = list(map(lambda x: x.decode('UTF-8'), StreamUtils.readString(self.stream).split(b'\x20')))
		self.numBaseObjects = StreamUtils.readUnsigned(self.stream)
		self.numObjects = StreamUtils.readUnsigned(self.stream)
		self.numClusters = StreamUtils.readUnsigned(self.stream)
		self.fieldTableLength = StreamUtils.readUnsigned(self.stream)

	def fieldSetup(self):
		self.isProduct = 'product' in self.features
		self.hasComments = False #FIXME
		self.isPrecompiled = self.kind == Kind.FULL_AOT and 'product' in self.features
		self.isDebug = 'debug' in self.features
		self.useBareInstructions = 'use_bare_instructions' in self.features
		self.includesCode = self.kind == Kind.FULL_JIT or self.kind == Kind.FULL_AOT
		self.instructionsImage = 0 #FIXME
		self.rodataOffset = NumericUtils.roundUp(self.size + Constants.kMagicSize, Constants.kMaxObjectAlignment)
		self.rodata = BytesIO(self.stream.getbuffer()[self.rodataOffset:])
		self.previousTextOffset = 0
		if 'x64-sysv' in self.features:
			self.arch = 'X64'
			Constants.kMonomorphicEntryOffsetAOT = 8
			Constants.kPolymorphicEntryOffsetAOT = 22
		elif 'arm64-sysv' in self.features:
			self.arch = 'ARM64'
			Constants.kMonomorphicEntryOffsetAOT = 8
			Constants.kPolymorphicEntryOffsetAOT = 20
		else:
			raise Exception('Unknown architecture')

	def addBaseObjects(self):
		#FIXME: review CIDs
		baseObjects = [
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'Null' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'Sentinel' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'TransitionSentinel' },
			{ 'cid': ClassId.ARRAY, 'isBase': True, 'name': 'EmptyArray', 'data': [] },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ZeroArray' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'DynamicType' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'VoidType' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'EmptyTypeArguments' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'True' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'False' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ExtractorParameterTypes' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ExtractorParameterNames' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'EmptyContextScope' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'EmptyDescriptors' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'EmptyVarDescriptors' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'EmptyExceptionHandlers' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ImplicitGetterBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ImplicitSetterBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ImplicitStaticGetterBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'MethodExtractorBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'InvokeClosureBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'InvokeFieldBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'NsmDispatcherBytecode' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'DynamicInvocationForwarderBytecode' },
			*({ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'CachedArgsDescriptors' } for _ in range(Constants.kCachedDescriptorCount)),
			*({ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'CachedICDataArrays' } for _ in range(Constants.kCachedICDataArrayCount)),
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'CachedArray' },
			*({ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'ClassStub' } for cid in range(ClassId.CLASS.value, ClassId.UNWIND_ERROR.value + 1) if (cid != ClassId.ERROR.value and cid != ClassId.CALL_SITE_DATA.value)),
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'Dynamic CID' },
			{ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'VoidCID' },
			*({ 'cid': ClassId.TYPE, 'isBase': True, 'name': 'StubCode' } for _ in range(Constants.kNumStubEntries) if not Snapshot.includesCode(self.kind))
		]
		for obj in baseObjects:
			self.assignRef(obj)

	#TODO
	def readRoots(self):
		self.symbolTable = StreamUtils.readRef(self.stream)
		if self.includesCode:
			self.stubs = [ StreamUtils.readRef(self.stream) for _ in range(Constants.kNumStubEntries) ]


	def assignRef(self, obj):
		self.references.append(obj)
		self.nextRefIndex += 1

	def readClusterAlloc(self):
		cid = StreamUtils.readCid(self.stream)
		deserializer = Cluster.getDeserializerForCid(self.includesCode, cid)
		deserializer.readAlloc(self)
		return deserializer

	# Getter of the snapshot's header
	def getMagic(self):
		return self.magic
 
	# Getter of the snapshot's size
	def getSize(self):
		return self.size
 
	# Getter of the snapshot's kind
	def getKind(self):
		return self.kind
 
	# Getter of the snapshot's version
	def getHash(self):
		return self.hash
 
	# Getter of the snapshot's features
	def getFeatures(self):
		return self.features
 
	# Getter of the snapshot's base objects count
	def getNumBaseObjects(self):
		return self.numBaseObjects
 
	# Getter of the snapshot's objects count
	def getNumObjects(self):
		return self.numObjects
 
	# Getter of the snapshot's clusters count
	def getNumClusters(self):
		return self.numClusters
 
	# Getter of the snapshot's clusters count
	def getFieldTableLength(self):
		return self.fieldTableLength
 
	# Getter of the snapshot's data image offset
	def getRODataOffset(self):
		return self.rodataOffset

	def includesCode(kind):
		return (kind is Kind.FULL_JIT) or (kind is Kind.FULL_AOT)
 
	# Pretty printable string of the snapshot's main characteristics
	def getSummary(self):
		prettyString = 'Magic: 0xf5f5dcdc' + '\n'
		prettyString += 'Snapshot size (including ' + str(Constants.kMagicSize) + 'B of magic): ' + str(self.size + Constants.kMagicSize) + 'B\n'
		prettyString += 'Kind: ' + str(self.getKind()) + '\n'
		prettyString += 'Version: ' + self.getHash() + ' (' + getVersionInfo(self.getHash()) + ')\n'
		prettyString += 'Features: ' + ', '.join(self.getFeatures()) + '\n'
		prettyString += 'Base objects count: ' + str(self.getNumBaseObjects()) + '\n'
		prettyString += 'Objects count: ' + str(self.getNumObjects()) + '\n'
		prettyString += 'Clusters count: ' + str(self.getNumClusters()) + '\n'
		prettyString += 'Field table length: ' + str(self.getFieldTableLength()) + '\n'
		prettyString += 'Data image offset: ' + str(self.getRODataOffset())
		return prettyString