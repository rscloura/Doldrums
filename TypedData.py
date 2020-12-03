from ClassId import ClassId
import Constants

def elementSizeInBytes(cid):
	return elementSize(elementType(cid))

def elementType(cid):
	if cid == ClassId.BYTE_DATA_VIEW.value:
		return 1
	elif ClassId.isTypedDataClass(cid):
		return (cid - ClassId.TYPED_DATA_INT8_ARRAY.value - Constants.kTypedDataCidRemainderInternal) / 3
	elif ClassId.isTypedDataViewClass(cid):
		return (cid - ClassId.TYPED_DATA_INT8_ARRAY.value - Constants.kTypedDataCidRemainderView) / 3
	elif ClassId.isExternalTypedDataClass(cid):
		return (cid - ClassId.TYPED_DATA_INT8_ARRAY.value - Constants.kTypedDataCidRemainderExternal) / 3

def elementSize(index):
	return [1, 1, 1, 2, 2, 4, 4, 8, 8, 4, 8, 16, 16, 16][int(index)]