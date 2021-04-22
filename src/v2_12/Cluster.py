import logging

from . import Constants
from . import TypedData

from v2_12.ClassId import ClassId
from v2_12.Kind import Kind
from v2_12.UnboxedFieldBitmap import UnboxedFieldBitmap
from v2_12.Utils import DecodeUtils, NumericUtils, StreamUtils, isTopLevelCid

def getDeserializerForCid(includesCode, cid):
	class LoggingDeserializer():
		def readAlloc(self, snapshot, isCanonical):
			logging.info('%s alloc stage at offset: %s', self.__class__.__name__, snapshot.stream.tell())
			self._readAlloc(snapshot, isCanonical)

		def readFill(self, snapshot, isCanonical):
			logging.info('%s fill stage at offset: %s', self.__class__.__name__, snapshot.stream.tell())
			self._readFill(snapshot, isCanonical)

	# Abstract deserializer for class IDs: 22, 23, 81, 82
	class RODataDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			runningOffset = 0
			for x in range(count):
				runningOffset += StreamUtils.readUnsigned(snapshot.stream) << Constants.kObjectAlignmentLog2
				snapshot.rodata.seek(runningOffset)
				snapshot.assignRef({ 'cid': self.cid, 'refId': x,'data': self.getObjectAt(snapshot) })
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			return

	# Base class for deserializers with simple counting alloc stages
	class CountDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('{} stub'.format(self.__class__.__name__))
			self.stopIndex = snapshot.nextRefIndex

	# Class ID: 4
	class ClassDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
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

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.predefinedStartIndex, self.predefinedStopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId
				classPtr['refId'] = snapshot.nextRefIndex

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['kernelOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)

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
				#TODO: verify necessity
				classPtr['refId'] = snapshot.nextRefIndex

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['kernelOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)
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
			classPtr['constants'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['declarationType'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['invocationDispatcherCache'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['allocationStub'] = StreamUtils.readUnsigned(snapshot.stream)
			if not (snapshot.kind is Kind.FULL_AOT):
				classPtr['directImplementors'] = StreamUtils.readUnsigned(snapshot.stream)
				if not (snapshot.kind is Kind.FULL or snapshot.kind is Kind.FULL_CORE):
					classPtr['directSubclasses'] = StreamUtils.readUnsigned(snapshot.stream)
					if not (snapshot.kind is Kind.FULL_JIT):
						classPtr['dependentCode'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 5
	class PatchClassDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot, refId)
				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['libraryKernelOffset'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot, refId):
			classPtr = { 'cid': ClassId.PATCH_CLASS, 'refId': refId }
			classPtr['patchedClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['originClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			if not snapshot.kind is Kind.FULL_AOT:
				classPtr['libraryKernelData'] = StreamUtils.readUnsigned(snapshot.stream)

			return classPtr

	# Class ID: 6
	class FunctionDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				funcPtr = self._readFromTo(snapshot, refId)
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
						funcPtr['kernelOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)
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

		def _readFromTo(self, snapshot, refId):
			funcPtr = { 'cid': ClassId.FUNCTION, 'refId': refId }
			funcPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterNames'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['signature'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

			return funcPtr

	# Class ID: 7
	class ClosureDataDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				closureDataPtr = { 'cid': ClassId.CLOSURE_DATA, 'refId': refId }

				if (snapshot.kind is Kind.FULL_AOT):
					closureDataPtr['contextScope'] = None
				else:
					closureDataPtr['contextScope'] = StreamUtils.readRef(snapshot.stream)

				closureDataPtr['parentFunction'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['closure'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['defaultTypeArguments'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['defaultTypeArgumentsInfo'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = closureDataPtr

	# Class ID: 10
	class FfiTrampolineDataDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				dataPtr = self._readFromTo(snapshot, refId)
				dataPtr['callbackId'] = StreamUtils.readUnsigned(snapshot.stream) if snapshot.kind is Kind.FULL_AOT else 0

				snapshot.references[refId] = dataPtr
			
		def _readFromTo(self, snapshot, refId):
			dataPtr = { 'cid': ClassId.FFI_TRAMPOLINE_DATA, 'refId': refId }
			dataPtr['signatureType'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['CSignature'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['callbackTarget'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['callbackExceptionalReturn'] = StreamUtils.readUnsigned(snapshot.stream)

			return dataPtr

	# Class ID: 11
	class FieldDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				fieldPtr = self._readFromTo(snapshot, refId)

				if snapshot.kind is not Kind.FULL_AOT:
					fieldPtr['guardedListLength'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is Kind.FULL_JIT:
					fieldPtr['dependentCode'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is not Kind.FULL_AOT:
					fieldPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['guardedCid'] = StreamUtils.readCid(snapshot.stream)
					fieldPtr['isNullable'] = StreamUtils.readCid(snapshot.stream)
					staticTypeExactnessState = StreamUtils.readInt(snapshot.stream, 8)
					if snapshot.arch == 'X64':
						fieldPtr['staticTypeExactnessState'] = staticTypeExactnessState
					if not snapshot.isPrecompiled:
						fieldPtr['kernelOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)

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

		def _readFromTo(self, snapshot, refId):
			fieldPtr = { 'cid': ClassId.FIELD, 'refId': refId }
			fieldPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['type'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['initializerFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return fieldPtr

	# Class ID: 12
	class ScriptDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				scriptPtr = self._readFromTo(snapshot, refId)

				scriptPtr['lineOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['colOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				if not snapshot.isPrecompiled:
					scriptPtr['flagsAndMaxPosition'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['kernelScriptIndex'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['loadTimestamp'] = 0

				snapshot.references[refId] = scriptPtr

		def _readFromTo(self, snapshot, refId):
			scriptPtr = { 'cid': ClassId.SCRIPT, 'refId': refId }
			scriptPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)

			if snapshot.kind is Kind.FULL or snapshot.kind is Kind.FULL_JIT:
				scriptPtr['resolvedUrl'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['compileTimeConstants'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['lineStarts'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['debugPositions'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['kernelProgramInfo'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['source'] = StreamUtils.readUnsigned(snapshot.stream)

			return scriptPtr

	# Class ID: 13
	class LibraryDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				libraryPtr = self._readFromTo(snapshot, refId)
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

		def _readFromTo(self, snapshot, refId):
			libraryPtr = { 'cid': ClassId.LIBRARY, 'refId': refId }
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
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				namespacePtr = { 'cid': ClassId.NAMESPACE, 'refId': refId }
				namespacePtr['target'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['showNames'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['hideNames'] = StreamUtils.readUnsigned(snapshot.stream)
				namespacePtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = namespacePtr

	# Class ID: 16
	class CodeDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('code')
			self.stopIndex = self.deferredStartIndex = snapshot.nextRefIndex
			deferredCount = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(deferredCount):
				snapshot.assignRef('code')
			self.deferredStopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				codePtr = self._innerRead(snapshot, refId, False)

				snapshot.references[refId] = codePtr

			for refId in range(self.deferredStartIndex, self.deferredStopIndex):
				codePtr = self._innerRead(snapshot, refId, True)

				snapshot.references[refId] = codePtr

		def _innerRead(self, snapshot, refId, deferred):
			codePtr = { 'cid': ClassId.CODE, 'refId': refId }
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

	# Class ID: 20
	class ObjectPoolDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('object pool')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				poolPtr = { 'cid': ClassId.OBJECT_POOL, 'refId': refId }
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

			def _readAlloc(self, snapshot, isCanonical):
				super()._readAlloc(snapshot, isCanonical)

			def getObjectAt(self, stream):
				return 'pc descriptor'

		# Class ID: 22
		class CodeSourceMapDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.CODE_SOURCE_MAP

			def _readAlloc(self, snapshot, isCanonical):
				super()._readAlloc(snapshot, isCanonical)

			def getObjectAt(self, stream):
				return 'code source map'

		# Class ID: 23
		class CompressedStackMapsDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.COMPRESSED_STACK_MAPS

			def _readAlloc(self, snapshot, isCanonical):
				super()._readAlloc(snapshot, isCanonical)

			def getObjectAt(self, stream):
				return 'compressed stack maps'
	else:
		# Class ID: 21
		class PcDescriptorsDeserializer(LoggingDeserializer):
			def __init__(self):
				self.cid = ClassId.PC_DESCRIPTORS

			def _readAlloc(self, snapshot, isCanonical):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('pc descriptors')
				self.stopIndex = snapshot.nextRefIndex

			def _readFill(self, snapshot, isCanonical):
				for refId in range(self.startIndex, self.stopIndex):
					length = StreamUtils.readUnsigned(snapshot.stream)
					descPtr = { 'cid': ClassId.PC_DESCRIPTORS, 'refId': refId }
					descPtr['length'] = length
					descPtr['data'] = snapshot.stream.read(length)

					snapshot.references[refId] = descPtr

	# Class ID: 25
	class ExceptionHandlersDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('exception')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				handlersPtr = { 'cid': ClassId.EXCEPTION_HANDLERS, 'refId': refId }
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
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				unlinkedPtr = self._readFromTo(snapshot, refId)
				unlinkedPtr['canPatchToMonomorphic'] = StreamUtils.readBool(snapshot.stream)

				snapshot.references[refId] = unlinkedPtr

		def _readFromTo(self, snapshot, refId):
			unlinkedPtr = { 'cid': ClassId.UNLINKED_CALL, 'refId': refId }
			unlinkedPtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			unlinkedPtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)

			return unlinkedPtr

	# Class ID: 34
	class MegamorphicCacheDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = self._readFromTo(snapshot, refId)
				cachePtr['filledEntryCount'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = cachePtr

		def _readFromTo(self, snapshot, refId):
			cachePtr = { 'cid': ClassId.MEGAMORPHIC_CACHE, 'refId': refId }
			cachePtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['buckets'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['mask'] = StreamUtils.readUnsigned(snapshot.stream)

			return cachePtr

	# Class ID: 35
	class SubtypeTestCacheDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = { 'cid': ClassId.SUBTYPE_TEST_CACHE, 'refId': refId }
				cachePtr['cache'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = cachePtr

	# Class ID: 35
	class LoadingUnitDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				unitPtr = { 'cid': ClassId.LOADING_UNIT, 'refId': refId }
				unitPtr['parent'] = StreamUtils.readRef(snapshot.stream)
				unitPtr['baseObjects'] = None
				unitPtr['id'] = StreamUtils.readInt(snapshot.stream, 32)
				unitPtr['loaded'] = False
				unitPtr['loadOutstanding'] = False

				snapshot.references[refId] = unitPtr

	# Class ID: 42
	class InstanceDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			self.nextFieldOffsetInWords = StreamUtils.readInt(snapshot.stream, 32)
			self.instanceSizeInWords = StreamUtils.readInt(snapshot.stream, 32)
			for _ in range(count):
				snapshot.assignRef('instance')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			nextFieldOffset = self.nextFieldOffsetInWords << Constants.kWordSizeLog2
			instanceSize = NumericUtils.roundUp(self.instanceSizeInWords * Constants.kWordSize, Constants.kObjectAlignment)
			unboxedFieldsBitmap = UnboxedFieldBitmap(StreamUtils.readUnsigned(snapshot.stream, 64))
			for refId in range(self.startIndex, self.stopIndex):
				instancePtr = { 'cid': ClassId.INSTANCE, 'refId': refId }
				instancePtr['data'] = []
				offset = 8 if snapshot.is64 else 4
				while offset < nextFieldOffset:
					if unboxedFieldsBitmap.get(int(offset / Constants.kWordSize)):
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readWordWith32BitReads(snapshot.stream))
					else:
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readRef(snapshot.stream))
					offset += Constants.kWordSize
				if offset < instanceSize:
					#TODO: verify
					instancePtr['data'].append(None)
					offset += Constants.kWordSize
				
				snapshot.references[refId] = instancePtr

	# Class ID: 44
	class TypeArgumentsDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream) # Length is read again during fill
				snapshot.assignRef('type args')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				typeArgsPtr = { 'cid': ClassId.TYPE_ARGUMENTS, 'refId': refId }
				typeArgsPtr['length'] = length
				typeArgsPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
				typeArgsPtr['nullability'] = StreamUtils.readUnsigned(snapshot.stream)
				typeArgsPtr['instantiations'] = StreamUtils.readRef(snapshot.stream)
				typeArgsPtr['types'] = []
				for j in range(length):
					typeArgsPtr['types'].append(StreamUtils.readRef(snapshot.stream))

				snapshot.references[refId] = typeArgsPtr

	# Class ID: 46
	class TypeDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot, refId)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['typeState'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot, refId):
			typePtr = { 'cid': ClassId.TYPE, 'refId': refId, 'isBase': False }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['typeClassId'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['arguments'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr

	# Class ID 53
	class FunctionTypeDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				functionTypePtr = self._readFromTo(snapshot, refId)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				functionTypePtr['typeState'] = combined >> Constants.kNullabilityBitSize
				functionTypePtr['nullability'] = combined & Constants.kNullabilityBitMask
				functionTypePtr['packedFields'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				snapshot.references[refId] = functionTypePtr

		def _readFromTo(self, snapshot, refId):
			functionTypePtr = { 'cid': ClassId.FUNCTION_TYPE, 'refId': refId }
			functionTypePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			functionTypePtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			functionTypePtr['resultType'] = StreamUtils.readUnsigned(snapshot.stream)
			functionTypePtr['parameterTypes'] = StreamUtils.readUnsigned(snapshot.stream)
			functionTypePtr['parameterNames'] = StreamUtils.readUnsigned(snapshot.stream)
			functionTypePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)

			return functionTypePtr

	# Class ID: 54
	class TypeRefDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				typePtr = { 'cid': ClassId.TYPE_REF, 'refId': refId }
				typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
				typePtr['type'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = typePtr

	# Class ID: 48
	class TypeParameterDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot, refId)
				typePtr['parametrizedClassId'] = StreamUtils.readInt(snapshot.stream, 32)
				typePtr['base'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				typePtr['index'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['flags'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot, refId):
			typePtr = { 'cid': ClassId.TYPE_PARAMETER, 'refId': refId, 'isBase': False }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['bound'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['defaultArgument'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr


	# Class ID: 49
	class ClosureDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				closurePtr = { 'cid': ClassId.CLOSURE, 'refId': refId }
				closurePtr['instantiatorTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['functionTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['delayedTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['function'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['context'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = closurePtr

	# Class ID: 53
	class MintDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for i in range(count):
				value = StreamUtils.readInt(snapshot.stream, 64)
				snapshot.assignRef({ 'cid': ClassId.MINT, 'isCanonical': isCanonical, 'value': value})

		def _readFill(self, snapshot, isCanonical):
			return

	# Class ID: 54
	class DoubleDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				value = StreamUtils.readInt(snapshot.stream, 64)
				snapshot.references[refId] = { 'cid': ClassId.DOUBLE, 'refId': refId, 'isCanonical': isCanonical,  'value': value }

	# Class ID: 56
	class GrowableObjectArrayDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				listPtr = { 'cid': ClassId.GROWABLE_OBJECT_ARRAY, 'refId': refId }
				listPtr['typeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['length'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = listPtr

	# Class ID: 77
	class WeakSerializationReferenceDeserializer(CountDeserializer):
		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				refPtr = { 'cid': ClassId.WEAK_SERIALIZATION_REFERENCE, 'refId': refId }
				refPtr['id'] = StreamUtils.readCid(snapshot.stream)

				snapshot.references[refId] = refPtr

	# Aggregate deserializer for class IDs: 78, 79
	class ArrayDeserializer(LoggingDeserializer):
		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				StreamUtils.readUnsigned(snapshot.stream) # Length is read again during fill
				snapshot.assignRef('array')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			arrayPtr = {}
			for refId in range(self.startIndex, self.stopIndex):
				arrayPtr = { 'cid': ClassId.ARRAY, 'refId': refId }
				length = StreamUtils.readUnsigned(snapshot.stream)
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

			def _readAlloc(self, snapshot, isCanonical):
				super()._readAlloc(snapshot, isCanonical)

			def getObjectAt(self, snapshot):
				stream = snapshot.rodata
				tags = int.from_bytes(stream.read(4), 'little')
				if snapshot.is64:
					hsh = int.from_bytes(stream.read(4), 'little')
					length = int.from_bytes(stream.read(8), 'little')
				else:
					length = int.from_bytes(stream.read(4), 'little')
					hsh = int.from_bytes(stream.read(4), 'little')
				return ''.join(chr(x) for x in stream.read(length // 2))

		# Class ID: 82
		class TwoByteStringDeserializer(RODataDeserializer):
			def __init__(self):
				self.cid = ClassId.TWO_BYTE_STRING

			def _readAlloc(self, snapshot, isCanonical):
				super()._readAlloc(snapshot, isCanonical)

			def getObjectAt(self, stream):
				return 'two-byte string'

	else:
		# Class ID: 81
		class OneByteStringDeserializer(LoggingDeserializer):
			def __init__(self):
				self.cid = ClassId.ONE_BYTE_STRING

			def _readAlloc(self, snapshot, isCanonical):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('one byte string')
				self.stopIndex = snapshot.nextRefIndex

			def _readFill(self, snapshot, isCanonical):
				for refId in range(self.startIndex, self.stopIndex):
					length = StreamUtils.readUnsigned(snapshot.stream)
					strPtr = { 'cid': ClassId.ONE_BYTE_STRING, 'refId': refId }
					strPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
					strPtr['length'] = length
					strPtr['data'] = ''.join(chr(x) for x in snapshot.stream.read(length))

					snapshot.references[refId] = strPtr

		# Class ID: 82
		class TwoByteStringDeserializer(LoggingDeserializer):
			def __init__(self):
				self.cid = ClassId.TWO_BYTE_STRING

			def _readAlloc(self, snapshot, isCanonical):
				self.startIndex = snapshot.nextRefIndex
				count = StreamUtils.readUnsigned(snapshot.stream)
				for _ in range(count):
					length = StreamUtils.readUnsigned(snapshot.stream)
					snapshot.assignRef('two-byte string')
				self.stopIndex = snapshot.nextRefIndex

	# Aggregate deserializer for class IDs: 108, 111, 114, 117, 120, 123, 126, 129, 132, 135, 138, 141, 144, 147
	class TypedDataDeserializer(LoggingDeserializer):
		def __init__(self, cid):
			self.elementSize = TypedData.elementSizeInBytes(cid)
			self.cid = cid

		def _readAlloc(self, snapshot, isCanonical):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('typed data')
			self.stopIndex = snapshot.nextRefIndex

		def _readFill(self, snapshot, isCanonical):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				lengthInBytes = length * self.elementSize
				dataPtr = { 'cid': self.cid, 'refId': refId }
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
	if cidEnum is ClassId.FUNCTION_TYPE:
		return FunctionTypeDeserializer()
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
	
	raise Exception('Deserializer missing for class {} (CID {})'.format(ClassId(cid).name, ClassId(cid).value))