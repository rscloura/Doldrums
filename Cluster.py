import Constants

from ClassId import ClassId
from Kind import Kind
import TypedData
from UnboxedFieldBitmap import UnboxedFieldBitmap
from Utils import DecodeUtils, NumericUtils, StreamUtils, isTopLevelCid

def getDeserializerForCid(includesCode, cid):
	# Abstract deserializer for class IDs: 22, 23, 81, 82
	class RODataDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			runningOffset = 0
			for x in range(count):
				runningOffset += StreamUtils.readUnsigned(snapshot.stream) << Constants.kObjectAlignmentLog2
				snapshot.rodata.seek(runningOffset)
				snapshot.assignRef({ 'cid': self.cid, 'refId': snapshot.nextRefIndex,'data': self.getObjectAt(snapshot) })

		def readFill(self, snapshot):
			return

	# Base class for deserializers with simple counting alloc stages
	class CountDeserializer():
		def readAlloc(self, snapshot, stubName):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef(stubName)
			self.stopIndex = snapshot.nextRefIndex

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
				classPtr['refId'] = snapshot.nextRefIndex

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
				snapshot.classes[classId] = classPtr

			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId
				classPtr['refId'] = snapshot.nextRefIndex

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
					snapshot.unboxedFieldsMapAt[classId] = UnboxedFieldBitmap(StreamUtils.readUnsigned(snapshot.stream, 64))

				snapshot.references[refId] = classPtr
				snapshot.classes[classId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { 'cid': ClassId.CLASS }
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
	class PatchClassDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Patch class stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['libraryKernelOffset'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { 'cid': ClassId.PATCH_CLASS, 'refId': snapshot.nextRefIndex }
			classPtr['patchedClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['originClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			if not snapshot.kind is Kind.FULL_AOT:
				classPtr['libraryKernelData'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 6
	class FunctionDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Function stub')

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
			funcPtr = { 'cid': ClassId.FUNCTION, 'refId': snapshot.nextRefIndex }
			funcPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['resultType'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterTypes'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterNames'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

			return funcPtr

	# Class ID: 7
	class ClosureDataDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Closure data stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				closureDataPtr = { 'cid': ClassId.CLOSURE_DATA, 'refId': snapshot.nextRefIndex }

				if (snapshot.kind is Kind.FULL_AOT):
					closureDataPtr['contextScope'] = None
				else:
					closureDataPtr['contextScope'] = StreamUtils.readRef(snapshot.stream)

				closureDataPtr['parentFunction'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['signatureType'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['closure'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = closureDataPtr

	# Class ID: 8
	class SignatureDataDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Signature data stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				dataPtr = self._readFromTo(snapshot)

				snapshot.references[refId] = dataPtr

		def _readFromTo(self, snapshot):
			dataPtr = { 'cid': ClassId.SIGNATURE_DATA, 'refId': snapshot.nextRefIndex }
			dataPtr['parentFunction'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['signatureType'] = StreamUtils.readUnsigned(snapshot.stream)

			return dataPtr

	# Class ID: 10
	class FfiTrampolineDataDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'FFI trampoline data stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				dataPtr = self._readFromTo(snapshot)
				dataPtr['callbackId'] = StreamUtils.readUnsigned(snapshot.stream) if snapshot.kind is Kind.FULL_AOT else 0

				snapshot.references[refId] = dataPtr
			
		def _readFromTo(self, snapshot):
			dataPtr = { 'cid': ClassId.FFI_TRAMPOLINE_DATA, 'refId': snapshot.nextRefIndex }
			dataPtr['signatureType'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['CSignature'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['callbackTarget'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['callbackExceptionalReturn'] = StreamUtils.readUnsigned(snapshot.stream)

			return dataPtr


	# Class ID: 11
	class FieldDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Field stub')

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
			fieldPtr = { 'cid': ClassId.FIELD, 'refId': snapshot.nextRefIndex }
			fieldPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['type'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['initializerFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return fieldPtr

	# Class ID: 12
	class ScriptDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Script stub')

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
			scriptPtr = { 'cid': ClassId.SCRIPT, 'refId': snapshot.nextRefIndex }
			scriptPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)

			if snapshot.kind is Kind.FULL or snapshot.kind is Kind.FULL_JIT:
				scriptPtr['resolvedUrl'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['compileTimeConstants'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['lineStarts'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['debugPositions'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['kernelProgramInfo'] = StreamUtils.readUnsigned(snapshot.stream)

			return scriptPtr

	# Class ID: 13
	class LibraryDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Library stub')

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
			libraryPtr = { 'cid': ClassId.LIBRARY, 'refId': snapshot.nextRefIndex }
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

	# Class ID: 14
	class NamespaceDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Namespace stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				namespacePtr = { 'cid': ClassId.NAMESPACE, 'refId': snapshot.nextRefIndex }
				namespacePtr['library'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['showNames'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['hideNames'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['metadataField'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = namespacePtr

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

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				codePtr = self._readFill(snapshot, refId, False)
				snapshot.references[refId] = codePtr
			for refId in range(self.deferredStartIndex, self.deferredStopIndex):
				cdPtr = self._readFill(snapshot, refId, True)
				snapshot.references[refId] = codePtr

		def _readFill(self, snapshot, refId, deferred):
			codePtr = { 'cid': ClassId.CODE, 'refId': snapshot.nextRefIndex }
			self._readInstructions(snapshot, codePtr, deferred)

			if not (snapshot.kind is Kind.FULL_AOT and snapshot.useBareInstructions):
				codePtr['objectPool'] = StreamUtils.readRef(snapshot.stream)
			else:
				codePtr['objectPool'] = None
			codePtr['owner'] = StreamUtils.readRef(snapshot.stream)
			codePtr['exceptionHandlers'] = StreamUtils.readRef(snapshot.stream)
			codePtr['pcDescriptors'] = StreamUtils.readRef(snapshot.stream)
			codePtr['catchEntry'] = StreamUtils.readRef(snapshot.stream)
			codePtr['compressedStackMaps'] = StreamUtils.readRef(snapshot.stream)
			codePtr['inlinedIdToFunction'] = StreamUtils.readRef(snapshot.stream)
			codePtr['codeSourceMap'] = StreamUtils.readRef(snapshot.stream)

			if (not snapshot.isPrecompiled) and (snapshot.kind is Kind.FULL_JIT):
				codePtr['deoptInfoArray'] = StreamUtils.readRef(snapshot.stream)
				codePtr['staticCallsTargetTable'] = StreamUtils.readRef(snapshot.stream)

			if not snapshot.isProduct:
				codePtr['returnAddressMetadata'] = StreamUtils.readRef(snapshot.stream)
				codePtr['varDescriptors'] = None
				codePtr['comments'] = StreamUtils.readRef(snapshot.stream) if snapshot.hasComments else []
				codePtr['compileTimestamp'] = 0

			codePtr['stateBits'] = StreamUtils.readInt(snapshot.stream, 32)

			return codePtr

		def _readInstructions(self, snapshot, codePtr, deferred):
			if deferred:
				if snapshot.isPrecompiled and snapshot.useBareInstructions:
					codePtr['entryPoint'] = 'entryPoint'
					codePtr['uncheckedEntryPoint'] = 'entryPoint'
					codePtr['monomorphicEntryPoint'] = 'entryPoint'
					codePtr['monomorphicUncheckedEntryPoint'] = 'entryPoint'
					codePtr['instructionsLength'] = 0
					return
				codePtr['uncheckedOffset'] = 0
				#TODO: cahed entry points
				return

			if snapshot.isPrecompiled and snapshot.useBareInstructions:
				snapshot.previousTextOffset += StreamUtils.readUnsigned(snapshot.stream)
				payloadStart = snapshot.instructionsImage + snapshot.previousTextOffset
				payloadInfo = StreamUtils.readUnsigned(snapshot.stream)
				uncheckedOffset = payloadInfo >> 1
				hasMonomorphicEntrypoint = (payloadInfo & 1) == 1

				entryOffset = Constants.kPolymorphicEntryOffsetAOT if hasMonomorphicEntrypoint else 0
				monomorphicEntryOffset = Constants.kMonomorphicEntryOffsetAOT if hasMonomorphicEntrypoint else 0
				entryPoint = payloadStart + entryOffset
				monomorphicEntryPoint = payloadStart + monomorphicEntryOffset

				codePtr['entryPoint'] = entryPoint
				codePtr['uncheckedEntryPoint'] = entryPoint + uncheckedOffset
				codePtr['monomorphicEntryPoint'] = monomorphicEntryPoint
				codePtr['monomorphicUncheckedEntryPoint'] = monomorphicEntryPoint + uncheckedOffset

				return

			#TODO
			raise Exception('Raw instructions deserialization missing')

	# Class ID: 17
	class BytecodeDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Bytecode stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				bytecodePtr = { 'cid': ClassId.BYTECODE, 'refId': snapshot.nextRefIndex }
				bytecodePtr['instructions'] = 0
				bytecodePtr['instructionsSize'] = StreamUtils.readInt(snapshot.stream, 32)
				bytecodePtr['objectPool'] = StreamUtils.readUnsigned(snapshot.stream)
				bytecodePtr['function'] = StreamUtils.readUnsigned(snapshot.stream)
				bytecodePtr['closures'] = StreamUtils.readUnsigned(snapshot.stream)
				bytecodePtr['exceptionHandlers'] = StreamUtils.readUnsigned(snapshot.stream)
				bytecodePtr['pcDescriptors'] = StreamUtils.readUnsigned(snapshot.stream)
				bytecodePtr['instructionsBinaryOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				bytecodePtr['sourcePositionsBinaryOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				bytecodePtr['localVariablesBinaryOffset'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = bytecodePtr

	# Class ID: 20
	class ObjectPoolDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('object pool')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				poolPtr = { 'cid': ClassId.OBJECT_POOL, 'refId': snapshot.nextRefIndex }
				length = StreamUtils.readUnsigned(snapshot.stream)
				poolPtr['length'] = length
				poolPtr['entryBits'] = [ ]
				poolPtr['data'] = [ ]
				for j in range(length):
					entryBits = StreamUtils.readUnsigned(snapshot.stream, 8)
					poolPtr['entryBits'].append(entryBits)
					entry = { }
					decodedBits = DecodeUtils.decodeTypeBits(entryBits)
					if decodedBits == Constants.kNativeEntryData or decodedBits == Constants.kTaggedObject:
						entry['rawObj'] = StreamUtils.readRef(snapshot.stream)
					elif decodedBits == Constants.kImmediate:
						entry['rawValue'] = StreamUtils.readInt(snapshot.stream, 64)
					elif decodedBits == Constants.kNativeFunction:
						entry['rawValue'] = 'native call entry'
					else:
						raise Exception('No type associated to decoded type bits')
					poolPtr['data'].append(entry)

				snapshot.references[refId] = poolPtr

	if includesCode:
		# Class ID: 21
		class PcDescriptorsDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.PC_DESCRIPTORS

			def getObjectAt(self, stream):
				return 'pc descriptor'

		# Class ID: 22
		class CodeSourceMapDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.CODE_SOURCE_MAP

			def getObjectAt(self, stream):
				return 'code source map'

		# Class ID: 23
		class CompressedStackMapsDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.COMPRESSED_STACK_MAPS

			def getObjectAt(self, stream):
				return 'compressed stack maps'
	else:
		# Class ID: 21
		class PcDescriptorsDeserializer():
			def __init__(self):
				self.cid = ClassId.PC_DESCRIPTORS

			def readAlloc(self, snapshot):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('pc descriptors')
				self.stopIndex = snapshot.nextRefIndex

			def readFill(self, snapshot):
				for refId in range(self.startIndex, self.stopIndex):
					length = StreamUtils.readUnsigned(snapshot.stream)
					descPtr = { 'cid': ClassId.PC_DESCRIPTORS, 'refId': snapshot.nextRefIndex }
					descPtr['length'] = length
					descPtr['data'] = snapshot.stream.read(length)

					snapshot.references[refId] = descPtr

	# Class ID: 25
	class ExceptionHandlersDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('exception')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				handlersPtr = { 'cid': ClassId.EXCEPTION_HANDLERS, 'refId': snapshot.nextRefIndex }
				handlersPtr['numEntries'] = length
				handlersPtr['handledTypesData'] = StreamUtils.readRef(snapshot.stream)
				data = []
				for j in range(length):
					info = { }
					info['handlerPcOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)
					info['outerTryIndex'] = StreamUtils.readInt(snapshot.stream, 16)
					# Original code has read int8
					info['needsStacktrace'] = StreamUtils.readBool(snapshot.stream)
					info['hasCatchAll'] = StreamUtils.readBool(snapshot.stream)
					info['isGenerated'] = StreamUtils.readBool(snapshot.stream)
					data.append(info)
				handlersPtr['data'] = data

				snapshot.references[refId] = handlersPtr

	# Class ID: 30
	class UnlinkedCallDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Unlinked call stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				unlinkedPtr = self._readFromTo(snapshot)
				unlinkedPtr['canPatchToMonomorphic'] = StreamUtils.readBool(snapshot.stream)

				snapshot.references[refId] = unlinkedPtr

		def _readFromTo(self, snapshot):
			unlinkedPtr = { 'cid': ClassId.UNLINKED_CALL, 'refId': snapshot.nextRefIndex }
			unlinkedPtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			unlinkedPtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)

			return unlinkedPtr

	# Class ID: 34
	class MegamorphicCacheDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Megamorphic cache stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = self._readFromTo(snapshot)
				cachePtr['filledEntryCount'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = cachePtr

		def _readFromTo(self, snapshot):
			cachePtr = { 'cid': ClassId.MEGAMORPHIC_CACHE, 'refId': snapshot.nextRefIndex }
			cachePtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['buckets'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['mask'] = StreamUtils.readUnsigned(snapshot.stream)

			return cachePtr

	# Class ID: 35
	class SubtypeTestCacheDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Subtype test stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = { 'cid': ClassId.SUBTYPE_TEST_CACHE, 'refId': snapshot.nextRefIndex }
				cachePtr['cache'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = cachePtr

	# Class ID: 35
	class LoadingUnitDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Loading unit stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				unitPtr = { 'cid': ClassId.LOADING_UNIT, 'refId': snapshot.nextRefIndex }
				unitPtr['parent'] = StreamUtils.readRef(snapshot.stream)
				unitPtr['baseObjects'] = None
				unitPtr['id'] = StreamUtils.readInt(snapshot.stream, 32)
				unitPtr['loaded'] = False
				unitPtr['loadOutstanding'] = False

				snapshot.references[refId] = unitPtr

	# Class ID: 42
	class InstanceDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			self.nextFieldOffsetInWords = StreamUtils.readInt(snapshot.stream, 32)
			self.instanceSizeInWords = StreamUtils.readInt(snapshot.stream, 32)
			for _ in range(count):
				snapshot.assignRef('instance')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			nextFieldOffset = self.nextFieldOffsetInWords << Constants.kWordSizeLog2
			instanceSize = NumericUtils.roundUp(self.instanceSizeInWords * Constants.kWordSize, Constants.kObjectAlignment)
			for refId in range(self.startIndex, self.stopIndex):
				instancePtr = { 'cid': ClassId.INSTANCE, 'refId': snapshot.nextRefIndex }
				instancePtr['isCanonical'] = StreamUtils.readBool(snapshot.stream)
				instancePtr['data'] = []
				offset = 8
				while offset < nextFieldOffset:
					if snapshot.unboxedFieldsMapAt[cid].get(int(offset / Constants.kWordSize)):
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readWordWith32BitReads(snapshot.stream))
					else:
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readRef(snapshot.stream))
					offset += Constants.kWordSize
				if offset < instanceSize:
					#TODO: verify
					instancePtr['data'].append(None)
				
				snapshot.references[refId] = instancePtr

	# Class ID: 44
	class TypeArgumentsDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('type args')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				isCanonical = StreamUtils.readBool(snapshot.stream)
				typeArgsPtr = { 'cid': ClassId.TYPE_ARGUMENTS, 'refId': snapshot.nextRefIndex }
				typeArgsPtr['length'] = length
				typeArgsPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
				typeArgsPtr['nullability'] = StreamUtils.readUnsigned(snapshot.stream)
				typeArgsPtr['instantiations'] = StreamUtils.readRef(snapshot.stream)
				typeArgsPtr['types'] = []
				for j in range(length):
					typeArgsPtr['types'].append(StreamUtils.readRef(snapshot.stream))

				snapshot.references[refId] = typeArgsPtr

	# Class ID: 46
	class TypeDeserializer():
		def readAlloc(self, snapshot):
			self.canonicalStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('Canonical type stub')
			self.canonicalStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('Type stub')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.canonicalStartIndex, self.canonicalStopIndex):
				typePtr = self._readFromTo(snapshot)
				typePtr['isCanonical'] = True
				typePtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['typeState'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

			for refId in range(self.startIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot)
				typePtr['isCanonical'] = False
				typePtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['typeState'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot):
			typePtr = { 'cid': ClassId.TYPE, 'refId': snapshot.nextRefIndex, 'isBase': False }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['typeClassId'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['arguments'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['signature'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr

	# Class ID: 47
	class TypeRefDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Type ref stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				typePtr = { 'cid': ClassId.TYPE_REF, 'refId': snapshot.nextRefIndex }
				typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
				typePtr['type'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = typePtr

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

		def readFill(self, snapshot):
			# Canonicalization plays no role in parsing
			for refId in range(self.canonicalStartIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot)
				typePtr['parametrizedClassId'] = StreamUtils.readInt(snapshot.stream, 32)
				typePtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				typePtr['index'] = StreamUtils.readInt(snapshot.stream, 16)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['flags'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot):
			typePtr = { 'cid': ClassId.TYPE_PARAMETER, 'refId': snapshot.nextRefIndex, 'isBase': False }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['bound'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['parametrizedFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr


	# Class ID: 49
	class ClosureDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Closure stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				closurePtr = { 'cid': ClassId.CLOSURE, 'refId': snapshot.nextRefIndex }
				closurePtr['isCanonical'] = StreamUtils.readBool(snapshot.stream)
				closurePtr['instantiatorTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['functionTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['delayedTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['function'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['context'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = closurePtr

	# Class ID: 53
	class MintDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for i in range(count):
				isCanonical = StreamUtils.readBool(snapshot.stream)
				value = StreamUtils.readInt(snapshot.stream, 64)
				snapshot.assignRef({ 'cid': ClassId.MINT, 'isCanonical': isCanonical, 'value': value})

		def readFill(self, snapshot):
			return

	# Class ID: 54
	class DoubleDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Double stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				isCanonical = StreamUtils.readBool(snapshot.stream)
				value = StreamUtils.readInt(snapshot.stream, 64)
				snapshot.references[refId] = { 'cid': ClassId.DOUBLE, 'refId': snapshot.nextRefIndex, 'isCanonical': isCanonical,  'value': value }

	# Class ID: 56
	class GrowableObjectArrayDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Growable object array stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				listPtr = { 'cid': ClassId.GROWABLE_OBJECT_ARRAY, 'refId': snapshot.nextRefIndex }
				listPtr['isCanonical'] = StreamUtils.readBool(snapshot.stream)
				listPtr['typeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['length'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = listPtr

	# Class ID: 77
	class WeakSerializationReferenceDeserializer(CountDeserializer):
		def readAlloc(self, snapshot):
			super().readAlloc(snapshot, 'Weak deserialization reference stub')

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				refPtr = { 'cid': ClassId.WEAK_SERIALIZATION_REFERENCE, 'refId': snapshot.nextRefIndex }
				refPtr['id'] = StreamUtils.readCid(snapshot.stream)

				snapshot.references[refId] = refPtr

	# Aggregate deserializer for class IDs: 78, 79
	class ArrayDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				StreamUtils.readUnsigned(snapshot.stream) # Length is read again during fill
				snapshot.assignRef('array')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				arrayPtr = { 'cid': ClassId.ARRAY, 'refId': snapshot.nextRefIndex }
				length = StreamUtils.readUnsigned(snapshot.stream)
				arrayPtr['isCanonical'] = StreamUtils.readBool(snapshot.stream)
				arrayPtr['typeArguments'] = StreamUtils.readRef(snapshot.stream)
				arrayPtr['length'] = length
				arrayPtr['data'] = []
				for _ in range(length):
					arrayPtr['data'].append(StreamUtils.readRef(snapshot.stream))

				snapshot.references[refId] = arrayPtr

	if includesCode:
		# Class ID: 81
		class OneByteStringDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.ONE_BYTE_STRING

			def getObjectAt(self, snapshot):
				stream = snapshot.rodata
				tags = int.from_bytes(stream.read(4), 'little')
				hsh = int.from_bytes(stream.read(4), 'little')
				length = int.from_bytes(stream.read(8), 'little')
				return ''.join(chr(x) for x in stream.read(length // 2))

		# Class ID: 82
		class TwoByteStringDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.TWO_BYTE_STRING

			def getObjectAt(self, stream):
				return 'two-byte string'

	else:
		# Class ID: 81
		class OneByteStringDeserializer():
			def __init__(self):
				self.cid = ClassId.ONE_BYTE_STRING

			def readAlloc(self, snapshot):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('one byte string')
				self.stopIndex = snapshot.nextRefIndex

			def readFill(self, snapshot):
				for refId in range(self.startIndex, self.stopIndex):
					length = StreamUtils.readUnsigned(snapshot.stream)
					StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
					strPtr = { 'cid': ClassId.ONE_BYTE_STRING, 'refId': snapshot.nextRefIndex }
					strPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
					strPtr['length'] = length
					strPtr['data'] = ''.join(chr(x) for x in snapshot.stream.read(length))

					snapshot.references[refId] = strPtr

		# Class ID: 82
		class TwoByteStringDeserializer():
			def __init__(self):
				self.cid = ClassId.TWO_BYTE_STRING

			def readAlloc(self, snapshot):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('two-byte string')
				self.stopIndex = snapshot.nextRefIndex

	# Aggregate deserializer for class IDs: 108, 111, 114, 117, 120, 123, 126, 129, 132, 135, 138, 141, 144, 147
	class TypedDataDeserializer():
		def __init__(self, cid):
			self.elementSize = TypedData.elementSizeInBytes(cid)
			self.cid = cid

		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('typed data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				isCanonical = StreamUtils.readBool(snapshot.stream)
				lengthInBytes = length * self.elementSize
				dataPtr = { 'cid': self.cid, 'refId': snapshot.nextRefIndex }
				dataPtr['length'] = length
				dataPtr['data'] = snapshot.stream.read(lengthInBytes)

				snapshot.references[refId] = dataPtr

	if cid >= ClassId.NUM_PREDEFINED.value or cid == ClassId.INSTANCE.value:
		return InstanceDeserializer()

	if ClassId.isTypedDataViewClass(cid):
		raise Exception('Typed data view deserializer not implemented')

	if ClassId.isExternalTypedDataClass(cid):
		raise Exception('External typed data deserializer not implemented')

	if ClassId.isTypedDataClass(cid):
		return TypedDataDeserializer(cid)

	cidEnum = ClassId(cid)
	if cidEnum is ClassId.ILLEGAL:
		raise Exception('Encountered illegal cluster')
	if cidEnum is ClassId.CLASS:
		return ClassDeserializer()
	if cidEnum is ClassId.PATCH_CLASS:
		return PatchClassDeserializer()
	if cidEnum is ClassId.FUNCTION:
		return FunctionDeserializer()
	if cidEnum is ClassId.CLOSURE_DATA:
		return ClosureDataDeserializer()
	if cidEnum is ClassId.SIGNATURE_DATA:
		return SignatureDataDeserializer()
	if cidEnum is ClassId.FFI_TRAMPOLINE_DATA:
		return FfiTrampolineDataDeserializer()
	if cidEnum is ClassId.FIELD:
		return FieldDeserializer()
	if cidEnum is ClassId.SCRIPT:
		return ScriptDeserializer()
	if cidEnum is ClassId.LIBRARY:
		return LibraryDeserializer()
	if cidEnum is ClassId.NAMESPACE:
		return NamespaceDeserializer()
	if cidEnum is ClassId.CODE:
		return CodeDeserializer()
	#FIXME: should check if snapshot is not precompiled
	if cidEnum is ClassId.BYTECODE:
		return BytecodeDeserializer()
	if cidEnum is ClassId.OBJECT_POOL:
		return ObjectPoolDeserializer()
	if cidEnum is ClassId.PC_DESCRIPTORS:
		return PcDescriptorsDeserializer()
	if cidEnum is ClassId.CODE_SOURCE_MAP:
		return CodeSourceMapDeserializer()
	if cidEnum is ClassId.COMPRESSED_STACK_MAPS:
		return CompressedStackMapsDeserializer()
	if cidEnum is ClassId.EXCEPTION_HANDLERS:
		return ExceptionHandlersDeserializer()
	if cidEnum is ClassId.UNLINKED_CALL:
		return UnlinkedCallDeserializer()
	if cidEnum is ClassId.MEGAMORPHIC_CACHE:
		return MegamorphicCacheDeserializer()
	if cidEnum is ClassId.SUBTYPE_TEST_CACHE:
		return SubtypeTestCacheDeserializer()
	if cidEnum is ClassId.LOADING_UNIT:
		return LoadingUnitDeserializer()
	if cidEnum is ClassId.TYPE_ARGUMENTS:
		return TypeArgumentsDeserializer()
	if cidEnum is ClassId.TYPE:
		return TypeDeserializer()
	if cidEnum is ClassId.TYPE_REF:
		return TypeRefDeserializer()
	if cidEnum is ClassId.TYPE_PARAMETER:
		return TypeParameterDeserializer()
	if cidEnum is ClassId.CLOSURE:
		return ClosureDeserializer()
	if cidEnum is ClassId.MINT:
		return MintDeserializer()
	if cidEnum is ClassId.DOUBLE:
		return DoubleDeserializer()
	if cidEnum is ClassId.GROWABLE_OBJECT_ARRAY:
		return GrowableObjectArrayDeserializer()
	# FIXME: should only target precompiled AOT snapshots
	if cidEnum is ClassId.WEAK_SERIALIZATION_REFERENCE:
		return WeakSerializationReferenceDeserializer()
	if cidEnum is ClassId.ARRAY:
		return ArrayDeserializer()
	if cidEnum is ClassId.IMMUTABLE_ARRAY:
		return ArrayDeserializer()
	if cidEnum is ClassId.ONE_BYTE_STRING:
		return OneByteStringDeserializer()
	if cidEnum is ClassId.TWO_BYTE_STRING:
		return TwoByteStringDeserializer()
	
	raise Exception('Deserializer missing for class {}'.format(ClassId(cid).name))