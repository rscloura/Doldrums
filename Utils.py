import math

class NumericUtils: 
	def isPowerOfTwo(n):
		return ((n & (n - 1)) == 0) and (n != 0)
 
	def roundDown(n, m):
		assert(NumericUtils.isPowerOfTwo(m))
		return n & -m
 
	def roundUp(n, m):
		return NumericUtils.roundDown(n + m - 1, m)

class StreamUtils:
	kDataBitsPerByte = 7
	kByteMask = (1 << kDataBitsPerByte) - 1
	kMaxUnsignedDataPerByte = kByteMask
	kMinDataPerByte = -(1 << (kDataBitsPerByte - 1))
	kMaxDataPerByte = (~kMinDataPerByte & kByteMask)
	kEndByteMarker = (255 - kMaxDataPerByte)
	kEndUnsignedByteMarker = (255 - kMaxUnsignedDataPerByte)

	def read(stream, endByteMarker, maxLoops = -1):
		b = int.from_bytes(stream.read(1), 'big', signed=False)
		r = 0
		s = 0
		if (maxLoops == -1):
			flag = -1
		else:
			flag = 1
		while (b <= StreamUtils.kMaxUnsignedDataPerByte):
			r |= b << s
			s += StreamUtils.kDataBitsPerByte
			x = stream.read(1)
			b = int.from_bytes(x, 'big', signed=False)
			maxLoops -= 1

		assert(flag * maxLoops >= 0)
		return r | ((b - endByteMarker) << s)
 
	def readUnsigned(stream, size = -1):
		if (size == -1):
			return StreamUtils.read(stream, StreamUtils.kEndUnsignedByteMarker)
		else:
			return StreamUtils.read(stream, StreamUtils.kEndUnsignedByteMarker, math.ceil(size / 7))

	def readInt(stream, size = 32):
		return StreamUtils.read(stream, StreamUtils.kEndByteMarker, math.ceil(size / 7)) # 7 bits per "byte" because of marker

	def readCid(stream):
		return StreamUtils.readInt(stream, 32)

	def readTokenPosition(stream):
		return StreamUtils.readInt(stream, 32)

	def readBool(stream):
		b = stream.read(1)
		if b == b'\x00':
			return False
		elif b == b'\x01':
			return True
		else:
			raise Exception('Expected boolean, but received non-boolean value while reading' + str(stream.tell()))

	def readString(stream):
		res = b''
		b = stream.read(1)
		while b != b'\x00':
			res += b
			b = stream.read(1)
		return res

def getVersionInfo(hsh):
	if hsh == '8ee4ef7a67df9845fba331734198a953':
		return 'Dart v2.10'
	else:
		return 'unknown version'