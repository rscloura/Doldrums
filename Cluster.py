import Constants

from ClassId import ClassId
from Kind import Kind
from Utils import DecodeUtils, StreamUtils, isTopLevelCid

def getDeserializerForCid(cid):
	# Class ID: 4
	class ClassDeserializer():
		def readAlloc(self, snapshot):
			self.predefinedStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				classId = StreamUtils.readCid(snapshot.stream)
				snapshot.assignRef('class')
			self.predefinedStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('instance size')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.predefinedStartIndex, self.predefinedStopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				# The two next fields are skipped IsInternalVMdefinedClassId fails
				# for the current class ID. Assigning them should be irrelevant.
				classPtr['hostInstanceSizeInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostNextFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostTypeArgumentsFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)

				if not snapshot.isPrecompiled:
					classPtr['targetInstanceSizeInWords'] = classPtr['hostInstanceSizeInWords']
					classPtr['targetNextFieldOffsetInWords'] = classPtr['hostNextFieldOffsetInWords']
					classPtr['targetTypeArgumentsFieldOffsetInWords'] = classPtr['hostTypeArgumentsFieldOffsetInWords']

				classPtr['numTypeArguments'] = StreamUtils.readInt(snapshot.stream, 16)
				classPtr['numNativeFields'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				classPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['stateBits'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if snapshot.isPrecompiled:
					StreamUtils.readUnsigned(snapshot.stream, 64)

				snapshot.references[refId] = classPtr

			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)
				classPtr['hostInstanceSizeInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostNextFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostTypeArgumentsFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)

				if not snapshot.isPrecompiled:
					classPtr['targetInstanceSizeInWords'] = classPtr['hostInstanceSizeInWords']
					classPtr['targetNextFieldOffsetInWords'] = classPtr['hostNextFieldOffsetInWords']
					classPtr['targetTypeArgumentsFieldOffsetInWords'] = classPtr['hostTypeArgumentsFieldOffsetInWords']

				classPtr['numTypeArguments'] = StreamUtils.readInt(snapshot.stream, 16)
				classPtr['numNativeFields'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				classPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['stateBits'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if snapshot.isPrecompiled and not isTopLevelCid(classId):
					StreamUtils.readUnsigned(snapshot.stream, 64)

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { }
			classPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['userName'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['functions'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['functionsHashTable'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['fields'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['offsetInWordsToField'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['interfaces'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['library'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['superType'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['signatureFunction'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['constants'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['declarationType'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['invocationDispatcherCache'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['allocationStub'] = StreamUtils.readUnsigned(snapshot.stream)
			if not (snapshot.kind is Kind.FULL_AOT):
				classPtr['directImplementors'] = StreamUtils.readUnsigned(snapshot.stream)
				if not (snapshot.kind is Kind.FULL):
					classPtr['directSubclasses'] = StreamUtils.readUnsigned(snapshot.stream)
					if not (snapshot.kind is Kind.FULL_JIT):
						classPtr['dependentCode'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 5
	class PatchClassDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('patch class')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['libraryKernelOffset'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { }
			classPtr['patchedClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['originClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			if not snapshot.kind is Kind.FULL_AOT:
				classPtr['libraryKernelData'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 6
	class FunctionDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('function')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				funcPtr = self._readFromTo(snapshot)
				if (snapshot.kind is Kind.FULL):
					#TODO
					raise Exception('Not implemented')
				elif (snapshot.kind is Kind.FULL_AOT):
					funcPtr['code'] = StreamUtils.readRef(snapshot.stream)
				else:
					#TODO
					raise Exception('Not implemented')

				#TODO: if debug

				if not snapshot.isPrecompiled:
					if not snapshot.kind is Kind.FULL_AOT:
						funcPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
						funcPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
						funcPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)
					#TODO: reset

				funcPtr['packedFields'] = StreamUtils.readUnsigned(snapshot.stream, 32)
				funcPtr['kindTag'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if (not snapshot.kind is Kind.FULL_AOT) and (not snapshot.isPrecompiled):
					funcPtr['usageCounter'] = 0
					funcPtr['optimizedInstructionCount'] = 0
					funcPtr['optimizedCallSiteCount'] = 0
					funcPtr['deoptimizationCounter'] = 0
					funcPtr['stateBits'] = 0
					funcPtr['inliningDepth'] = 0

				snapshot.references[refId] = funcPtr

		def _readFromTo(self, snapshot):
			funcPtr = { }
			funcPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['resultType'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterTypes'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterNames'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

			return funcPtr

	# Class ID: 7
	class ClosureDataDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('closure data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				closureDataPtr = { }

				if (snapshot.kind is Kind.FULL_AOT):
					closureDataPtr['contextScope'] = None
				else:
					closureDataPtr['contextScope'] = StreamUtils.readRef(snapshot.stream)

				closureDataPtr['parentFunction'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['signatureType'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['closure'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = closureDataPtr

	# Class ID: 8
	class SignatureDataDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('signature data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				dataPtr = self._readFromTo(snapshot)

				snapshot.references[refId] = dataPtr

		def _readFromTo(self, snapshot):
			dataPtr = { }
			dataPtr['parentFunction'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['signatureType'] = StreamUtils.readUnsigned(snapshot.stream)

			return dataPtr

	# Class ID: 11
	class FieldDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('field')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				fieldPtr = self._readFromTo(snapshot)

				if snapshot.kind is not Kind.FULL_AOT:
					if not snapshot.isPrecompiled:
						fieldPtr['savedInitialValue'] = StreamUtils.readRef(snapshot.stream)
					fieldPtr['guardedListLength'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is Kind.FULL_JIT:
					fieldPtr['dependentCode'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is not Kind.FULL_AOT:
					fieldPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['guardedCid'] = StreamUtils.readCid(snapshot.stream)
					fieldPtr['isNullable'] = StreamUtils.readCid(snapshot.stream)
					fieldPtr['staticTypeExactnessState'] = StreamUtils.readInt(snapshot.stream, 8)
					if not snapshot.isPrecompiled:
						fieldPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				fieldPtr['kindBits'] = StreamUtils.readUnsigned(snapshot.stream, 16)

				valueOrOffset = StreamUtils.readRef(snapshot.stream)
				if DecodeUtils.decodeStaticBit(fieldPtr['kindBits']):
					fieldId = StreamUtils.readUnsigned(snapshot.stream)
					fieldPtr['hostOffsetOrFieldId'] = ('Smi', fieldId)
				else:
					fieldPtr['hostOffsetOrFieldId'] = ('Smi', valueOrOffset)
					if not snapshot.isPrecompiled:
						fieldPtr['targetOffset'] = ('Smi', fieldPtr['hostOffsetOrFieldId'])

				snapshot.references[refId] = fieldPtr

		def _readFromTo(self, snapshot):
			fieldPtr = { }
			fieldPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['type'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['initializerFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return fieldPtr

	# Class ID: 12
	class ScriptDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('script')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				scriptPtr = self._readFromTo(snapshot)

				scriptPtr['lineOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['colOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['flags'] = StreamUtils.readUnsigned(snapshot.stream, 8)
				scriptPtr['kernelScriptIndex'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['loadTimestamp'] = 0

				snapshot.references[refId] = scriptPtr

		def _readFromTo(self, snapshot):
			scriptPtr = { }
			scriptPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)

			if snapshot.kind is Kind.FULL or snapshot.kind is Kind.FULL_JIT:
				scriptPtr['resolvedUrl'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['compileTimeConstants'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['lineStarts'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['debugPositions'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['kernelProgramInfo'] = StreamUtils.readUnsigned(snapshot.stream)

			return scriptPtr

	# Class ID: 13
	class LibraryDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('library')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				libraryPtr = self._readFromTo(snapshot)
				libraryPtr['nativeEntryResolver'] = None
				libraryPtr['nativeEntrySymbolResolver'] = None
				libraryPtr['index'] = StreamUtils.readInt(snapshot.stream, 32)
				libraryPtr['numImports'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				libraryPtr['loadState'] = StreamUtils.readInt(snapshot.stream, 8)

				#TODO: missing update
				libraryPtr['flags'] = StreamUtils.readUnsigned(snapshot.stream, 8)

				if (not snapshot.isPrecompiled) and (snapshot.kind is not Kind.FULL_AOT):
					libraryPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				snapshot.references[refId] = libraryPtr

		def _readFromTo(self, snapshot):
			libraryPtr = { }
			libraryPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['privateKey'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['dictionary'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['metadata'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['toplevelClass'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['usedScripts'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['loadingUnit'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['imports'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['exports'] = StreamUtils.readUnsigned(snapshot.stream)
			if (snapshot.kind is Kind.FULL) or (snapshot.kind is Kind.FULL_JIT):
				libraryPtr['dependencies'] = StreamUtils.readUnsigned(snapshot.stream)
				libraryPtr['kernelData'] = StreamUtils.readUnsigned(snapshot.stream)

			return libraryPtr

	# Class ID: 16
	class CodeDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('code')
			self.stopIndex = self.deferredStartIndex = snapshot.nextRefIndex
			deferredCount = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(deferredCount):
				snapshot.assignRef('code')
			self.deferredStopIndex = snapshot.nextRefIndex

	# Class ID: 20
	class ObjectPoolDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('library')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 21
	class PcDescriptorsDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('library')
			self.stopIndex = snapshot.nextRefIndex

	# Aggregate deserializer for class IDs: 22, 23, 81, 82
	class RODataDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			runningOffset = 0
			for _ in range(count):
				runningOffset += StreamUtils.readUnsigned(snapshot.stream) << Constants.kObjectAlignmentLog2
				snapshot.assignRef('ro data object')

		def readFill(self, snapshot):
			return

	# Class ID: 25
	class ExceptionHandlersDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('exception')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 30
	class UnlinkedCallDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('unlinked call')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 34
	class MegamorphicCacheDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('megamorphic cache')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 35
	class SubtypeTestCacheDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('subtype test cache')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 35
	class LoadingUnitDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('loading unit')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 42
	class InstanceDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			self.nextFieldOffsetInWords = StreamUtils.readInt(snapshot.stream)
			self.instanceSizeInWords = StreamUtils.readInt(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('instance')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 44
	class TypeArgumentsDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('type args')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 46
	class TypeDeserializer():
		def readAlloc(self, snapshot):
			self.canonicalStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type (canonical)')
			self.canonicalStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 47
	class TypeRefDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type refs')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 48
	class TypeParameterDeserializer():
		def readAlloc(self, snapshot):
			self.canonicalStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type parameter (canonical)')
			self.canonicalStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type parameter')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 49
	class ClosureDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('closure')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 53
	class MintDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for i in range(count):
				StreamUtils.readBool(snapshot.stream)
				StreamUtils.readInt(snapshot.stream, 64)
				snapshot.assignRef('smi or uninitialized')

		def readFill(self, snapshot):
			return

	# Class ID: 54
	class DoubleDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('double')
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 56
	class GrowableObjectArrayDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('growable object array')
			self.stopIndex = snapshot.nextRefIndex

	# Aggregate deserializer for class IDs: 78, 79
	class ArrayDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('array')

	class OneByteStringDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('one byte string')

	class TwoByteStringDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('two-byte string')
			self.stopIndex = snapshot.nextRefIndex

	class TypedDataDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('typed data')
			self.stopIndex = snapshot.nextRefIndex

	if cid > ClassId.NUM_PREDEFINED.value:
		return InstanceDeserializer()
	elif ClassId(cid) is ClassId.ILLEGAL:
		raise Exception('Encountered illegal cluster')
	elif ClassId.isTypedDataClass(cid):
		return TypedDataDeserializer()
	elif ClassId(cid) is ClassId.CLASS:
		return ClassDeserializer()
	elif ClassId(cid) is ClassId.PATCH_CLASS:
		return PatchClassDeserializer()
	elif ClassId(cid) is ClassId.FUNCTION:
		return FunctionDeserializer()
	elif ClassId(cid) is ClassId.CLOSURE_DATA:
		return ClosureDataDeserializer()
	elif ClassId(cid) is ClassId.SIGNATURE_DATA:
		return SignatureDataDeserializer()
	elif ClassId(cid) is ClassId.FIELD:
		return FieldDeserializer()
	elif ClassId(cid) is ClassId.SCRIPT:
		return ScriptDeserializer()
	elif ClassId(cid) is ClassId.LIBRARY:
		return LibraryDeserializer()
	elif ClassId(cid) is ClassId.CODE:
		return CodeDeserializer()
	elif ClassId(cid) is ClassId.OBJECT_POOL:
		return ObjectPoolDeserializer()
	elif ClassId(cid) is ClassId.PC_DESCRIPTORS:
		return PcDescriptorsDeserializer()
	elif ClassId(cid) is ClassId.CODE_SOURCE_MAP:
		return RODataDeserializer()
	elif ClassId(cid) is ClassId.COMPRESSED_STACK_MAPS:
		return RODataDeserializer()
	elif ClassId(cid) is ClassId.EXCEPTION_HANDLERS:
		return ExceptionHandlersDeserializer()
	elif ClassId(cid) is ClassId.UNLINKED_CALL:
		return UnlinkedCallDeserializer()
	elif ClassId(cid) is ClassId.MEGAMORPHIC_CACHE:
		return MegamorphicCacheDeserializer()
	elif ClassId(cid) is ClassId.SUBTYPE_TEST_CACHE:
		return SubtypeTestCacheDeserializer()
	elif ClassId(cid) is ClassId.LOADING_UNIT:
		return LoadingUnitDeserializer()
	elif ClassId(cid) is ClassId.INSTANCE:
		return InstanceDeserializer()
	elif ClassId(cid) is ClassId.TYPE_ARGUMENTS:
		return TypeArgumentsDeserializer()
	elif ClassId(cid) is ClassId.TYPE:
		return TypeDeserializer()
	elif ClassId(cid) is ClassId.TYPE_REF:
		return TypeRefDeserializer()
	elif ClassId(cid) is ClassId.TYPE_PARAMETER:
		return TypeParameterDeserializer()
	elif ClassId(cid) is ClassId.CLOSURE:
		return ClosureDeserializer()
	elif ClassId(cid) is ClassId.MINT:
		return MintDeserializer()
	elif ClassId(cid) is ClassId.DOUBLE:
		return DoubleDeserializer()
	elif ClassId(cid) is ClassId.GROWABLE_OBJECT_ARRAY:
		return GrowableObjectArrayDeserializer()
	elif ClassId(cid) is ClassId.ARRAY:
		return ArrayDeserializer()
	elif ClassId(cid) is ClassId.IMMUTABLE_ARRAY:
		return ArrayDeserializer()
	elif ClassId(cid) is ClassId.ONE_BYTE_STRING:
		return OneByteStringDeserializer()
	elif ClassId(cid) is ClassId.TWO_BYTE_STRING:
		return TwoByteStringDeserializer()
	else:
		raise Exception('Deserializer missing for class {}'.format(ClassId(cid).name))